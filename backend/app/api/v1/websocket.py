"""
WebSocket API Endpoints

Provides WebSocket endpoints for real-time features:
- /ws/main - Main connection for notifications and general events
- /ws/jobs/{job_id} - Job progress tracking
- /ws/messages - Direct messaging
- /ws/live/{session_id} - Live stream interaction
- /ws/feed - Real-time feed updates
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from app.websocket import (
    connection_manager,
    websocket_auth,
    WebSocketEvent,
    EventType,
    JobProgressEvent,
    MessageEvent,
    LiveStreamEvent,
)
from app.websocket.auth import WebSocketAuthMiddleware
from app.utils.redis import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Main WebSocket Connection
# =============================================================================

@router.websocket("/main")
async def websocket_main(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Main WebSocket connection for authenticated users.

    Features:
    - Notifications
    - Job progress updates
    - General events

    Authentication:
    - Via query param: ws://...?token=JWT_TOKEN
    - Via first message: {"type": "auth", "token": "JWT_TOKEN"}

    Client Messages:
    - {"type": "ping"} - Heartbeat
    - {"type": "auth", "token": "..."} - Authenticate
    - {"type": "subscribe", "channel": "..."} - Subscribe to channel
    - {"type": "unsubscribe", "channel": "..."} - Unsubscribe from channel

    Server Events:
    - See EventType enum for all event types
    """
    auth_middleware = WebSocketAuthMiddleware(websocket)

    # Try to authenticate from query param
    user = await auth_middleware.authenticate()

    # Accept and create connection
    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id if user else None,
    )

    try:
        # If authenticated, auto-join user-specific rooms
        if user:
            await connection_manager.join_room(
                connection,
                f"user:{user.id}",
            )
            await connection_manager.join_room(
                connection,
                f"notifications:{user.id}",
            )

        # Message handling loop
        while True:
            try:
                data = await websocket.receive_json()
                await handle_main_message(
                    connection,
                    auth_middleware,
                    data,
                )
            except WebSocketDisconnect:
                break

    finally:
        await connection_manager.disconnect(connection)


async def handle_main_message(
    connection,
    auth_middleware: WebSocketAuthMiddleware,
    data: dict,
) -> None:
    """Handle messages on the main WebSocket."""
    message_type = data.get("type")

    # Ping/Pong heartbeat
    if message_type == "ping":
        await connection_manager.handle_ping(connection)
        return

    # Authentication
    if message_type == "auth":
        user = await auth_middleware.authenticate_from_message(data)
        if user:
            await connection_manager.set_user(connection, user.id)
            await connection_manager.join_room(connection, f"user:{user.id}")
            await connection_manager.join_room(connection, f"notifications:{user.id}")
            await connection.send(WebSocketEvent(
                type=EventType.CONNECTED,
                data={"authenticated": True, "user_id": str(user.id)},
            ))
        else:
            await connection.send(WebSocketEvent(
                type=EventType.ERROR,
                data={"error": "Authentication failed"},
            ))
        return

    # Require authentication for other actions
    if not auth_middleware.is_authenticated:
        await connection.send(WebSocketEvent(
            type=EventType.ERROR,
            data={"error": "Authentication required"},
        ))
        return

    # Subscribe to channel
    if message_type == "subscribe":
        channel = data.get("channel")
        if channel:
            # Validate channel access (user can only subscribe to their own channels)
            user = auth_middleware.user
            if channel.startswith(f"user:{user.id}") or channel.startswith("public:"):
                await connection_manager.join_room(connection, channel)
                await connection.send(WebSocketEvent(
                    type=EventType.CONNECTED,
                    data={"subscribed": channel},
                ))
            else:
                await connection.send(WebSocketEvent(
                    type=EventType.ERROR,
                    data={"error": "Not authorized to subscribe to this channel"},
                ))
        return

    # Unsubscribe from channel
    if message_type == "unsubscribe":
        channel = data.get("channel")
        if channel:
            await connection_manager.leave_room(connection, channel)
            await connection.send(WebSocketEvent(
                type=EventType.CONNECTED,
                data={"unsubscribed": channel},
            ))
        return


# =============================================================================
# Job Progress WebSocket
# =============================================================================

@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for tracking job progress.

    Automatically subscribes to job updates and sends progress events.

    Events:
    - job_started - Job has started processing
    - job_progress - Progress update (0-100)
    - job_completed - Job finished successfully
    - job_failed - Job failed with error
    """
    user = await websocket_auth(websocket, token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
    )

    try:
        # Join job-specific room
        job_room = f"job:{job_id}"
        await connection_manager.join_room(connection, job_room)

        # Also join user's job room (for all user jobs)
        await connection_manager.join_room(connection, f"jobs:{user.id}")

        # Send initial status
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data={
                "job_id": job_id,
                "message": "Subscribed to job updates",
            },
        ))

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await connection_manager.handle_ping(connection)
            except WebSocketDisconnect:
                break

    finally:
        await connection_manager.disconnect(connection)


# =============================================================================
# Direct Messages WebSocket
# =============================================================================

@router.websocket("/messages")
async def websocket_messages(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for real-time direct messaging.

    Events:
    - message_new - New message received
    - message_read - Message was read
    - message_typing - User is typing
    - message_delivered - Message was delivered

    Client Messages:
    - {"type": "typing", "conversation_id": "..."} - Send typing indicator
    - {"type": "read", "message_id": "..."} - Mark message as read
    """
    user = await websocket_auth(websocket, token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
    )

    try:
        # Join user's message room
        await connection_manager.join_room(connection, f"messages:{user.id}")

        # Send connected event
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data={"message": "Connected to messaging"},
        ))

        # Message handling loop
        while True:
            try:
                data = await websocket.receive_json()
                await handle_message_event(connection, user, data)
            except WebSocketDisconnect:
                break

    finally:
        await connection_manager.disconnect(connection)


async def handle_message_event(connection, user, data: dict) -> None:
    """Handle direct messaging events."""
    message_type = data.get("type")

    if message_type == "ping":
        await connection_manager.handle_ping(connection)
        return

    if message_type == "typing":
        conversation_id = data.get("conversation_id")
        if conversation_id:
            # Broadcast typing indicator to conversation participants
            event = MessageEvent.typing(
                conversation_id=UUID(conversation_id),
                user_id=user.id,
                user_name=user.display_name or user.username,
                is_typing=data.get("is_typing", True),
            )
            # Send to conversation room (excluding sender)
            await connection_manager.send_to_room(
                f"conversation:{conversation_id}",
                event,
                exclude_connection=connection.connection_id,
            )
        return

    if message_type == "read":
        message_id = data.get("message_id")
        conversation_id = data.get("conversation_id")
        if message_id and conversation_id:
            # Broadcast read receipt
            event = WebSocketEvent(
                type=EventType.MESSAGE_READ,
                data={
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "reader_id": str(user.id),
                },
            )
            await connection_manager.send_to_room(
                f"conversation:{conversation_id}",
                event,
            )
        return

    if message_type == "join_conversation":
        conversation_id = data.get("conversation_id")
        if conversation_id:
            # Verify user is participant in conversation
            is_participant = await _verify_conversation_participant(
                user_id=user.id,
                conversation_id=conversation_id,
            )

            if not is_participant:
                await connection.send(WebSocketEvent(
                    type=EventType.ERROR,
                    data={"error": "Not authorized to join this conversation"},
                ))
                return

            await connection_manager.join_room(
                connection,
                f"conversation:{conversation_id}",
            )
            await connection.send(WebSocketEvent(
                type=EventType.CONNECTED,
                data={"joined_conversation": conversation_id},
            ))
        return


async def _verify_conversation_participant(user_id: UUID, conversation_id: str) -> bool:
    """
    Verify that a user is a participant in the given conversation.

    Checks the SocialDMConversation table to ensure the user owns the conversation.
    """
    from sqlalchemy import select
    from app.models.database import async_session_maker
    from app.models.social import SocialDMConversation

    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(SocialDMConversation.id).where(
                    SocialDMConversation.id == UUID(conversation_id),
                    SocialDMConversation.user_id == user_id,
                )
            )
            conversation = result.scalar_one_or_none()
            return conversation is not None

    except (ValueError, Exception):
        return False


def _is_admin_user(user) -> bool:
    """
    Check if user has admin privileges.

    Admin status is determined by:
    1. Email in ADMIN_EMAILS config list
    2. Enterprise subscription tier (as fallback)

    Note: In production, consider adding an explicit is_admin field to User model.
    """
    from app.config import settings

    # Check against configured admin emails
    admin_emails = getattr(settings, "admin_emails", [])
    if isinstance(admin_emails, str):
        admin_emails = [e.strip() for e in admin_emails.split(",") if e.strip()]

    if user.email in admin_emails:
        return True

    # Fallback: enterprise tier users have admin access to status endpoint
    if user.subscription_tier == "enterprise":
        return True

    return False


# =============================================================================
# Live Stream WebSocket
# =============================================================================

@router.websocket("/live/{session_id}")
async def websocket_live_stream(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for live stream interaction.

    Events:
    - live_viewer_joined - Viewer joined the stream
    - live_viewer_left - Viewer left the stream
    - live_comment - New comment on stream
    - live_reaction - Reaction (like, heart, etc.)
    - live_stats - Stats update (viewer count, etc.)
    - live_ended - Stream ended

    Client Messages:
    - {"type": "comment", "content": "..."} - Send comment
    - {"type": "reaction", "reaction_type": "like|heart|..."} - Send reaction
    """
    user = await websocket_auth(websocket, token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
    )

    live_room = f"live:{session_id}"

    try:
        # Join live stream room
        await connection_manager.join_room(connection, live_room)

        # Notify others of new viewer
        viewer_joined = WebSocketEvent(
            type=EventType.LIVE_VIEWER_JOINED,
            data={
                "session_id": session_id,
                "user_id": str(user.id),
                "user_name": user.display_name or user.username,
                "viewer_count": connection_manager.get_room_size(live_room),
            },
        )
        await connection_manager.send_to_room(
            live_room,
            viewer_joined,
            exclude_connection=connection.connection_id,
        )

        # Send connected event
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data={
                "session_id": session_id,
                "viewer_count": connection_manager.get_room_size(live_room),
            },
        ))

        # Message handling loop
        while True:
            try:
                data = await websocket.receive_json()
                await handle_live_event(connection, user, session_id, data)
            except WebSocketDisconnect:
                break

    finally:
        # Notify others of viewer leaving
        viewer_left = WebSocketEvent(
            type=EventType.LIVE_VIEWER_LEFT,
            data={
                "session_id": session_id,
                "user_id": str(user.id),
                "viewer_count": max(0, connection_manager.get_room_size(live_room) - 1),
            },
        )
        await connection_manager.send_to_room(
            live_room,
            viewer_left,
            exclude_connection=connection.connection_id,
        )
        await connection_manager.disconnect(connection)


async def handle_live_event(connection, user, session_id: str, data: dict) -> None:
    """Handle live stream events."""
    message_type = data.get("type")
    live_room = f"live:{session_id}"

    if message_type == "ping":
        await connection_manager.handle_ping(connection)
        return

    if message_type == "comment":
        content = data.get("content", "").strip()
        if content:
            import uuid
            event = LiveStreamEvent.comment(
                session_id=UUID(session_id),
                comment_id=uuid.uuid4(),
                user_id=user.id,
                user_name=user.display_name or user.username,
                content=content[:500],  # Limit comment length
            )
            await connection_manager.send_to_room(live_room, event)
        return

    if message_type == "reaction":
        reaction_type = data.get("reaction_type", "like")
        event = WebSocketEvent(
            type=EventType.LIVE_REACTION,
            data={
                "session_id": session_id,
                "user_id": str(user.id),
                "reaction_type": reaction_type,
            },
        )
        await connection_manager.send_to_room(live_room, event)
        return


# =============================================================================
# Feed Updates WebSocket
# =============================================================================

@router.websocket("/feed")
async def websocket_feed(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for real-time feed updates.

    Receives updates when:
    - Someone you follow posts
    - Your posts get liked/commented
    - Trending content updates

    Events:
    - feed_new_post - New post from followed user
    - feed_post_liked - Your post was liked
    - feed_post_commented - Your post was commented
    - feed_post_shared - Your post was shared
    """
    user = await websocket_auth(websocket, token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
    )

    try:
        # Join user's feed room
        await connection_manager.join_room(connection, f"feed:{user.id}")

        # Join public trending room
        await connection_manager.join_room(connection, "feed:trending")

        # Send connected event
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data={"message": "Connected to feed updates"},
        ))

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await connection_manager.handle_ping(connection)
            except WebSocketDisconnect:
                break

    finally:
        await connection_manager.disconnect(connection)


# =============================================================================
# Admin/Status WebSocket (for monitoring)
# =============================================================================

@router.websocket("/status")
async def websocket_status(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for connection status monitoring (admin only).

    Provides real-time stats about WebSocket connections.
    """
    user = await websocket_auth(websocket, token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Check if user has admin privileges
    if not _is_admin_user(user):
        await websocket.close(code=4003, reason="Admin access required")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
    )

    try:
        # Send initial stats
        await connection.send(WebSocketEvent(
            type=EventType.CONNECTED,
            data=connection_manager.get_stats(),
        ))

        # Periodically send stats
        while True:
            try:
                # Wait for message or send stats every 5 seconds
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=5.0,
                    )
                    if data.get("type") == "ping":
                        await connection_manager.handle_ping(connection)
                except asyncio.TimeoutError:
                    # Send stats update
                    await connection.send(WebSocketEvent(
                        type=EventType.CONNECTED,
                        data=connection_manager.get_stats(),
                    ))

            except WebSocketDisconnect:
                break

    finally:
        await connection_manager.disconnect(connection)
