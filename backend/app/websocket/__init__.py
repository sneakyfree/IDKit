"""
IDKit WebSocket Module

Provides real-time communication infrastructure for:
- Notifications
- Job progress updates
- Direct messaging
- Live podcast streaming
- Feed updates
"""

from app.websocket.manager import ConnectionManager, connection_manager
from app.websocket.events import (
    WebSocketEvent,
    EventType,
    NotificationEvent,
    JobProgressEvent,
    MessageEvent,
    FeedUpdateEvent,
    LiveStreamEvent,
    ContentGenerationEvent,
    TwinEvent,
)
from app.websocket.auth import websocket_auth
from app.websocket.publisher import WebSocketPublisher, ws_publisher

__all__ = [
    # Manager
    "ConnectionManager",
    "connection_manager",
    # Events
    "WebSocketEvent",
    "EventType",
    "NotificationEvent",
    "JobProgressEvent",
    "MessageEvent",
    "FeedUpdateEvent",
    "LiveStreamEvent",
    "ContentGenerationEvent",
    "TwinEvent",
    # Auth
    "websocket_auth",
    # Publisher
    "WebSocketPublisher",
    "ws_publisher",
]
