"""
Plugin Base Classes

Defines the core plugin interface and metadata structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, Set
from datetime import datetime

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel


class PluginCapability(str, Enum):
    """Capabilities a plugin can provide."""
    API_ROUTES = "api_routes"           # Can register new API endpoints
    BACKGROUND_TASKS = "background"     # Can run background tasks
    EVENT_HANDLERS = "events"           # Can subscribe to events
    DATA_MODELS = "models"              # Can extend data models
    AI_PROCESSORS = "ai"                # Can add AI processing
    STORAGE_BACKENDS = "storage"        # Can provide storage backends
    AUTH_PROVIDERS = "auth"             # Can provide auth methods
    ANALYTICS = "analytics"             # Can add analytics tracking
    WEBHOOKS = "webhooks"               # Can handle webhooks
    MIDDLEWARE = "middleware"           # Can add middleware


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"


@dataclass
class PluginMeta:
    """
    Plugin metadata.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version (semver)
        description: Human-readable description
        author: Plugin author
        homepage: Plugin homepage URL
        license: Plugin license
        dependencies: List of plugin dependencies (name:version)
        capabilities: Set of plugin capabilities
        min_idkit_version: Minimum IDKit version required
        max_idkit_version: Maximum IDKit version supported (optional)
        tags: List of tags for categorization
    """
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = ""
    dependencies: List[str] = field(default_factory=list)
    capabilities: Set[PluginCapability] = field(default_factory=set)
    min_idkit_version: str = "1.0.0"
    max_idkit_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "license": self.license,
            "dependencies": self.dependencies,
            "capabilities": [c.value for c in self.capabilities],
            "min_idkit_version": self.min_idkit_version,
            "max_idkit_version": self.max_idkit_version,
            "tags": self.tags,
        }


class PluginConfig(BaseModel):
    """
    Base class for plugin configuration.

    Plugins should extend this to define their configuration schema.
    """
    enabled: bool = True

    class Config:
        extra = "allow"


@dataclass
class PluginContext:
    """
    Context provided to plugins during lifecycle.

    Contains references to IDKit services and utilities
    that plugins can use.
    """
    app: FastAPI
    config: Dict[str, Any]
    logger: Any  # structlog logger
    get_db: Callable  # Database session factory
    get_redis: Callable  # Redis client factory
    get_storage: Callable  # Storage service factory
    version: str  # IDKit version


class IDKitPlugin(ABC):
    """
    Base class for IDKit plugins.

    All plugins must inherit from this class and implement
    the required methods.

    Example:
        class MyPlugin(IDKitPlugin):
            meta = PluginMeta(
                name="my-plugin",
                version="1.0.0",
                description="My awesome plugin",
                capabilities={PluginCapability.API_ROUTES}
            )

            async def activate(self, context: PluginContext) -> None:
                self.logger = context.logger
                self.logger.info("MyPlugin activated!")

            async def deactivate(self) -> None:
                self.logger.info("MyPlugin deactivated!")

            def register_routes(self) -> APIRouter:
                router = APIRouter(prefix="/my-plugin", tags=["My Plugin"])

                @router.get("/hello")
                async def hello():
                    return {"message": "Hello from MyPlugin!"}

                return router
    """

    # Plugin metadata (must be overridden)
    meta: PluginMeta

    # Configuration class (can be overridden)
    config_class: Type[PluginConfig] = PluginConfig

    def __init__(self):
        """Initialize the plugin."""
        self._status = PluginStatus.UNLOADED
        self._config: Optional[PluginConfig] = None
        self._context: Optional[PluginContext] = None
        self._activated_at: Optional[datetime] = None
        self._error: Optional[str] = None

    @property
    def status(self) -> PluginStatus:
        """Get plugin status."""
        return self._status

    @property
    def config(self) -> Optional[PluginConfig]:
        """Get plugin configuration."""
        return self._config

    @property
    def context(self) -> Optional[PluginContext]:
        """Get plugin context."""
        return self._context

    @property
    def is_active(self) -> bool:
        """Check if plugin is active."""
        return self._status == PluginStatus.ACTIVATED

    def set_config(self, config_data: Dict[str, Any]) -> None:
        """
        Set plugin configuration.

        Args:
            config_data: Configuration dictionary
        """
        self._config = self.config_class(**config_data)

    def set_context(self, context: PluginContext) -> None:
        """
        Set plugin context.

        Args:
            context: Plugin context with app services
        """
        self._context = context

    @abstractmethod
    async def activate(self, context: PluginContext) -> None:
        """
        Activate the plugin.

        Called when the plugin is being activated.
        Use this to initialize resources, start background tasks, etc.

        Args:
            context: Plugin context with app services
        """
        pass

    @abstractmethod
    async def deactivate(self) -> None:
        """
        Deactivate the plugin.

        Called when the plugin is being deactivated.
        Use this to cleanup resources, stop background tasks, etc.
        """
        pass

    def register_routes(self) -> Optional[APIRouter]:
        """
        Register API routes.

        Override this to add custom API endpoints.

        Returns:
            FastAPI router with endpoints, or None if no routes.
        """
        return None

    def register_middleware(self, app: FastAPI) -> None:
        """
        Register middleware.

        Override this to add custom middleware to the app.

        Args:
            app: The FastAPI application
        """
        pass

    def register_event_handlers(self) -> Dict[str, List[Callable]]:
        """
        Register event handlers.

        Override this to subscribe to application events.

        Returns:
            Dictionary mapping event names to handler functions.
        """
        return {}

    def register_background_tasks(self) -> List[Callable]:
        """
        Register background tasks.

        Override this to add periodic background tasks.

        Returns:
            List of async task functions.
        """
        return []

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform plugin health check.

        Override this to add custom health checks.

        Returns:
            Health check result dictionary.
        """
        return {
            "status": "healthy",
            "plugin": self.meta.name,
            "version": self.meta.version,
        }

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.

        Returns:
            Plugin info dictionary.
        """
        return {
            "meta": self.meta.to_dict(),
            "status": self._status.value,
            "activated_at": self._activated_at.isoformat() if self._activated_at else None,
            "error": self._error,
            "config_enabled": self._config.enabled if self._config else True,
        }


class PluginBase(IDKitPlugin):
    """
    Convenience base class with common utilities.

    Provides default implementations and helper methods.
    """

    def __init__(self):
        super().__init__()
        self._logger = None
        self._db = None
        self._redis = None

    @property
    def logger(self):
        """Get the plugin logger."""
        return self._logger

    async def activate(self, context: PluginContext) -> None:
        """Default activation with common setup."""
        self._context = context
        self._logger = context.logger.bind(plugin=self.meta.name)
        self._status = PluginStatus.ACTIVATED
        self._activated_at = datetime.utcnow()

        self._logger.info(
            "Plugin activated",
            version=self.meta.version,
        )

        # Call custom activation
        await self.on_activate()

    async def deactivate(self) -> None:
        """Default deactivation with cleanup."""
        await self.on_deactivate()

        self._status = PluginStatus.DEACTIVATED

        if self._logger:
            self._logger.info("Plugin deactivated")

    async def on_activate(self) -> None:
        """Override this for custom activation logic."""
        pass

    async def on_deactivate(self) -> None:
        """Override this for custom deactivation logic."""
        pass

    async def get_db(self):
        """Get database session."""
        if self._context:
            return await self._context.get_db()
        return None

    async def get_redis(self):
        """Get Redis client."""
        if self._context:
            return await self._context.get_redis()
        return None
