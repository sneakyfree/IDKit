"""
Notification Tasks

Background tasks for sending notifications.
"""

import logging
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
)
def send_notification(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    actor_id: Optional[str] = None,
    data: Optional[dict] = None,
) -> dict:
    """
    Send a notification to a user.

    Args:
        user_id: Target user ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        action_url: Optional action URL
        actor_id: Optional actor (user who triggered the notification)
        data: Additional notification data

    Returns:
        Notification result
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Sending {notification_type} notification to {user_id}")

    async def _send_notification():
        async with get_async_db() as db:
            from app.services.notification import NotificationService
            import uuid

            service = NotificationService(db)

            # Create notification in database
            notification = await service.create(
                user_id=UUID(user_id),
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                actor_id=UUID(actor_id) if actor_id else None,
                data=data or {},
            )

            # Send via WebSocket
            from app.websocket import ws_publisher

            actor_name = None
            actor_avatar = None
            if actor_id:
                from sqlalchemy import select
                from app.models.user import User

                result = await db.execute(
                    select(User).where(User.id == UUID(actor_id))
                )
                actor = result.scalar_one_or_none()
                if actor:
                    actor_name = actor.full_name
                    actor_avatar = actor.avatar_url

            await ws_publisher.send_notification(
                user_id=UUID(user_id),
                notification_id=notification.id,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                actor_id=UUID(actor_id) if actor_id else None,
                actor_name=actor_name,
                actor_avatar=actor_avatar,
            )

            # Also send push notification if enabled
            from app.services.notifications.push_service import PushNotificationService

            push_service = PushNotificationService(db)
            await push_service.send_to_user(
                user_id=UUID(user_id),
                title=title,
                body=message,
                data={
                    "notification_id": str(notification.id),
                    "type": notification_type,
                    "action_url": action_url,
                },
            )

            return {
                "notification_id": str(notification.id),
                "delivered": True,
            }

    return asyncio.get_event_loop().run_until_complete(_send_notification())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def send_batch_notifications(
    self,
    user_ids: list[str],
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> dict:
    """
    Send notifications to multiple users.

    Args:
        user_ids: List of target user IDs
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        action_url: Optional action URL
        actor_id: Optional actor ID

    Returns:
        Batch results
    """
    from celery import group

    logger.info(f"Sending batch notifications to {len(user_ids)} users")

    tasks = []
    for user_id in user_ids:
        task = send_notification.s(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            actor_id=actor_id,
        )
        tasks.append(task)

    job = group(tasks)
    result = job.apply_async()
    results = result.get(timeout=300)

    sent = sum(1 for r in results if r.get("delivered"))

    return {
        "total": len(user_ids),
        "sent": sent,
        "failed": len(user_ids) - sent,
    }


@celery_app.task
def send_follow_notification(
    follower_id: str,
    following_id: str,
) -> dict:
    """Send notification when someone follows a user."""
    import asyncio
    from app.workers.utils import get_async_db

    async def _send():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            result = await db.execute(
                select(User).where(User.id == UUID(follower_id))
            )
            follower = result.scalar_one_or_none()

            if not follower:
                return {"error": "Follower not found"}

            # Send notification
            return await send_notification(
                user_id=following_id,
                notification_type="follow",
                title="New Follower",
                message=f"{follower.full_name or 'Someone'} started following you",
                action_url=f"/profile/{follower_id}",
                actor_id=follower_id,
            )

    return asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task
def send_like_notification(
    liker_id: str,
    post_owner_id: str,
    post_id: str,
) -> dict:
    """Send notification when someone likes a post."""
    import asyncio
    from app.workers.utils import get_async_db

    async def _send():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            result = await db.execute(
                select(User).where(User.id == UUID(liker_id))
            )
            liker = result.scalar_one_or_none()

            if not liker:
                return {"error": "Liker not found"}

            return await send_notification(
                user_id=post_owner_id,
                notification_type="like",
                title="New Like",
                message=f"{liker.full_name or 'Someone'} liked your post",
                action_url=f"/posts/{post_id}",
                actor_id=liker_id,
            )

    return asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task
def send_comment_notification(
    commenter_id: str,
    post_owner_id: str,
    post_id: str,
    comment_preview: str,
) -> dict:
    """Send notification when someone comments on a post."""
    import asyncio
    from app.workers.utils import get_async_db

    async def _send():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            result = await db.execute(
                select(User).where(User.id == UUID(commenter_id))
            )
            commenter = result.scalar_one_or_none()

            if not commenter:
                return {"error": "Commenter not found"}

            name = commenter.full_name or "Someone"
            preview = comment_preview[:50] + "..." if len(comment_preview) > 50 else comment_preview

            return await send_notification(
                user_id=post_owner_id,
                notification_type="comment",
                title="New Comment",
                message=f'{name} commented: "{preview}"',
                action_url=f"/posts/{post_id}",
                actor_id=commenter_id,
            )

    return asyncio.get_event_loop().run_until_complete(_send())
