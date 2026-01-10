"""
WebSocket Event Types

Defines all event types and schemas for real-time communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """WebSocket event types."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

    # Notification events
    NOTIFICATION = "notification"
    NOTIFICATION_READ = "notification_read"
    NOTIFICATION_COUNT = "notification_count"

    # Job/task progress events
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"

    # Direct message events
    MESSAGE_NEW = "message_new"
    MESSAGE_READ = "message_read"
    MESSAGE_TYPING = "message_typing"
    MESSAGE_DELIVERED = "message_delivered"

    # Feed events
    FEED_NEW_POST = "feed_new_post"
    FEED_POST_LIKED = "feed_post_liked"
    FEED_POST_COMMENTED = "feed_post_commented"
    FEED_POST_SHARED = "feed_post_shared"

    # Follow events
    FOLLOW_NEW = "follow_new"
    FOLLOW_REMOVED = "follow_removed"

    # Live stream events
    LIVE_STARTED = "live_started"
    LIVE_ENDED = "live_ended"
    LIVE_VIEWER_JOINED = "live_viewer_joined"
    LIVE_VIEWER_LEFT = "live_viewer_left"
    LIVE_COMMENT = "live_comment"
    LIVE_REACTION = "live_reaction"
    LIVE_STATS = "live_stats"

    # Content generation events
    CONTENT_GENERATING = "content_generating"
    CONTENT_GENERATED = "content_generated"
    CONTENT_PUBLISHED = "content_published"

    # AI Twin events
    TWIN_TRAINING_PROGRESS = "twin_training_progress"
    TWIN_VIDEO_GENERATING = "twin_video_generating"
    TWIN_VIDEO_READY = "twin_video_ready"

    # Podcast events
    PODCAST_GENERATING = "podcast_generating"
    PODCAST_READY = "podcast_ready"
    PODCAST_CLIP_READY = "podcast_clip_ready"

    # Social sync events
    SOCIAL_POST_PUBLISHED = "social_post_published"
    SOCIAL_POST_FAILED = "social_post_failed"
    SOCIAL_ANALYTICS_UPDATED = "social_analytics_updated"


class WebSocketEvent(BaseModel):
    """Base WebSocket event model."""

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class NotificationEvent(WebSocketEvent):
    """Notification event with specific data structure."""

    type: EventType = EventType.NOTIFICATION
    data: dict = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        notification_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        actor_name: Optional[str] = None,
        actor_avatar: Optional[str] = None,
    ) -> "NotificationEvent":
        """Create a notification event."""
        return cls(
            data={
                "notification_id": str(notification_id),
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "action_url": action_url,
                "actor": {
                    "id": str(actor_id) if actor_id else None,
                    "name": actor_name,
                    "avatar": actor_avatar,
                } if actor_id else None,
            }
        )


class JobProgressEvent(WebSocketEvent):
    """Job/task progress event."""

    type: EventType = EventType.JOB_PROGRESS
    data: dict = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        job_id: UUID,
        job_type: str,
        progress: float,
        status: str,
        message: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> "JobProgressEvent":
        """Create a job progress event."""
        event_type = EventType.JOB_PROGRESS
        if progress >= 100 and status == "completed":
            event_type = EventType.JOB_COMPLETED
        elif status == "failed":
            event_type = EventType.JOB_FAILED
        elif progress == 0 and status == "started":
            event_type = EventType.JOB_STARTED

        return cls(
            type=event_type,
            data={
                "job_id": str(job_id),
                "job_type": job_type,
                "progress": progress,
                "status": status,
                "message": message,
                "result": result,
                "error": error,
            }
        )


class MessageEvent(WebSocketEvent):
    """Direct message event."""

    type: EventType = EventType.MESSAGE_NEW
    data: dict = Field(default_factory=dict)

    @classmethod
    def new_message(
        cls,
        message_id: UUID,
        conversation_id: UUID,
        sender_id: UUID,
        sender_name: str,
        sender_avatar: Optional[str],
        content: str,
        message_type: str = "text",
        media_url: Optional[str] = None,
    ) -> "MessageEvent":
        """Create a new message event."""
        return cls(
            type=EventType.MESSAGE_NEW,
            data={
                "message_id": str(message_id),
                "conversation_id": str(conversation_id),
                "sender": {
                    "id": str(sender_id),
                    "name": sender_name,
                    "avatar": sender_avatar,
                },
                "content": content,
                "message_type": message_type,
                "media_url": media_url,
            }
        )

    @classmethod
    def typing(
        cls,
        conversation_id: UUID,
        user_id: UUID,
        user_name: str,
        is_typing: bool = True,
    ) -> "MessageEvent":
        """Create a typing indicator event."""
        return cls(
            type=EventType.MESSAGE_TYPING,
            data={
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "user_name": user_name,
                "is_typing": is_typing,
            }
        )


class FeedUpdateEvent(WebSocketEvent):
    """Feed update event."""

    type: EventType = EventType.FEED_NEW_POST
    data: dict = Field(default_factory=dict)

    @classmethod
    def new_post(
        cls,
        post_id: UUID,
        user_id: UUID,
        username: str,
        preview: str,
        media_type: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> "FeedUpdateEvent":
        """Create a new post event."""
        return cls(
            type=EventType.FEED_NEW_POST,
            data={
                "post_id": str(post_id),
                "user": {
                    "id": str(user_id),
                    "username": username,
                },
                "preview": preview[:200] if preview else None,
                "media_type": media_type,
                "thumbnail_url": thumbnail_url,
            }
        )

    @classmethod
    def post_liked(
        cls,
        post_id: UUID,
        liker_id: UUID,
        liker_name: str,
        like_count: int,
    ) -> "FeedUpdateEvent":
        """Create a post liked event."""
        return cls(
            type=EventType.FEED_POST_LIKED,
            data={
                "post_id": str(post_id),
                "liker": {
                    "id": str(liker_id),
                    "name": liker_name,
                },
                "like_count": like_count,
            }
        )


class LiveStreamEvent(WebSocketEvent):
    """Live stream event."""

    type: EventType = EventType.LIVE_STARTED
    data: dict = Field(default_factory=dict)

    @classmethod
    def started(
        cls,
        session_id: UUID,
        host_id: UUID,
        host_name: str,
        title: str,
        playback_url: str,
    ) -> "LiveStreamEvent":
        """Create a live stream started event."""
        return cls(
            type=EventType.LIVE_STARTED,
            data={
                "session_id": str(session_id),
                "host": {
                    "id": str(host_id),
                    "name": host_name,
                },
                "title": title,
                "playback_url": playback_url,
            }
        )

    @classmethod
    def comment(
        cls,
        session_id: UUID,
        comment_id: UUID,
        user_id: UUID,
        user_name: str,
        content: str,
    ) -> "LiveStreamEvent":
        """Create a live stream comment event."""
        return cls(
            type=EventType.LIVE_COMMENT,
            data={
                "session_id": str(session_id),
                "comment_id": str(comment_id),
                "user": {
                    "id": str(user_id),
                    "name": user_name,
                },
                "content": content,
            }
        )

    @classmethod
    def stats(
        cls,
        session_id: UUID,
        viewer_count: int,
        like_count: int,
        comment_count: int,
        duration_seconds: int,
    ) -> "LiveStreamEvent":
        """Create a live stream stats update event."""
        return cls(
            type=EventType.LIVE_STATS,
            data={
                "session_id": str(session_id),
                "viewer_count": viewer_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "duration_seconds": duration_seconds,
            }
        )


class ContentGenerationEvent(WebSocketEvent):
    """Content generation progress event."""

    type: EventType = EventType.CONTENT_GENERATING
    data: dict = Field(default_factory=dict)

    @classmethod
    def progress(
        cls,
        content_id: UUID,
        content_type: str,
        stage: str,
        progress: float,
        message: Optional[str] = None,
    ) -> "ContentGenerationEvent":
        """Create a content generation progress event."""
        return cls(
            type=EventType.CONTENT_GENERATING,
            data={
                "content_id": str(content_id),
                "content_type": content_type,
                "stage": stage,
                "progress": progress,
                "message": message,
            }
        )

    @classmethod
    def completed(
        cls,
        content_id: UUID,
        content_type: str,
        preview_url: Optional[str] = None,
    ) -> "ContentGenerationEvent":
        """Create a content generation completed event."""
        return cls(
            type=EventType.CONTENT_GENERATED,
            data={
                "content_id": str(content_id),
                "content_type": content_type,
                "preview_url": preview_url,
            }
        )


class TwinEvent(WebSocketEvent):
    """AI Twin generation event."""

    type: EventType = EventType.TWIN_TRAINING_PROGRESS
    data: dict = Field(default_factory=dict)

    @classmethod
    def training_progress(
        cls,
        twin_id: UUID,
        job_type: str,
        stage: str,
        progress: float,
        message: Optional[str] = None,
    ) -> "TwinEvent":
        """Create a twin training progress event."""
        return cls(
            type=EventType.TWIN_TRAINING_PROGRESS,
            data={
                "twin_id": str(twin_id),
                "job_type": job_type,
                "stage": stage,
                "progress": progress,
                "message": message,
            }
        )

    @classmethod
    def video_ready(
        cls,
        twin_id: UUID,
        video_id: UUID,
        video_url: str,
        thumbnail_url: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> "TwinEvent":
        """Create a twin video ready event."""
        return cls(
            type=EventType.TWIN_VIDEO_READY,
            data={
                "twin_id": str(twin_id),
                "video_id": str(video_id),
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "duration_seconds": duration_seconds,
            }
        )
