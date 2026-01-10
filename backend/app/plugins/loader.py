"""
Plugin Loader

Handles discovering and loading plugins from various sources.
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import json
import tomli

from .base import IDKitPlugin, PluginMeta
from .registry import PluginRegistry, get_registry
from .exceptions import PluginLoadError, PluginDependencyError


class PluginLoader:
    """
    Loader for discovering and loading IDKit plugins.

    Supports loading from:
    - Python packages
    - Local directories
    - Plugin manifest files (JSON/TOML)
    """

    MANIFEST_FILES = ["plugin.json", "plugin.toml", "idkit_plugin.json"]
    PLUGIN_ENTRY_POINTS = ["plugin", "Plugin", "IDKitPlugin", "get_plugin"]

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        Initialize the plugin loader.

        Args:
            registry: Plugin registry to use (uses global if not provided)
        """
        self.registry = registry or get_registry()
        self._loaded_paths: List[str] = []

    def load_from_module(self, module_name: str) -> IDKitPlugin:
        """
        Load a plugin from a Python module.

        Args:
            module_name: Fully qualified module name (e.g., "idkit_plugins.my_plugin")

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If module cannot be loaded or has no plugin class
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import module '{module_name}': {e}"
            )

        return self._extract_plugin_from_module(module)

    def load_from_path(self, path: str) -> IDKitPlugin:
        """
        Load a plugin from a file path.

        Args:
            path: Path to the plugin Python file or directory

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        path = os.path.abspath(path)

        if os.path.isdir(path):
            return self._load_from_directory(path)
        elif os.path.isfile(path):
            return self._load_from_file(path)
        else:
            raise PluginLoadError(f"Path does not exist: {path}")

    def _load_from_file(self, filepath: str) -> IDKitPlugin:
        """Load plugin from a Python file."""
        if not filepath.endswith(".py"):
            raise PluginLoadError(f"Not a Python file: {filepath}")

        module_name = os.path.basename(filepath)[:-3]  # Remove .py
        spec = importlib.util.spec_from_file_location(module_name, filepath)

        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Cannot load module from {filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return self._extract_plugin_from_module(module)

    def _load_from_directory(self, dirpath: str) -> IDKitPlugin:
        """Load plugin from a directory (package)."""
        # Check for manifest file
        manifest = self._load_manifest(dirpath)

        # Find entry point
        entry_point = manifest.get("entry_point", "__init__.py")
        entry_file = os.path.join(dirpath, entry_point)

        if not os.path.exists(entry_file):
            # Try __init__.py
            entry_file = os.path.join(dirpath, "__init__.py")
            if not os.path.exists(entry_file):
                raise PluginLoadError(
                    f"No entry point found in plugin directory: {dirpath}"
                )

        # Add directory to path for imports
        parent_dir = os.path.dirname(dirpath)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Load the module
        plugin_name = os.path.basename(dirpath)
        module = importlib.import_module(plugin_name)

        plugin = self._extract_plugin_from_module(module, manifest)
        self._loaded_paths.append(dirpath)

        return plugin

    def _load_manifest(self, dirpath: str) -> Dict[str, Any]:
        """Load plugin manifest file if it exists."""
        for manifest_name in self.MANIFEST_FILES:
            manifest_path = os.path.join(dirpath, manifest_name)
            if os.path.exists(manifest_path):
                with open(manifest_path, "rb") as f:
                    if manifest_name.endswith(".toml"):
                        return tomli.load(f)
                    else:
                        return json.loads(f.read())
        return {}

    def _extract_plugin_from_module(
        self,
        module,
        manifest: Optional[Dict[str, Any]] = None,
    ) -> IDKitPlugin:
        """Extract plugin class/instance from a module."""
        plugin_class = None

        # Check for factory function first
        for entry_point in self.PLUGIN_ENTRY_POINTS:
            if hasattr(module, entry_point):
                attr = getattr(module, entry_point)

                if callable(attr) and not isinstance(attr, type):
                    # It's a factory function
                    result = attr()
                    if isinstance(result, IDKitPlugin):
                        self.registry.register(result)
                        return result
                    elif isinstance(result, type) and issubclass(result, IDKitPlugin):
                        plugin_class = result
                        break
                elif isinstance(attr, type) and issubclass(attr, IDKitPlugin):
                    plugin_class = attr
                    break
                elif isinstance(attr, IDKitPlugin):
                    # Already an instance
                    self.registry.register(attr)
                    return attr

        # Search for any IDKitPlugin subclass
        if plugin_class is None:
            for name in dir(module):
                attr = getattr(module, name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, IDKitPlugin)
                    and attr is not IDKitPlugin
                ):
                    plugin_class = attr
                    break

        if plugin_class is None:
            raise PluginLoadError(
                f"No IDKitPlugin class found in module: {module.__name__}"
            )

        # Create instance
        plugin = plugin_class()

        # Apply manifest overrides if present
        if manifest:
            if "config" in manifest:
                plugin.set_config(manifest["config"])

        self.registry.register(plugin)
        return plugin

    def discover_plugins(
        self,
        search_paths: List[str],
        auto_load: bool = False,
    ) -> List[str]:
        """
        Discover plugins in the given search paths.

        Args:
            search_paths: List of directories to search
            auto_load: If True, automatically load discovered plugins

        Returns:
            List of discovered plugin paths
        """
        discovered = []

        for search_path in search_paths:
            if not os.path.isdir(search_path):
                continue

            for entry in os.listdir(search_path):
                entry_path = os.path.join(search_path, entry)

                # Check for plugin directory
                if os.path.isdir(entry_path):
                    if self._is_plugin_directory(entry_path):
                        discovered.append(entry_path)
                        if auto_load:
                            try:
                                self.load_from_path(entry_path)
                            except PluginLoadError:
                                pass

                # Check for single-file plugin
                elif entry.endswith(".py") and entry.startswith("idkit_plugin_"):
                    discovered.append(entry_path)
                    if auto_load:
                        try:
                            self.load_from_path(entry_path)
                        except PluginLoadError:
                            pass

        return discovered

    def _is_plugin_directory(self, dirpath: str) -> bool:
        """Check if a directory contains a plugin."""
        # Check for manifest
        for manifest_name in self.MANIFEST_FILES:
            if os.path.exists(os.path.join(dirpath, manifest_name)):
                return True

        # Check for __init__.py with plugin marker
        init_file = os.path.join(dirpath, "__init__.py")
        if os.path.exists(init_file):
            try:
                with open(init_file, "r") as f:
                    content = f.read()
                    if "IDKitPlugin" in content or "idkit_plugin" in content:
                        return True
            except Exception:
                pass

        return False


def discover_plugins(
    search_paths: List[str],
    auto_load: bool = False,
) -> List[str]:
    """
    Convenience function to discover plugins.

    Args:
        search_paths: List of directories to search
        auto_load: If True, automatically load discovered plugins

    Returns:
        List of discovered plugin paths
    """
    loader = PluginLoader()
    return loader.discover_plugins(search_paths, auto_load)
