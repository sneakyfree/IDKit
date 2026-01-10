"""
WebSocket Connection Manager

Manages WebSocket connections, rooms, and message broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.websocket.events import EventType, WebSocketEvent

logger = logging.getLogger(__name__)


class Connection:
    """Represents a single WebSocket connection."""

    def __init__(
        self,
        websocket: WebSocket,
        user_id: Optional[UUID] = None,
        connection_id: Optional[str] = None,
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id or str(UUID(int=0))
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.rooms: set[str] = set()
        self.metadata: dict[str, Any] = {}

    async def send(self, event: WebSocketEvent) -> bool:
        """Send event to this connection."""
        try:
            await self.websocket.send_json(event.model_dump(mode="json"))
            return True
        except Exception as e:
            logger.error(f"Failed to send to connection {self.connection_id}: {e}")
            return False

    async def send_raw(self, data: dict) -> bool:
        """Send raw JSON data to this connection."""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send raw to connection {self.connection_id}: {e}")
            return False


class ConnectionManager:
    """
    Manages all WebSocket connections.

    Features:
    - User-based connections (multiple connections per user)
    - Room-based broadcasting
    - Heartbeat/ping-pong support
    - Redis pub/sub for horizontal scaling
    """

    def __init__(self):
        # user_id -> list of connections
        self._user_connections: dict[UUID, list[Connection]] = {}
        # connection_id -> connection
        self._connections: dict[str, Connection] = {}
        # room_name -> set of connection_ids
        self._rooms: dict[str, set[str]] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[UUID] = None,
        connection_id: Optional[str] = None,
    ) -> Connection:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: Optional user ID (for authenticated connections)
            connection_id: Optional unique connection ID

        Returns:
            Connection object
        """
        await websocket.accept()

        import uuid as uuid_module
        if connection_id is None:
            connection_id = str(uuid_module.uuid4())

        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            connection_id=connection_id,
        )

        async with self._lock:
            self._connections[connection_id] = connection

            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = []
                self._user_connections[user_id].append(connection)

        logger.info(
            f"WebSocket connected: {connection_id}"
            f" (user: {user_id or 'anonymous'})"
        )

        # Send connected event
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data={
                "connection_id": connection_id,
                "user_id": str(user_id) if user_id else None,
            }
        ))

        return connection

    async def disconnect(self, connection: Connection) -> None:
        """Disconnect and cleanup a connection."""
        async with self._lock:
            # Remove from connections dict
            if connection.connection_id in self._connections:
                del self._connections[connection.connection_id]

            # Remove from user connections
            if connection.user_id and connection.user_id in self._user_connections:
                self._user_connections[connection.user_id] = [
                    c for c in self._user_connections[connection.user_id]
                    if c.connection_id != connection.connection_id
                ]
                # Clean up empty user entry
                if not self._user_connections[connection.user_id]:
                    del self._user_connections[connection.user_id]

            # Remove from all rooms
            for room_name in list(connection.rooms):
                await self._leave_room_unlocked(connection, room_name)

        logger.info(
            f"WebSocket disconnected: {connection.connection_id}"
            f" (user: {connection.user_id or 'anonymous'})"
        )

    async def set_user(self, connection: Connection, user_id: UUID) -> None:
        """Set the user ID for a connection (post-authentication)."""
        async with self._lock:
            # Remove from old user list if exists
            if connection.user_id and connection.user_id in self._user_connections:
                self._user_connections[connection.user_id] = [
                    c for c in self._user_connections[connection.user_id]
                    if c.connection_id != connection.connection_id
                ]

            # Set new user ID
            connection.user_id = user_id

            # Add to new user list
            if user_id not in self._user_connections:
                self._user_connections[user_id] = []
            self._user_connections[user_id].append(connection)

    # =========================================================================
    # Room Management
    # =========================================================================

    async def join_room(self, connection: Connection, room_name: str) -> None:
        """Add connection to a room."""
        async with self._lock:
            await self._join_room_unlocked(connection, room_name)

    async def _join_room_unlocked(self, connection: Connection, room_name: str) -> None:
        """Join room without lock (internal use)."""
        if room_name not in self._rooms:
            self._rooms[room_name] = set()

        self._rooms[room_name].add(connection.connection_id)
        connection.rooms.add(room_name)

        logger.debug(
            f"Connection {connection.connection_id} joined room {room_name}"
        )

    async def leave_room(self, connection: Connection, room_name: str) -> None:
        """Remove connection from a room."""
        async with self._lock:
            await self._leave_room_unlocked(connection, room_name)

    async def _leave_room_unlocked(self, connection: Connection, room_name: str) -> None:
        """Leave room without lock (internal use)."""
        if room_name in self._rooms:
            self._rooms[room_name].discard(connection.connection_id)
            # Clean up empty room
            if not self._rooms[room_name]:
                del self._rooms[room_name]

        connection.rooms.discard(room_name)

        logger.debug(
            f"Connection {connection.connection_id} left room {room_name}"
        )

    # =========================================================================
    # Broadcasting
    # =========================================================================

    async def send_to_user(
        self,
        user_id: UUID,
        event: WebSocketEvent,
    ) -> int:
        """
        Send event to all connections of a user.

        Returns:
            Number of successful sends
        """
        async with self._lock:
            connections = self._user_connections.get(user_id, [])

        sent = 0
        for connection in connections:
            if await connection.send(event):
                sent += 1

        return sent

    async def send_to_room(
        self,
        room_name: str,
        event: WebSocketEvent,
        exclude_connection: Optional[str] = None,
    ) -> int:
        """
        Broadcast event to all connections in a room.

        Args:
            room_name: Name of the room
            event: Event to send
            exclude_connection: Optional connection ID to exclude

        Returns:
            Number of successful sends
        """
        async with self._lock:
            connection_ids = self._rooms.get(room_name, set()).copy()

        sent = 0
        for conn_id in connection_ids:
            if conn_id == exclude_connection:
                continue

            connection = self._connections.get(conn_id)
            if connection and await connection.send(event):
                sent += 1

        return sent

    async def broadcast(
        self,
        event: WebSocketEvent,
        exclude_connection: Optional[str] = None,
    ) -> int:
        """
        Broadcast event to all connections.

        Returns:
            Number of successful sends
        """
        async with self._lock:
            connections = list(self._connections.values())

        sent = 0
        for connection in connections:
            if connection.connection_id == exclude_connection:
                continue
            if await connection.send(event):
                sent += 1

        return sent

    async def send_to_connection(
        self,
        connection_id: str,
        event: WebSocketEvent,
    ) -> bool:
        """Send event to a specific connection."""
        connection = self._connections.get(connection_id)
        if connection:
            return await connection.send(event)
        return False

    # =========================================================================
    # Status & Utilities
    # =========================================================================

    def is_user_online(self, user_id: UUID) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0

    def get_user_connection_count(self, user_id: UUID) -> int:
        """Get the number of connections for a user."""
        return len(self._user_connections.get(user_id, []))

    def get_room_size(self, room_name: str) -> int:
        """Get the number of connections in a room."""
        return len(self._rooms.get(room_name, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self._connections),
            "total_users": len(self._user_connections),
            "total_rooms": len(self._rooms),
            "rooms": {
                name: len(connections)
                for name, connections in self._rooms.items()
            },
        }

    # =========================================================================
    # Heartbeat
    # =========================================================================

    async def handle_ping(self, connection: Connection) -> None:
        """Handle ping from client."""
        connection.last_ping = datetime.utcnow()
        await connection.send(WebSocketEvent(
            type=EventType.PONG,
            data={"timestamp": datetime.utcnow().isoformat()}
        ))

    async def cleanup_stale_connections(
        self,
        max_idle_seconds: int = 300,
    ) -> int:
        """
        Remove connections that haven't pinged recently.

        Returns:
            Number of connections removed
        """
        now = datetime.utcnow()
        stale_connections = []

        async with self._lock:
            for connection in self._connections.values():
                idle_time = (now - connection.last_ping).total_seconds()
                if idle_time > max_idle_seconds:
                    stale_connections.append(connection)

        removed = 0
        for connection in stale_connections:
            try:
                await connection.websocket.close()
            except Exception:
                pass
            await self.disconnect(connection)
            removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} stale WebSocket connections")

        return removed


# Global connection manager instance
connection_manager = ConnectionManager()


# =========================================================================
# Redis Pub/Sub Integration for Horizontal Scaling
# =========================================================================

class RedisWebSocketBridge:
    """
    Bridges WebSocket events with Redis pub/sub for horizontal scaling.

    When running multiple API instances, this ensures events reach
    users connected to any instance.
    """

    CHANNEL_PREFIX = "ws:"

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._redis = None
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self, redis_client) -> None:
        """Connect to Redis and start listening."""
        self._redis = redis_client
        self._pubsub = redis_client.pubsub()

        # Subscribe to broadcast channel
        await self._pubsub.subscribe(f"{self.CHANNEL_PREFIX}broadcast")

        # Start listener task
        self._listener_task = asyncio.create_task(self._listen())

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()

    async def _listen(self) -> None:
        """Listen for Redis messages and broadcast to local connections."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data = json.loads(message["data"])
                    event = WebSocketEvent(**data["event"])

                    # Determine broadcast target
                    target_type = data.get("target_type")
                    target_id = data.get("target_id")

                    if target_type == "user":
                        await self.manager.send_to_user(
                            UUID(target_id),
                            event,
                        )
                    elif target_type == "room":
                        await self.manager.send_to_room(
                            target_id,
                            event,
                        )
                    elif target_type == "broadcast":
                        await self.manager.broadcast(event)

                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")

        except asyncio.CancelledError:
            pass

    async def publish_to_user(
        self,
        user_id: UUID,
        event: WebSocketEvent,
    ) -> None:
        """Publish event to user across all instances."""
        await self._publish({
            "target_type": "user",
            "target_id": str(user_id),
            "event": event.model_dump(mode="json"),
        })

    async def publish_to_room(
        self,
        room_name: str,
        event: WebSocketEvent,
    ) -> None:
        """Publish event to room across all instances."""
        await self._publish({
            "target_type": "room",
            "target_id": room_name,
            "event": event.model_dump(mode="json"),
        })

    async def publish_broadcast(
        self,
        event: WebSocketEvent,
    ) -> None:
        """Publish event to all connections across all instances."""
        await self._publish({
            "target_type": "broadcast",
            "target_id": None,
            "event": event.model_dump(mode="json"),
        })

    async def _publish(self, message: dict) -> None:
        """Publish message to Redis."""
        if self._redis:
            await self._redis.publish(
                f"{self.CHANNEL_PREFIX}broadcast",
                json.dumps(message),
            )


# Global Redis bridge (initialized on startup)
redis_bridge: Optional[RedisWebSocketBridge] = None
