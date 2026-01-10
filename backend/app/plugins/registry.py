"""
Plugin Registry

Maintains the registry of all loaded plugins.
"""

from typing import Dict, List, Optional, Type, Iterator
from threading import RLock

from .base import IDKitPlugin, PluginMeta, PluginStatus
from .exceptions import PluginError


class PluginRegistry:
    """
    Registry for managing plugin instances.

    Thread-safe registry that tracks all loaded plugins
    and their status.
    """

    _instance: Optional["PluginRegistry"] = None
    _lock = RLock()

    def __new__(cls) -> "PluginRegistry":
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._plugins: Dict[str, IDKitPlugin] = {}
                cls._instance._plugin_classes: Dict[str, Type[IDKitPlugin]] = {}
            return cls._instance

    def register(self, plugin: IDKitPlugin) -> None:
        """
        Register a plugin instance.

        Args:
            plugin: Plugin instance to register

        Raises:
            PluginError: If plugin with same name already registered
        """
        with self._lock:
            name = plugin.meta.name

            if name in self._plugins:
                raise PluginError(
                    f"Plugin '{name}' is already registered"
                )

            self._plugins[name] = plugin
            self._plugin_classes[name] = type(plugin)

    def register_class(self, plugin_class: Type[IDKitPlugin]) -> None:
        """
        Register a plugin class (not instantiated).

        Args:
            plugin_class: Plugin class to register

        Raises:
            PluginError: If plugin with same name already registered
        """
        with self._lock:
            name = plugin_class.meta.name

            if name in self._plugin_classes:
                raise PluginError(
                    f"Plugin class '{name}' is already registered"
                )

            self._plugin_classes[name] = plugin_class

    def unregister(self, name: str) -> Optional[IDKitPlugin]:
        """
        Unregister a plugin.

        Args:
            name: Plugin name to unregister

        Returns:
            The unregistered plugin, or None if not found
        """
        with self._lock:
            plugin = self._plugins.pop(name, None)
            self._plugin_classes.pop(name, None)
            return plugin

    def get(self, name: str) -> Optional[IDKitPlugin]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def get_class(self, name: str) -> Optional[Type[IDKitPlugin]]:
        """
        Get a plugin class by name.

        Args:
            name: Plugin name

        Returns:
            Plugin class or None
        """
        return self._plugin_classes.get(name)

    def has(self, name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            name: Plugin name

        Returns:
            True if registered
        """
        return name in self._plugins or name in self._plugin_classes

    def get_all(self) -> List[IDKitPlugin]:
        """
        Get all registered plugin instances.

        Returns:
            List of all plugins
        """
        return list(self._plugins.values())

    def get_active(self) -> List[IDKitPlugin]:
        """
        Get all active plugins.

        Returns:
            List of active plugins
        """
        return [
            p for p in self._plugins.values()
            if p.status == PluginStatus.ACTIVATED
        ]

    def get_by_capability(self, capability: str) -> List[IDKitPlugin]:
        """
        Get plugins with a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of plugins with the capability
        """
        from .base import PluginCapability

        cap = PluginCapability(capability)
        return [
            p for p in self._plugins.values()
            if cap in p.meta.capabilities
        ]

    def get_by_tag(self, tag: str) -> List[IDKitPlugin]:
        """
        Get plugins with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of plugins with the tag
        """
        return [
            p for p in self._plugins.values()
            if tag in p.meta.tags
        ]

    def create_instance(self, name: str) -> IDKitPlugin:
        """
        Create a new instance of a registered plugin class.

        Args:
            name: Plugin name

        Returns:
            New plugin instance

        Raises:
            PluginError: If plugin class not found
        """
        plugin_class = self._plugin_classes.get(name)

        if plugin_class is None:
            raise PluginError(f"Plugin class '{name}' not found")

        instance = plugin_class()
        self._plugins[name] = instance
        return instance

    def clear(self) -> None:
        """Clear all registered plugins."""
        with self._lock:
            self._plugins.clear()
            self._plugin_classes.clear()

    def __len__(self) -> int:
        """Get number of registered plugins."""
        return len(self._plugins)

    def __iter__(self) -> Iterator[IDKitPlugin]:
        """Iterate over registered plugins."""
        return iter(self._plugins.values())

    def __contains__(self, name: str) -> bool:
        """Check if plugin is registered."""
        return self.has(name)

    def get_info(self) -> Dict:
        """Get registry info."""
        return {
            "total_plugins": len(self._plugins),
            "active_plugins": len(self.get_active()),
            "plugin_classes": len(self._plugin_classes),
            "plugins": {
                name: plugin.get_info()
                for name, plugin in self._plugins.items()
            },
        }


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """
    Get the global plugin registry.

    Returns:
        The singleton PluginRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
