"""
IDKit Plugin System

A flexible plugin architecture for extending IDKit functionality.

Plugins can:
- Register new API routes
- Add background tasks
- Extend data models
- Subscribe to application events
- Provide new AI processing capabilities

Usage:
    from app.plugins import PluginManager, IDKitPlugin

    # Get the plugin manager
    manager = PluginManager()

    # Load plugins from directory
    await manager.discover_plugins("/path/to/plugins")

    # Activate all plugins
    await manager.activate_all()
"""

from .base import (
    IDKitPlugin,
    PluginMeta,
    PluginConfig,
    PluginCapability,
)
from .registry import PluginRegistry, get_registry
from .loader import PluginLoader, discover_plugins
from .manager import PluginManager, get_plugin_manager
from .hooks import (
    HookRegistry,
    Hook,
    HookPriority,
    register_hook,
    trigger_hook,
)
from .exceptions import (
    PluginError,
    PluginLoadError,
    PluginActivationError,
    PluginDependencyError,
    PluginConfigError,
)

__all__ = [
    # Base classes
    "IDKitPlugin",
    "PluginMeta",
    "PluginConfig",
    "PluginCapability",
    # Registry
    "PluginRegistry",
    "get_registry",
    # Loader
    "PluginLoader",
    "discover_plugins",
    # Manager
    "PluginManager",
    "get_plugin_manager",
    # Hooks
    "HookRegistry",
    "Hook",
    "HookPriority",
    "register_hook",
    "trigger_hook",
    # Exceptions
    "PluginError",
    "PluginLoadError",
    "PluginActivationError",
    "PluginDependencyError",
    "PluginConfigError",
]
