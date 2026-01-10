"""
WebSocket Event Publisher

High-level service for publishing events to WebSocket clients
from anywhere in the application.
"""

import logging
from typing import Optional
from uuid import UUID

from app.websocket.manager import connection_manager, redis_bridge
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

logger = logging.getLogger(__name__)


class WebSocketPublisher:
    """
    Service for publishing WebSocket events.

    Uses Redis pub/sub when available for horizontal scaling.
    Falls back to direct broadcast when Redis is not available.
    """

    def __init__(self):
        self.manager = connection_manager
        self.bridge = redis_bridge

    async def _publish_to_user(
        self,
        user_id: UUID,
        event: WebSocketEvent,
    ) -> int:
        """Publish event to a specific user."""
        if self.bridge and self.bridge._redis:
            await self.bridge.publish_to_user(user_id, event)
            # Also send locally for immediate delivery
            return await self.manager.send_to_user(user_id, event)
        else:
            return await self.manager.send_to_user(user_id, event)

    async def _publish_to_room(
        self,
        room_name: str,
        event: WebSocketEvent,
    ) -> int:
        """Publish event to a room."""
        if self.bridge and self.bridge._redis:
            await self.bridge.publish_to_room(room_name, event)
            return await self.manager.send_to_room(room_name, event)
        else:
            return await self.manager.send_to_room(room_name, event)

    # =========================================================================
    # Notification Events
    # =========================================================================

    async def send_notification(
        self,
        user_id: UUID,
        notification_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        actor_name: Optional[str] = None,
        actor_avatar: Optional[str] = None,
    ) -> int:
        """Send a notification to a user."""
        event = NotificationEvent.create(
            notification_id=notification_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_avatar=actor_avatar,
        )
        return await self._publish_to_room(f"notifications:{user_id}", event)

    async def send_notification_count(
        self,
        user_id: UUID,
        unread_count: int,
    ) -> int:
        """Send notification count update."""
        event = WebSocketEvent(
            type=EventType.NOTIFICATION_COUNT,
            data={"unread_count": unread_count},
        )
        return await self._publish_to_room(f"notifications:{user_id}", event)

    # =========================================================================
    # Job Progress Events
    # =========================================================================

    async def send_job_started(
        self,
        job_id: UUID,
        user_id: UUID,
        job_type: str,
        message: Optional[str] = None,
    ) -> int:
        """Send job started event."""
        event = JobProgressEvent.create(
            job_id=job_id,
            job_type=job_type,
            progress=0,
            status="started",
            message=message or f"Job {job_type} started",
        )

        # Send to job-specific room
        await self._publish_to_room(f"job:{job_id}", event)
        # Also send to user's jobs room
        return await self._publish_to_room(f"jobs:{user_id}", event)

    async def send_job_progress(
        self,
        job_id: UUID,
        user_id: UUID,
        job_type: str,
        progress: float,
        message: Optional[str] = None,
    ) -> int:
        """Send job progress update."""
        event = JobProgressEvent.create(
            job_id=job_id,
            job_type=job_type,
            progress=progress,
            status="processing",
            message=message,
        )

        await self._publish_to_room(f"job:{job_id}", event)
        return await self._publish_to_room(f"jobs:{user_id}", event)

    async def send_job_completed(
        self,
        job_id: UUID,
        user_id: UUID,
        job_type: str,
        result: Optional[dict] = None,
        message: Optional[str] = None,
    ) -> int:
        """Send job completed event."""
        event = JobProgressEvent.create(
            job_id=job_id,
            job_type=job_type,
            progress=100,
            status="completed",
            message=message or "Job completed successfully",
            result=result,
        )

        await self._publish_to_room(f"job:{job_id}", event)
        return await self._publish_to_room(f"jobs:{user_id}", event)

    async def send_job_failed(
        self,
        job_id: UUID,
        user_id: UUID,
        job_type: str,
        error: str,
    ) -> int:
        """Send job failed event."""
        event = JobProgressEvent.create(
            job_id=job_id,
            job_type=job_type,
            progress=0,
            status="failed",
            error=error,
        )

        await self._publish_to_room(f"job:{job_id}", event)
        return await self._publish_to_room(f"jobs:{user_id}", event)

    # =========================================================================
    # Direct Message Events
    # =========================================================================

    async def send_new_message(
        self,
        recipient_id: UUID,
        message_id: UUID,
        conversation_id: UUID,
        sender_id: UUID,
        sender_name: str,
        sender_avatar: Optional[str],
        content: str,
        message_type: str = "text",
        media_url: Optional[str] = None,
    ) -> int:
        """Send new message notification."""
        event = MessageEvent.new_message(
            message_id=message_id,
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_avatar=sender_avatar,
            content=content,
            message_type=message_type,
            media_url=media_url,
        )

        # Send to recipient's messages room
        await self._publish_to_room(f"messages:{recipient_id}", event)
        # Also send to conversation room
        return await self._publish_to_room(f"conversation:{conversation_id}", event)

    async def send_typing_indicator(
        self,
        conversation_id: UUID,
        user_id: UUID,
        user_name: str,
        is_typing: bool = True,
    ) -> int:
        """Send typing indicator."""
        event = MessageEvent.typing(
            conversation_id=conversation_id,
            user_id=user_id,
            user_name=user_name,
            is_typing=is_typing,
        )
        return await self._publish_to_room(f"conversation:{conversation_id}", event)

    # =========================================================================
    # Feed Events
    # =========================================================================

    async def send_new_post_to_followers(
        self,
        follower_ids: list[UUID],
        post_id: UUID,
        user_id: UUID,
        username: str,
        preview: str,
        media_type: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> int:
        """Send new post notification to all followers."""
        event = FeedUpdateEvent.new_post(
            post_id=post_id,
            user_id=user_id,
            username=username,
            preview=preview,
            media_type=media_type,
            thumbnail_url=thumbnail_url,
        )

        sent = 0
        for follower_id in follower_ids:
            sent += await self._publish_to_room(f"feed:{follower_id}", event)

        return sent

    async def send_post_liked(
        self,
        post_owner_id: UUID,
        post_id: UUID,
        liker_id: UUID,
        liker_name: str,
        like_count: int,
    ) -> int:
        """Send post liked notification."""
        event = FeedUpdateEvent.post_liked(
            post_id=post_id,
            liker_id=liker_id,
            liker_name=liker_name,
            like_count=like_count,
        )
        return await self._publish_to_room(f"feed:{post_owner_id}", event)

    async def send_post_commented(
        self,
        post_owner_id: UUID,
        post_id: UUID,
        commenter_id: UUID,
        commenter_name: str,
        comment_preview: str,
    ) -> int:
        """Send post commented notification."""
        event = WebSocketEvent(
            type=EventType.FEED_POST_COMMENTED,
            data={
                "post_id": str(post_id),
                "commenter": {
                    "id": str(commenter_id),
                    "name": commenter_name,
                },
                "comment_preview": comment_preview[:100],
            },
        )
        return await self._publish_to_room(f"feed:{post_owner_id}", event)

    # =========================================================================
    # Live Stream Events
    # =========================================================================

    async def send_live_started(
        self,
        follower_ids: list[UUID],
        session_id: UUID,
        host_id: UUID,
        host_name: str,
        title: str,
        playback_url: str,
    ) -> int:
        """Notify followers that a live stream started."""
        event = LiveStreamEvent.started(
            session_id=session_id,
            host_id=host_id,
            host_name=host_name,
            title=title,
            playback_url=playback_url,
        )

        sent = 0
        for follower_id in follower_ids:
            sent += await self._publish_to_user(follower_id, event)

        return sent

    async def send_live_ended(
        self,
        session_id: UUID,
        final_viewer_count: int,
        duration_seconds: int,
    ) -> int:
        """Send live stream ended event."""
        event = WebSocketEvent(
            type=EventType.LIVE_ENDED,
            data={
                "session_id": str(session_id),
                "final_viewer_count": final_viewer_count,
                "duration_seconds": duration_seconds,
            },
        )
        return await self._publish_to_room(f"live:{session_id}", event)

    async def send_live_stats(
        self,
        session_id: UUID,
        viewer_count: int,
        like_count: int,
        comment_count: int,
        duration_seconds: int,
    ) -> int:
        """Send live stream stats update."""
        event = LiveStreamEvent.stats(
            session_id=session_id,
            viewer_count=viewer_count,
            like_count=like_count,
            comment_count=comment_count,
            duration_seconds=duration_seconds,
        )
        return await self._publish_to_room(f"live:{session_id}", event)

    # =========================================================================
    # Content Generation Events
    # =========================================================================

    async def send_content_progress(
        self,
        user_id: UUID,
        content_id: UUID,
        content_type: str,
        stage: str,
        progress: float,
        message: Optional[str] = None,
    ) -> int:
        """Send content generation progress."""
        event = ContentGenerationEvent.progress(
            content_id=content_id,
            content_type=content_type,
            stage=stage,
            progress=progress,
            message=message,
        )
        return await self._publish_to_user(user_id, event)

    async def send_content_completed(
        self,
        user_id: UUID,
        content_id: UUID,
        content_type: str,
        preview_url: Optional[str] = None,
    ) -> int:
        """Send content generation completed."""
        event = ContentGenerationEvent.completed(
            content_id=content_id,
            content_type=content_type,
            preview_url=preview_url,
        )
        return await self._publish_to_user(user_id, event)

    # =========================================================================
    # AI Twin Events
    # =========================================================================

    async def send_twin_training_progress(
        self,
        user_id: UUID,
        twin_id: UUID,
        job_type: str,
        stage: str,
        progress: float,
        message: Optional[str] = None,
    ) -> int:
        """Send AI twin training progress."""
        event = TwinEvent.training_progress(
            twin_id=twin_id,
            job_type=job_type,
            stage=stage,
            progress=progress,
            message=message,
        )
        return await self._publish_to_user(user_id, event)

    async def send_twin_video_ready(
        self,
        user_id: UUID,
        twin_id: UUID,
        video_id: UUID,
        video_url: str,
        thumbnail_url: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> int:
        """Send AI twin video ready notification."""
        event = TwinEvent.video_ready(
            twin_id=twin_id,
            video_id=video_id,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration_seconds=duration_seconds,
        )
        return await self._publish_to_user(user_id, event)

    # =========================================================================
    # Social Publishing Events
    # =========================================================================

    async def send_social_post_published(
        self,
        user_id: UUID,
        content_id: UUID,
        platform: str,
        platform_post_id: str,
        post_url: str,
    ) -> int:
        """Send social post published notification."""
        event = WebSocketEvent(
            type=EventType.SOCIAL_POST_PUBLISHED,
            data={
                "content_id": str(content_id),
                "platform": platform,
                "platform_post_id": platform_post_id,
                "post_url": post_url,
            },
        )
        return await self._publish_to_user(user_id, event)

    async def send_social_post_failed(
        self,
        user_id: UUID,
        content_id: UUID,
        platform: str,
        error: str,
    ) -> int:
        """Send social post failed notification."""
        event = WebSocketEvent(
            type=EventType.SOCIAL_POST_FAILED,
            data={
                "content_id": str(content_id),
                "platform": platform,
                "error": error,
            },
        )
        return await self._publish_to_user(user_id, event)

    # =========================================================================
    # Follow Events
    # =========================================================================

    async def send_new_follower(
        self,
        user_id: UUID,
        follower_id: UUID,
        follower_name: str,
        follower_avatar: Optional[str] = None,
    ) -> int:
        """Send new follower notification."""
        event = WebSocketEvent(
            type=EventType.FOLLOW_NEW,
            data={
                "follower": {
                    "id": str(follower_id),
                    "name": follower_name,
                    "avatar": follower_avatar,
                },
            },
        )
        return await self._publish_to_user(user_id, event)


# Global publisher instance
ws_publisher = WebSocketPublisher()
