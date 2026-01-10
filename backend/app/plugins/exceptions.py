"""
Plugin Exception Classes

Custom exceptions for the plugin system.
"""


class PluginError(Exception):
    """Base exception for plugin errors."""

    def __init__(self, message: str, plugin_name: str = None):
        super().__init__(message)
        self.plugin_name = plugin_name


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginActivationError(PluginError):
    """Raised when a plugin fails to activate."""
    pass


class PluginDeactivationError(PluginError):
    """Raised when a plugin fails to deactivate."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be resolved."""

    def __init__(
        self,
        message: str,
        plugin_name: str = None,
        missing_dependency: str = None,
    ):
        super().__init__(message, plugin_name)
        self.missing_dependency = missing_dependency


class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""

    def __init__(
        self,
        message: str,
        plugin_name: str = None,
        config_key: str = None,
    ):
        super().__init__(message, plugin_name)
        self.config_key = config_key


class PluginVersionError(PluginError):
    """Raised when plugin version is incompatible."""

    def __init__(
        self,
        message: str,
        plugin_name: str = None,
        required_version: str = None,
        actual_version: str = None,
    ):
        super().__init__(message, plugin_name)
        self.required_version = required_version
        self.actual_version = actual_version


class HookError(PluginError):
    """Raised when a hook operation fails."""

    def __init__(
        self,
        message: str,
        hook_name: str = None,
        plugin_name: str = None,
    ):
        super().__init__(message, plugin_name)
        self.hook_name = hook_name
