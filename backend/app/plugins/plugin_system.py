"""
Plugin Architecture for IDKit

Extensible plugin system for adding custom functionality:
- Plugin discovery and loading
- Hook system for extensibility points
- Plugin lifecycle management
- Plugin configuration
"""

import importlib
import importlib.util
import inspect
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
import logging

logger = logging.getLogger(__name__)


class PluginState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class HookType(Enum):
    """Available hook points in the system."""
    # Content hooks
    CONTENT_PRE_GENERATE = "content.pre_generate"
    CONTENT_POST_GENERATE = "content.post_generate"
    CONTENT_PRE_PUBLISH = "content.pre_publish"
    CONTENT_POST_PUBLISH = "content.post_publish"
    
    # AI hooks
    AI_PRE_INFERENCE = "ai.pre_inference"
    AI_POST_INFERENCE = "ai.post_inference"
    
    # User hooks
    USER_PRE_CREATE = "user.pre_create"
    USER_POST_CREATE = "user.post_create"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Analytics hooks
    ANALYTICS_PRE_EXPORT = "analytics.pre_export"
    ANALYTICS_POST_EXPORT = "analytics.post_export"
    
    # Payment hooks
    PAYMENT_PRE_PROCESS = "payment.pre_process"
    PAYMENT_POST_PROCESS = "payment.post_process"
    
    # System hooks
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    REQUEST_PRE_PROCESS = "request.pre_process"
    REQUEST_POST_PROCESS = "request.post_process"


@dataclass
class PluginMetadata:
    """Plugin metadata from plugin.json or class attributes."""
    name: str
    version: str
    description: str
    author: str
    homepage: Optional[str] = None
    license: Optional[str] = None
    requires: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    settings_schema: Optional[Dict] = None


@dataclass
class HookResult:
    """Result from a hook execution."""
    plugin_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    modified: bool = False


class PluginBase(ABC):
    """
    Base class for all plugins.
    
    Example plugin:
    
        class MyPlugin(PluginBase):
            name = "my-plugin"
            version = "1.0.0"
            description = "My custom plugin"
            author = "Author Name"
            
            def on_enable(self):
                self.register_hook(HookType.CONTENT_POST_GENERATE, self.process_content)
            
            def process_content(self, context):
                content = context.get("content")
                # Process content
                return {"content": modified_content, "modified": True}
    """
    
    # Required metadata (override in subclass)
    name: str = "unnamed-plugin"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    
    # Optional metadata
    homepage: Optional[str] = None
    license: Optional[str] = None
    requires: List[str] = []
    
    def __init__(self, manager: "PluginManager"):
        self.manager = manager
        self.state = PluginState.LOADED
        self.settings: Dict[str, Any] = {}
        self._registered_hooks: List[tuple] = []
    
    def register_hook(self, hook_type: HookType, handler: Callable):
        """Register a handler for a hook."""
        self.manager.register_hook(hook_type, self.name, handler)
        self._registered_hooks.append((hook_type, handler))
    
    def unregister_all_hooks(self):
        """Unregister all hooks registered by this plugin."""
        for hook_type, handler in self._registered_hooks:
            self.manager.unregister_hook(hook_type, self.name)
        self._registered_hooks.clear()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a plugin setting."""
        self.settings[key] = value
        self.manager.save_plugin_settings(self.name, self.settings)
    
    @abstractmethod
    def on_enable(self):
        """Called when plugin is enabled. Register hooks here."""
        pass
    
    def on_disable(self):
        """Called when plugin is disabled. Cleanup here."""
        self.unregister_all_hooks()
    
    def on_install(self):
        """Called when plugin is first installed."""
        pass
    
    def on_uninstall(self):
        """Called when plugin is uninstalled."""
        pass
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            homepage=self.homepage,
            license=self.license,
            requires=self.requires,
            hooks=[h[0].value for h in self._registered_hooks],
        )


class PluginManager:
    """
    Central plugin management system.
    
    Usage:
        manager = PluginManager(plugins_dir="/path/to/plugins")
        manager.discover_plugins()
        manager.enable_plugin("my-plugin")
        
        # Execute hooks
        results = await manager.execute_hook(
            HookType.CONTENT_POST_GENERATE,
            context={"content": content}
        )
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self.hooks: Dict[HookType, Dict[str, Callable]] = {h: {} for h in HookType}
        self.settings_store: Dict[str, Dict] = {}
    
    def discover_plugins(self) -> List[str]:
        """Discover plugins in the plugins directory."""
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return discovered
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                try:
                    plugin_name = item.name
                    plugin = self._load_plugin(item)
                    if plugin:
                        self.plugins[plugin_name] = plugin
                        discovered.append(plugin_name)
                        logger.info(f"Discovered plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {item.name}: {e}")
        
        return discovered
    
    def _load_plugin(self, plugin_path: Path) -> Optional[PluginBase]:
        """Load a plugin from a directory."""
        init_path = plugin_path / "__init__.py"
        
        spec = importlib.util.spec_from_file_location(
            plugin_path.name,
            init_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find PluginBase subclass
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PluginBase) and 
                obj is not PluginBase):
                return obj(self)
        
        return None
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self.plugins.get(name)
        if not plugin:
            logger.error(f"Plugin not found: {name}")
            return False
        
        try:
            # Check dependencies
            for dep in plugin.requires:
                if dep not in self.plugins or self.plugins[dep].state != PluginState.ENABLED:
                    logger.error(f"Plugin {name} requires {dep}")
                    return False
            
            # Load settings
            plugin.settings = self.load_plugin_settings(name)
            
            # Enable
            plugin.on_enable()
            plugin.state = PluginState.ENABLED
            logger.info(f"Enabled plugin: {name}")
            return True
        except Exception as e:
            plugin.state = PluginState.ERROR
            logger.error(f"Failed to enable plugin {name}: {e}")
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self.plugins.get(name)
        if not plugin:
            return False
        
        try:
            plugin.on_disable()
            plugin.state = PluginState.DISABLED
            logger.info(f"Disabled plugin: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable plugin {name}: {e}")
            return False
    
    def register_hook(self, hook_type: HookType, plugin_name: str, handler: Callable):
        """Register a hook handler."""
        self.hooks[hook_type][plugin_name] = handler
        logger.debug(f"Registered hook {hook_type.value} for {plugin_name}")
    
    def unregister_hook(self, hook_type: HookType, plugin_name: str):
        """Unregister a hook handler."""
        if plugin_name in self.hooks[hook_type]:
            del self.hooks[hook_type][plugin_name]
    
    async def execute_hook(
        self,
        hook_type: HookType,
        context: Dict[str, Any],
        stop_on_error: bool = False
    ) -> List[HookResult]:
        """
        Execute all handlers for a hook.
        
        Args:
            hook_type: The hook to execute
            context: Context data passed to handlers
            stop_on_error: Stop execution if a handler fails
        
        Returns:
            List of HookResult from each handler
        """
        results = []
        current_context = context.copy()
        
        for plugin_name, handler in self.hooks[hook_type].items():
            try:
                # Call handler (supports both sync and async)
                if inspect.iscoroutinefunction(handler):
                    result = await handler(current_context)
                else:
                    result = handler(current_context)
                
                # Handle result
                if isinstance(result, dict):
                    modified = result.get("modified", False)
                    if modified:
                        current_context.update(result)
                    
                    results.append(HookResult(
                        plugin_name=plugin_name,
                        success=True,
                        data=result,
                        modified=modified
                    ))
                else:
                    results.append(HookResult(
                        plugin_name=plugin_name,
                        success=True,
                        data=result
                    ))
                    
            except Exception as e:
                logger.error(f"Hook {hook_type.value} failed for {plugin_name}: {e}")
                results.append(HookResult(
                    plugin_name=plugin_name,
                    success=False,
                    error=str(e)
                ))
                
                if stop_on_error:
                    break
        
        return results
    
    def load_plugin_settings(self, name: str) -> Dict[str, Any]:
        """Load plugin settings from storage."""
        return self.settings_store.get(name, {})
    
    def save_plugin_settings(self, name: str, settings: Dict[str, Any]):
        """Save plugin settings to storage."""
        self.settings_store[name] = settings
    
    def get_all_plugins(self) -> List[PluginMetadata]:
        """Get metadata for all plugins."""
        return [p.get_metadata() for p in self.plugins.values()]
    
    def get_enabled_plugins(self) -> List[str]:
        """Get names of enabled plugins."""
        return [
            name for name, plugin in self.plugins.items()
            if plugin.state == PluginState.ENABLED
        ]


# Example built-in plugin
class ExamplePlugin(PluginBase):
    """
    Example plugin demonstrating the plugin system.
    """
    name = "example-plugin"
    version = "1.0.0"
    description = "Example plugin for IDKit"
    author = "IDKit Team"
    
    def on_enable(self):
        self.register_hook(HookType.CONTENT_POST_GENERATE, self.add_watermark)
        logger.info("Example plugin enabled")
    
    def add_watermark(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add watermark to generated content."""
        content = context.get("content", "")
        watermark = self.get_setting("watermark", "Generated by IDKit")
        
        return {
            "content": f"{content}\n\n{watermark}",
            "modified": True
        }


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
