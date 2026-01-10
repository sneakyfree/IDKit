"""
Notification Service

Handles creation, delivery, and management of notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType, NotificationSettings
from app.models.feed import UserProfile, FeedPost
from app.utils.redis import redis_client


class NotificationService:
    """
    Service for managing user notifications.

    Handles creation, batching, and real-time delivery.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        body: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        post_id: Optional[uuid.UUID] = None,
        comment_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """
        Create a new notification.

        Also publishes to Redis for real-time delivery.
        """
        # Don't notify users about their own actions
        if actor_id and user_id == actor_id:
            return None

        # Check user notification settings
        settings = await self._get_settings(user_id)
        if settings and not self._should_notify(settings, notification_type):
            return None

        notification = Notification(
            user_id=user_id,
            notification_type=notification_type.value,
            title=title,
            body=body,
            actor_id=actor_id,
            post_id=post_id,
            comment_id=comment_id,
            metadata=metadata or {},
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        # Publish for real-time delivery
        await self._publish_notification(notification)

        # Update unread count in cache
        await self._increment_unread_count(user_id)

        return notification

    async def create_like_notification(
        self,
        post_owner_id: uuid.UUID,
        liker_id: uuid.UUID,
        post_id: uuid.UUID,
    ) -> Optional[Notification]:
        """Create notification when someone likes a post."""
        # Get liker profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == liker_id)
        )
        liker = result.scalar_one_or_none()
        if not liker:
            return None

        return await self.create_notification(
            user_id=post_owner_id,
            notification_type=NotificationType.LIKE,
            title=f"@{liker.username} liked your post",
            actor_id=liker_id,
            post_id=post_id,
            metadata={"liker_avatar": liker.avatar_url},
        )

    async def create_comment_notification(
        self,
        post_owner_id: uuid.UUID,
        commenter_id: uuid.UUID,
        post_id: uuid.UUID,
        comment_id: uuid.UUID,
        comment_preview: str,
    ) -> Optional[Notification]:
        """Create notification when someone comments on a post."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == commenter_id)
        )
        commenter = result.scalar_one_or_none()
        if not commenter:
            return None

        # Truncate comment preview
        preview = comment_preview[:100] + "..." if len(comment_preview) > 100 else comment_preview

        return await self.create_notification(
            user_id=post_owner_id,
            notification_type=NotificationType.COMMENT,
            title=f"@{commenter.username} commented on your post",
            body=preview,
            actor_id=commenter_id,
            post_id=post_id,
            comment_id=comment_id,
            metadata={"commenter_avatar": commenter.avatar_url},
        )

    async def create_follow_notification(
        self,
        followed_id: uuid.UUID,
        follower_id: uuid.UUID,
    ) -> Optional[Notification]:
        """Create notification when someone follows a user."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == follower_id)
        )
        follower = result.scalar_one_or_none()
        if not follower:
            return None

        return await self.create_notification(
            user_id=followed_id,
            notification_type=NotificationType.FOLLOW,
            title=f"@{follower.username} started following you",
            actor_id=follower_id,
            metadata={
                "follower_avatar": follower.avatar_url,
                "follower_bio": follower.bio[:100] if follower.bio else None,
            },
        )

    async def create_mention_notification(
        self,
        mentioned_user_id: uuid.UUID,
        mentioner_id: uuid.UUID,
        post_id: uuid.UUID,
        context: str,
    ) -> Optional[Notification]:
        """Create notification when someone mentions a user."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == mentioner_id)
        )
        mentioner = result.scalar_one_or_none()
        if not mentioner:
            return None

        return await self.create_notification(
            user_id=mentioned_user_id,
            notification_type=NotificationType.MENTION,
            title=f"@{mentioner.username} mentioned you",
            body=context[:100] + "..." if len(context) > 100 else context,
            actor_id=mentioner_id,
            post_id=post_id,
            metadata={"mentioner_avatar": mentioner.avatar_url},
        )

    async def create_ai_complete_notification(
        self,
        user_id: uuid.UUID,
        job_type: str,
        job_id: str,
        result_url: Optional[str] = None,
    ) -> Optional[Notification]:
        """Create notification when an AI job completes."""
        job_names = {
            "video": "AI Video",
            "podcast": "Podcast Episode",
            "avatar": "Avatar Training",
            "voice": "Voice Cloning",
            "content": "Content Generation",
        }

        job_name = job_names.get(job_type, "AI Job")

        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.AI_COMPLETE,
            title=f"Your {job_name} is ready!",
            body="Tap to view your generated content",
            metadata={
                "job_type": job_type,
                "job_id": job_id,
                "result_url": result_url,
            },
        )

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        query = (
            query.order_by(desc(Notification.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_as_read(
        self,
        user_id: uuid.UUID,
        notification_ids: Optional[List[uuid.UUID]] = None,
    ) -> int:
        """
        Mark notifications as read.

        If notification_ids is None, marks all as read.
        Returns the number of notifications marked as read.
        """
        query = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )

        if notification_ids:
            query = query.where(Notification.id.in_(notification_ids))

        result = await self.db.execute(query)
        await self.db.commit()

        # Clear unread count cache
        await self._clear_unread_count(user_id)

        return result.rowcount

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get unread notification count for a user."""
        # Try cache first
        cache_key = f"notif:unread:{user_id}"
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return int(cached)

        # Query database
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        count = result.scalar() or 0

        # Cache for 5 minutes
        await redis_client.setex(cache_key, 300, str(count))

        return count

    async def delete_notification(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> bool:
        """Delete a specific notification."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()

        return True

    async def _get_settings(self, user_id: uuid.UUID) -> Optional[NotificationSettings]:
        """Get user notification settings."""
        result = await self.db.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _should_notify(
        self,
        settings: NotificationSettings,
        notification_type: NotificationType,
    ) -> bool:
        """Check if user wants this type of notification."""
        if not settings.push_enabled:
            return False

        type_map = {
            NotificationType.LIKE: settings.push_likes,
            NotificationType.COMMENT: settings.push_comments,
            NotificationType.FOLLOW: settings.push_follows,
            NotificationType.MENTION: settings.push_mentions,
            NotificationType.REPLY: settings.push_comments,
            NotificationType.AI_COMPLETE: settings.push_ai_complete,
        }

        return type_map.get(notification_type, True)

    async def _publish_notification(self, notification: Notification):
        """Publish notification for real-time delivery via WebSocket."""
        channel = f"notifications:{notification.user_id}"
        message = {
            "id": str(notification.id),
            "type": notification.notification_type,
            "title": notification.title,
            "body": notification.body,
            "created_at": notification.created_at.isoformat(),
            "metadata": notification.metadata,
        }

        await redis_client.publish(channel, str(message))

    async def _increment_unread_count(self, user_id: uuid.UUID):
        """Increment cached unread count."""
        cache_key = f"notif:unread:{user_id}"
        await redis_client.incr(cache_key)

    async def _clear_unread_count(self, user_id: uuid.UUID):
        """Clear cached unread count."""
        cache_key = f"notif:unread:{user_id}"
        await redis_client.delete(cache_key)
