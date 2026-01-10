"""
Plugin Manager

Central manager for plugin lifecycle and operations.
"""

from typing import Any, Dict, List, Optional, Callable
import asyncio
from pathlib import Path

from fastapi import FastAPI, APIRouter

from .base import IDKitPlugin, PluginContext, PluginStatus, PluginCapability
from .registry import PluginRegistry, get_registry
from .loader import PluginLoader
from .hooks import HookRegistry, get_hook_registry, register_system_hooks
from .exceptions import (
    PluginError,
    PluginActivationError,
    PluginDependencyError,
)


class PluginManager:
    """
    Central manager for IDKit plugins.

    Handles:
    - Plugin discovery and loading
    - Plugin lifecycle (activate/deactivate)
    - Dependency resolution
    - Route registration
    - Hook management
    """

    _instance: Optional["PluginManager"] = None

    def __new__(cls, *args, **kwargs) -> "PluginManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        app: Optional[FastAPI] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the plugin manager.

        Args:
            app: FastAPI application instance
            config: Plugin configuration dictionary
        """
        if self._initialized:
            return

        self._app = app
        self._config = config or {}
        self._registry = get_registry()
        self._hook_registry = get_hook_registry()
        self._loader = PluginLoader(self._registry)
        self._context: Optional[PluginContext] = None
        self._plugin_routers: Dict[str, APIRouter] = {}
        self._background_tasks: List[asyncio.Task] = []

        # Register system hooks
        register_system_hooks()

        self._initialized = True

    def set_app(self, app: FastAPI) -> None:
        """Set the FastAPI application."""
        self._app = app

    def set_context(self, context: PluginContext) -> None:
        """Set the plugin context."""
        self._context = context

    async def discover_and_load(
        self,
        search_paths: List[str],
    ) -> List[IDKitPlugin]:
        """
        Discover and load plugins from directories.

        Args:
            search_paths: Directories to search for plugins

        Returns:
            List of loaded plugins
        """
        loaded = []
        discovered = self._loader.discover_plugins(search_paths, auto_load=False)

        for plugin_path in discovered:
            try:
                plugin = self._loader.load_from_path(plugin_path)
                loaded.append(plugin)
            except Exception as e:
                # Log but continue
                print(f"Failed to load plugin from {plugin_path}: {e}")

        return loaded

    async def load_plugin(self, source: str) -> IDKitPlugin:
        """
        Load a single plugin.

        Args:
            source: Module name or file path

        Returns:
            Loaded plugin
        """
        if source.endswith(".py") or Path(source).is_dir():
            return self._loader.load_from_path(source)
        else:
            return self._loader.load_from_module(source)

    async def activate_plugin(self, name: str) -> None:
        """
        Activate a plugin by name.

        Args:
            name: Plugin name

        Raises:
            PluginActivationError: If activation fails
        """
        plugin = self._registry.get(name)
        if plugin is None:
            raise PluginActivationError(f"Plugin '{name}' not found")

        if plugin.is_active:
            return  # Already active

        # Check dependencies
        await self._check_dependencies(plugin)

        # Create context if needed
        if self._context is None and self._app is not None:
            self._context = await self._create_context()

        if self._context is None:
            raise PluginActivationError(
                "Cannot activate plugin: no context available"
            )

        # Activate
        try:
            await plugin.activate(self._context)
            plugin._status = PluginStatus.ACTIVATED

            # Register routes
            if PluginCapability.API_ROUTES in plugin.meta.capabilities:
                await self._register_plugin_routes(plugin)

            # Register middleware
            if PluginCapability.MIDDLEWARE in plugin.meta.capabilities:
                plugin.register_middleware(self._app)

            # Register event handlers
            handlers = plugin.register_event_handlers()
            for event_name, callbacks in handlers.items():
                for callback in callbacks:
                    self._hook_registry.subscribe(
                        hook_name=event_name,
                        callback=callback,
                        plugin_name=plugin.meta.name,
                    )

            # Start background tasks
            if PluginCapability.BACKGROUND_TASKS in plugin.meta.capabilities:
                tasks = plugin.register_background_tasks()
                for task_func in tasks:
                    task = asyncio.create_task(task_func())
                    self._background_tasks.append(task)

            # Trigger activation hook
            await self._hook_registry.trigger(
                "plugin.activated",
                plugin=plugin,
            )

        except Exception as e:
            plugin._status = PluginStatus.ERROR
            plugin._error = str(e)
            raise PluginActivationError(
                f"Failed to activate plugin '{name}': {e}"
            )

    async def deactivate_plugin(self, name: str) -> None:
        """
        Deactivate a plugin by name.

        Args:
            name: Plugin name
        """
        plugin = self._registry.get(name)
        if plugin is None or not plugin.is_active:
            return

        # Check if other plugins depend on this one
        dependents = self._get_dependents(name)
        if dependents:
            raise PluginError(
                f"Cannot deactivate '{name}': required by {dependents}"
            )

        try:
            await plugin.deactivate()
            plugin._status = PluginStatus.DEACTIVATED

            # Unregister event handlers
            self._hook_registry.unsubscribe_plugin(name)

            # Remove routes
            if name in self._plugin_routers:
                # Note: FastAPI doesn't support removing routes dynamically
                # Routes will remain but the plugin won't handle them
                del self._plugin_routers[name]

            # Trigger deactivation hook
            await self._hook_registry.trigger(
                "plugin.deactivated",
                plugin=plugin,
            )

        except Exception as e:
            plugin._error = str(e)
            raise PluginError(f"Error deactivating plugin '{name}': {e}")

    async def activate_all(self) -> Dict[str, str]:
        """
        Activate all loaded plugins.

        Returns:
            Dictionary mapping plugin names to status/errors
        """
        results = {}

        # Sort by dependencies
        sorted_plugins = self._topological_sort()

        for plugin in sorted_plugins:
            name = plugin.meta.name

            # Check if plugin is enabled in config
            plugin_config = self._config.get(name, {})
            if not plugin_config.get("enabled", True):
                results[name] = "disabled"
                continue

            try:
                plugin.set_config(plugin_config)
                await self.activate_plugin(name)
                results[name] = "activated"
            except Exception as e:
                results[name] = f"error: {e}"

        return results

    async def deactivate_all(self) -> None:
        """Deactivate all active plugins."""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._background_tasks.clear()

        # Deactivate in reverse dependency order
        sorted_plugins = list(reversed(self._topological_sort()))

        for plugin in sorted_plugins:
            if plugin.is_active:
                try:
                    await self.deactivate_plugin(plugin.meta.name)
                except Exception:
                    pass

    async def _check_dependencies(self, plugin: IDKitPlugin) -> None:
        """Check if all plugin dependencies are satisfied."""
        for dep_spec in plugin.meta.dependencies:
            # Parse dependency spec (name:version)
            parts = dep_spec.split(":")
            dep_name = parts[0]
            dep_version = parts[1] if len(parts) > 1 else None

            dep_plugin = self._registry.get(dep_name)

            if dep_plugin is None:
                raise PluginDependencyError(
                    f"Plugin '{plugin.meta.name}' requires '{dep_name}' which is not installed"
                )

            if not dep_plugin.is_active:
                # Try to activate dependency
                await self.activate_plugin(dep_name)

    def _get_dependents(self, name: str) -> List[str]:
        """Get list of plugins that depend on the given plugin."""
        dependents = []
        for plugin in self._registry.get_active():
            for dep_spec in plugin.meta.dependencies:
                dep_name = dep_spec.split(":")[0]
                if dep_name == name:
                    dependents.append(plugin.meta.name)
        return dependents

    def _topological_sort(self) -> List[IDKitPlugin]:
        """Sort plugins by dependencies (dependencies first)."""
        plugins = list(self._registry.get_all())
        sorted_list = []
        visited = set()
        temp_visited = set()

        def visit(plugin: IDKitPlugin):
            name = plugin.meta.name
            if name in temp_visited:
                raise PluginDependencyError(
                    f"Circular dependency detected involving '{name}'"
                )
            if name in visited:
                return

            temp_visited.add(name)

            for dep_spec in plugin.meta.dependencies:
                dep_name = dep_spec.split(":")[0]
                dep_plugin = self._registry.get(dep_name)
                if dep_plugin:
                    visit(dep_plugin)

            temp_visited.remove(name)
            visited.add(name)
            sorted_list.append(plugin)

        for plugin in plugins:
            if plugin.meta.name not in visited:
                visit(plugin)

        return sorted_list

    async def _register_plugin_routes(self, plugin: IDKitPlugin) -> None:
        """Register API routes from a plugin."""
        router = plugin.register_routes()
        if router and self._app:
            self._plugin_routers[plugin.meta.name] = router
            self._app.include_router(
                router,
                prefix=f"/plugins/{plugin.meta.name}",
                tags=[f"Plugin: {plugin.meta.name}"],
            )

    async def _create_context(self) -> PluginContext:
        """Create plugin context from current app."""
        from app.config import settings
        from app.logging_config import get_logger
        from app.dependencies import get_db
        from app.utils.redis import get_redis

        return PluginContext(
            app=self._app,
            config=self._config,
            logger=get_logger("plugins"),
            get_db=get_db,
            get_redis=get_redis,
            get_storage=lambda: None,  # TODO: Implement storage factory
            version=settings.version,
        )

    def get_plugin(self, name: str) -> Optional[IDKitPlugin]:
        """Get a plugin by name."""
        return self._registry.get(name)

    def get_all_plugins(self) -> List[IDKitPlugin]:
        """Get all registered plugins."""
        return self._registry.get_all()

    def get_active_plugins(self) -> List[IDKitPlugin]:
        """Get all active plugins."""
        return self._registry.get_active()

    async def health_check(self) -> Dict[str, Any]:
        """Run health checks for all active plugins."""
        results = {}
        for plugin in self._registry.get_active():
            try:
                results[plugin.meta.name] = await plugin.health_check()
            except Exception as e:
                results[plugin.meta.name] = {
                    "status": "error",
                    "error": str(e),
                }
        return results

    def get_info(self) -> Dict[str, Any]:
        """Get manager info."""
        return {
            "registry": self._registry.get_info(),
            "hooks": self._hook_registry.get_info(),
            "active_routers": list(self._plugin_routers.keys()),
            "background_tasks": len(self._background_tasks),
        }


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(
    app: Optional[FastAPI] = None,
    config: Optional[Dict[str, Any]] = None,
) -> PluginManager:
    """
    Get the global plugin manager.

    Args:
        app: FastAPI application (optional, for initialization)
        config: Plugin configuration (optional, for initialization)

    Returns:
        The singleton PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(app, config)
    elif app is not None:
        _plugin_manager.set_app(app)
    return _plugin_manager
