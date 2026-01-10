"""
Analytics Plugin Example

A more complex example demonstrating background tasks,
database access, and hook subscriptions.
"""

from typing import Any, Dict, List, Callable
from datetime import datetime, timedelta
import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.plugins.base import (
    PluginBase,
    PluginMeta,
    PluginCapability,
    PluginConfig,
)
from app.plugins.hooks import HookPriority


class AnalyticsConfig(PluginConfig):
    """Configuration for AnalyticsPlugin."""
    tracking_enabled: bool = True
    retention_days: int = 30
    batch_size: int = 100
    flush_interval_seconds: int = 60


class EventData(BaseModel):
    """Analytics event data."""
    event_type: str
    timestamp: datetime
    user_id: str | None = None
    properties: Dict[str, Any] = {}


class AnalyticsPlugin(PluginBase):
    """
    Analytics tracking plugin.

    Demonstrates:
    - Background task for batch processing
    - Database access
    - Multiple event subscriptions
    - Complex configuration
    """

    meta = PluginMeta(
        name="analytics-plugin",
        version="1.0.0",
        description="Track and analyze user behavior",
        author="IDKit Team",
        capabilities={
            PluginCapability.API_ROUTES,
            PluginCapability.BACKGROUND_TASKS,
            PluginCapability.EVENT_HANDLERS,
            PluginCapability.ANALYTICS,
        },
        tags=["analytics", "tracking", "metrics"],
    )

    config_class = AnalyticsConfig

    def __init__(self):
        super().__init__()
        self._event_buffer: List[EventData] = []
        self._event_counts: Dict[str, int] = {}
        self._flush_task: asyncio.Task | None = None

    async def on_activate(self) -> None:
        """Initialize analytics tracking."""
        self.logger.info(
            "Analytics plugin activated",
            tracking_enabled=self.config.tracking_enabled,
        )

    async def on_deactivate(self) -> None:
        """Cleanup and flush remaining events."""
        # Flush any remaining events
        await self._flush_events()
        self.logger.info("Analytics plugin deactivated")

    def register_routes(self) -> APIRouter:
        """Register analytics API routes."""
        router = APIRouter()

        @router.post("/track")
        async def track_event(event: EventData) -> Dict[str, Any]:
            """Track a custom event."""
            if not self.config.tracking_enabled:
                return {"tracked": False, "reason": "tracking_disabled"}

            self._buffer_event(event)
            return {
                "tracked": True,
                "event_type": event.event_type,
            }

        @router.get("/summary")
        async def get_summary() -> Dict[str, Any]:
            """Get analytics summary."""
            return {
                "event_counts": self._event_counts,
                "buffer_size": len(self._event_buffer),
                "tracking_enabled": self.config.tracking_enabled,
            }

        @router.get("/events/{event_type}/count")
        async def get_event_count(event_type: str) -> Dict[str, Any]:
            """Get count for a specific event type."""
            return {
                "event_type": event_type,
                "count": self._event_counts.get(event_type, 0),
            }

        @router.post("/flush")
        async def flush_events() -> Dict[str, Any]:
            """Manually flush event buffer."""
            count = await self._flush_events()
            return {
                "flushed": True,
                "events_flushed": count,
            }

        return router

    def register_event_handlers(self) -> Dict[str, List[Callable]]:
        """Subscribe to system events for automatic tracking."""

        async def track_user_login(user: Any) -> None:
            """Track user login events."""
            event = EventData(
                event_type="user.login",
                timestamp=datetime.utcnow(),
                user_id=str(getattr(user, "id", "unknown")),
                properties={"source": "system"},
            )
            self._buffer_event(event)

        async def track_content_created(content: Any) -> None:
            """Track content creation events."""
            event = EventData(
                event_type="content.created",
                timestamp=datetime.utcnow(),
                user_id=str(getattr(content, "user_id", "unknown")),
                properties={
                    "content_type": getattr(content, "type", "unknown"),
                },
            )
            self._buffer_event(event)

        async def track_content_published(content: Any) -> None:
            """Track content publish events."""
            event = EventData(
                event_type="content.published",
                timestamp=datetime.utcnow(),
                user_id=str(getattr(content, "user_id", "unknown")),
                properties={
                    "content_id": str(getattr(content, "id", "unknown")),
                    "platform": getattr(content, "platform", "unknown"),
                },
            )
            self._buffer_event(event)

        return {
            "user.login": [track_user_login],
            "content.created": [track_content_created],
            "content.published": [track_content_published],
        }

    def register_background_tasks(self) -> List[Callable]:
        """Register periodic flush task."""

        async def periodic_flush():
            """Periodically flush event buffer."""
            while True:
                await asyncio.sleep(self.config.flush_interval_seconds)
                try:
                    await self._flush_events()
                except Exception as e:
                    self.logger.error(
                        "Error flushing analytics events",
                        error=str(e),
                    )

        return [periodic_flush]

    def _buffer_event(self, event: EventData) -> None:
        """Add event to buffer."""
        if not self.config.tracking_enabled:
            return

        self._event_buffer.append(event)

        # Update counts
        self._event_counts[event.event_type] = (
            self._event_counts.get(event.event_type, 0) + 1
        )

        self.logger.debug(
            "Event buffered",
            event_type=event.event_type,
            buffer_size=len(self._event_buffer),
        )

        # Auto-flush if buffer is full
        if len(self._event_buffer) >= self.config.batch_size:
            asyncio.create_task(self._flush_events())

    async def _flush_events(self) -> int:
        """Flush buffered events to storage."""
        if not self._event_buffer:
            return 0

        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()

        # In a real implementation, this would write to a database
        # For this example, we just log
        self.logger.info(
            "Flushing analytics events",
            event_count=len(events_to_flush),
        )

        # Simulate database write
        # db = await self.get_db()
        # await db.execute(...)

        return len(events_to_flush)

    async def health_check(self) -> Dict[str, Any]:
        """Check analytics plugin health."""
        return {
            "status": "healthy",
            "plugin": self.meta.name,
            "version": self.meta.version,
            "tracking_enabled": self.config.tracking_enabled,
            "buffer_size": len(self._event_buffer),
            "total_events_tracked": sum(self._event_counts.values()),
        }


# Plugin instance
plugin = AnalyticsPlugin()
