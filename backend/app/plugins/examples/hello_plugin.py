"""
Hello World Plugin

A minimal example plugin demonstrating the plugin architecture.
"""

from typing import Any, Dict, List, Callable, Optional
from fastapi import APIRouter

from app.plugins.base import (
    PluginBase,
    PluginMeta,
    PluginCapability,
    PluginConfig,
    PluginContext,
)
from app.plugins.hooks import register_hook


class HelloPluginConfig(PluginConfig):
    """Configuration for HelloPlugin."""
    greeting: str = "Hello"
    exclamation: bool = True


class HelloPlugin(PluginBase):
    """
    A simple Hello World plugin.

    Demonstrates:
    - Custom configuration
    - API route registration
    - Event handling
    - Background tasks
    """

    meta = PluginMeta(
        name="hello-plugin",
        version="1.0.0",
        description="A friendly greeting plugin",
        author="IDKit Team",
        capabilities={
            PluginCapability.API_ROUTES,
            PluginCapability.EVENT_HANDLERS,
        },
        tags=["example", "greeting"],
    )

    config_class = HelloPluginConfig

    def __init__(self):
        super().__init__()
        self._greet_count = 0

    async def on_activate(self) -> None:
        """Called when plugin is activated."""
        self.logger.info(
            "HelloPlugin ready to greet!",
            greeting=self.config.greeting,
        )

    async def on_deactivate(self) -> None:
        """Called when plugin is deactivated."""
        self.logger.info(
            "HelloPlugin saying goodbye!",
            total_greetings=self._greet_count,
        )

    def register_routes(self) -> APIRouter:
        """Register plugin API routes."""
        router = APIRouter()

        @router.get("/hello")
        async def hello() -> Dict[str, Any]:
            """Get a greeting."""
            self._greet_count += 1
            greeting = self.config.greeting
            if self.config.exclamation:
                greeting += "!"
            return {
                "message": greeting,
                "greeting_number": self._greet_count,
            }

        @router.get("/hello/{name}")
        async def hello_name(name: str) -> Dict[str, Any]:
            """Get a personalized greeting."""
            self._greet_count += 1
            greeting = f"{self.config.greeting}, {name}"
            if self.config.exclamation:
                greeting += "!"
            return {
                "message": greeting,
                "greeting_number": self._greet_count,
            }

        @router.get("/stats")
        async def stats() -> Dict[str, Any]:
            """Get greeting statistics."""
            return {
                "total_greetings": self._greet_count,
                "plugin_version": self.meta.version,
            }

        return router

    def register_event_handlers(self) -> Dict[str, List[Callable]]:
        """Register event handlers."""

        async def on_user_created(user: Any) -> None:
            """Welcome new users."""
            self.logger.info(
                "New user! Sending greeting",
                user_id=getattr(user, "id", "unknown"),
            )

        return {
            "user.created": [on_user_created],
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "plugin": self.meta.name,
            "version": self.meta.version,
            "greet_count": self._greet_count,
        }


# Plugin factory function (alternative to class discovery)
def get_plugin() -> HelloPlugin:
    """Factory function to create plugin instance."""
    return HelloPlugin()
