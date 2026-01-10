"""
Plugin Hook System

Provides a hook/event system for plugins to subscribe to
and emit events.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Awaitable
import asyncio
from functools import wraps


class HookPriority(IntEnum):
    """Priority levels for hook handlers."""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    SYSTEM = 999  # Reserved for internal handlers


@dataclass
class HookHandler:
    """A registered hook handler."""
    callback: Callable[..., Awaitable[Any]]
    priority: HookPriority
    plugin_name: Optional[str] = None
    once: bool = False


@dataclass
class Hook:
    """
    A hook that can be subscribed to.

    Hooks allow plugins to:
    - Subscribe to events from the core system
    - Subscribe to events from other plugins
    - Emit their own events
    """
    name: str
    description: str = ""
    handlers: List[HookHandler] = field(default_factory=list)

    def add_handler(
        self,
        callback: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        plugin_name: Optional[str] = None,
        once: bool = False,
    ) -> None:
        """Add a handler to this hook."""
        handler = HookHandler(
            callback=callback,
            priority=priority,
            plugin_name=plugin_name,
            once=once,
        )
        self.handlers.append(handler)
        # Sort by priority (highest first)
        self.handlers.sort(key=lambda h: -h.priority)

    def remove_handler(self, callback: Callable) -> bool:
        """Remove a handler from this hook."""
        for i, handler in enumerate(self.handlers):
            if handler.callback == callback:
                self.handlers.pop(i)
                return True
        return False

    def remove_plugin_handlers(self, plugin_name: str) -> int:
        """Remove all handlers from a specific plugin."""
        original_count = len(self.handlers)
        self.handlers = [
            h for h in self.handlers
            if h.plugin_name != plugin_name
        ]
        return original_count - len(self.handlers)

    async def trigger(self, *args, **kwargs) -> List[Any]:
        """
        Trigger all handlers for this hook.

        Returns list of results from all handlers.
        """
        results = []
        to_remove = []

        for handler in self.handlers:
            try:
                result = await handler.callback(*args, **kwargs)
                results.append(result)

                if handler.once:
                    to_remove.append(handler)
            except Exception as e:
                # Log error but continue to next handler
                results.append({"error": str(e)})

        # Remove one-time handlers
        for handler in to_remove:
            self.handlers.remove(handler)

        return results

    async def trigger_until(
        self,
        stop_condition: Callable[[Any], bool],
        *args,
        **kwargs,
    ) -> Optional[Any]:
        """
        Trigger handlers until one returns a value that matches stop condition.

        Useful for handlers that can "claim" an event.
        """
        for handler in self.handlers:
            try:
                result = await handler.callback(*args, **kwargs)
                if stop_condition(result):
                    return result
            except Exception:
                continue
        return None


class HookRegistry:
    """
    Registry for managing hooks.

    Provides a centralized place to register and trigger hooks.
    """

    _instance: Optional["HookRegistry"] = None

    def __new__(cls) -> "HookRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._hooks: Dict[str, Hook] = {}
        return cls._instance

    def register(self, name: str, description: str = "") -> Hook:
        """
        Register a new hook.

        Args:
            name: Unique hook name
            description: Hook description

        Returns:
            The registered hook
        """
        if name not in self._hooks:
            self._hooks[name] = Hook(name=name, description=description)
        return self._hooks[name]

    def get(self, name: str) -> Optional[Hook]:
        """Get a hook by name."""
        return self._hooks.get(name)

    def subscribe(
        self,
        hook_name: str,
        callback: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        plugin_name: Optional[str] = None,
        once: bool = False,
    ) -> None:
        """
        Subscribe to a hook.

        Args:
            hook_name: Name of hook to subscribe to
            callback: Async callback function
            priority: Handler priority
            plugin_name: Plugin that owns this handler
            once: If True, handler is removed after first call
        """
        hook = self._hooks.get(hook_name)
        if hook is None:
            hook = self.register(hook_name)

        hook.add_handler(
            callback=callback,
            priority=priority,
            plugin_name=plugin_name,
            once=once,
        )

    def unsubscribe(self, hook_name: str, callback: Callable) -> bool:
        """
        Unsubscribe from a hook.

        Returns True if handler was found and removed.
        """
        hook = self._hooks.get(hook_name)
        if hook:
            return hook.remove_handler(callback)
        return False

    def unsubscribe_plugin(self, plugin_name: str) -> int:
        """
        Remove all handlers for a plugin.

        Returns count of handlers removed.
        """
        total_removed = 0
        for hook in self._hooks.values():
            total_removed += hook.remove_plugin_handlers(plugin_name)
        return total_removed

    async def trigger(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Trigger a hook.

        Args:
            hook_name: Name of hook to trigger
            *args: Positional arguments for handlers
            **kwargs: Keyword arguments for handlers

        Returns:
            List of results from all handlers
        """
        hook = self._hooks.get(hook_name)
        if hook:
            return await hook.trigger(*args, **kwargs)
        return []

    async def trigger_filter(
        self,
        hook_name: str,
        value: Any,
        *args,
        **kwargs,
    ) -> Any:
        """
        Trigger a filter hook.

        Each handler receives the value and can modify it.
        The final modified value is returned.

        Args:
            hook_name: Name of hook to trigger
            value: Initial value to filter

        Returns:
            Filtered value after all handlers
        """
        hook = self._hooks.get(hook_name)
        if hook:
            for handler in hook.handlers:
                try:
                    value = await handler.callback(value, *args, **kwargs)
                except Exception:
                    continue  # Skip failed handlers
        return value

    def list_hooks(self) -> List[str]:
        """List all registered hooks."""
        return list(self._hooks.keys())

    def get_info(self) -> Dict:
        """Get registry info."""
        return {
            "hook_count": len(self._hooks),
            "hooks": {
                name: {
                    "description": hook.description,
                    "handler_count": len(hook.handlers),
                }
                for name, hook in self._hooks.items()
            },
        }

    def clear(self) -> None:
        """Clear all hooks."""
        self._hooks.clear()


# Global hook registry
_hook_registry: Optional[HookRegistry] = None


def get_hook_registry() -> HookRegistry:
    """Get the global hook registry."""
    global _hook_registry
    if _hook_registry is None:
        _hook_registry = HookRegistry()
    return _hook_registry


def register_hook(
    hook_name: str,
    priority: HookPriority = HookPriority.NORMAL,
    plugin_name: Optional[str] = None,
    once: bool = False,
):
    """
    Decorator to register a function as a hook handler.

    Usage:
        @register_hook("user.created")
        async def on_user_created(user):
            print(f"User created: {user.id}")
    """
    def decorator(func: Callable):
        registry = get_hook_registry()
        registry.subscribe(
            hook_name=hook_name,
            callback=func,
            priority=priority,
            plugin_name=plugin_name,
            once=once,
        )
        return func
    return decorator


async def trigger_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """
    Trigger a hook with the given arguments.

    Convenience function for triggering hooks.
    """
    registry = get_hook_registry()
    return await registry.trigger(hook_name, *args, **kwargs)


# Pre-defined system hooks
SYSTEM_HOOKS = [
    # Application lifecycle
    ("app.startup", "Triggered when the application starts"),
    ("app.shutdown", "Triggered when the application shuts down"),
    # User events
    ("user.created", "Triggered when a user is created"),
    ("user.updated", "Triggered when a user is updated"),
    ("user.deleted", "Triggered when a user is deleted"),
    ("user.login", "Triggered when a user logs in"),
    ("user.logout", "Triggered when a user logs out"),
    # Content events
    ("content.created", "Triggered when content is created"),
    ("content.published", "Triggered when content is published"),
    ("content.updated", "Triggered when content is updated"),
    ("content.deleted", "Triggered when content is deleted"),
    # AI events
    ("ai.generation.started", "Triggered when AI generation starts"),
    ("ai.generation.completed", "Triggered when AI generation completes"),
    ("ai.generation.failed", "Triggered when AI generation fails"),
    # Plugin events
    ("plugin.activated", "Triggered when a plugin is activated"),
    ("plugin.deactivated", "Triggered when a plugin is deactivated"),
]


def register_system_hooks() -> None:
    """Register all system hooks."""
    registry = get_hook_registry()
    for name, description in SYSTEM_HOOKS:
        registry.register(name, description)
