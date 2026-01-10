"""
Publishing Tasks

Background tasks for social media publishing.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from celery import shared_task

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 120},
    rate_limit="10/m",
)
def publish_to_platform(
    self,
    user_id: str,
    content_id: str,
    platform: str,
    account_id: str,
    post_content: dict,
    scheduled_time: Optional[str] = None,
) -> dict:
    """
    Publish content to a social media platform.

    Args:
        user_id: User ID
        content_id: Content item ID
        platform: Platform name (youtube, instagram, tiktok, etc.)
        account_id: Connected social account ID
        post_content: Platform-specific post content
        scheduled_time: Optional scheduled time (ISO format)

    Returns:
        Platform post details
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Publishing to {platform} for user {user_id}")

    async def _publish():
        async with get_async_db() as db:
            from app.services.social.publishing_service import PublishingService

            service = PublishingService(db)

            result = await service.publish(
                user_id=UUID(user_id),
                content_id=UUID(content_id),
                platform=platform,
                account_id=UUID(account_id),
                post_content=post_content,
            )

            # Send WebSocket notification
            from app.websocket import ws_publisher

            if result.get("success"):
                await ws_publisher.send_social_post_published(
                    user_id=UUID(user_id),
                    content_id=UUID(content_id),
                    platform=platform,
                    platform_post_id=result.get("platform_post_id", ""),
                    post_url=result.get("post_url", ""),
                )
            else:
                await ws_publisher.send_social_post_failed(
                    user_id=UUID(user_id),
                    content_id=UUID(content_id),
                    platform=platform,
                    error=result.get("error", "Unknown error"),
                )

            return result

    return asyncio.get_event_loop().run_until_complete(_publish())


@celery_app.task
def check_scheduled_posts() -> dict:
    """
    Check for scheduled posts that need to be published.

    This runs every minute via Celery Beat.
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Checking for scheduled posts")

    async def _check_scheduled():
        async with get_async_db() as db:
            from sqlalchemy import select, and_
            from app.models.social import ScheduledPost

            now = datetime.now(timezone.utc)

            # Find posts scheduled for now or earlier
            result = await db.execute(
                select(ScheduledPost).where(
                    and_(
                        ScheduledPost.scheduled_time <= now,
                        ScheduledPost.status == "pending",
                    )
                ).limit(50)
            )
            posts = result.scalars().all()

            published = 0
            for post in posts:
                # Mark as processing
                post.status = "processing"
                await db.commit()

                # Queue for publishing
                publish_to_platform.delay(
                    user_id=str(post.user_id),
                    content_id=str(post.content_id),
                    platform=post.platform,
                    account_id=str(post.account_id),
                    post_content=post.post_content,
                )
                published += 1

            return {"checked": len(posts), "published": published}

    return asyncio.get_event_loop().run_until_complete(_check_scheduled())


@celery_app.task(
    bind=True,
    soft_time_limit=1800,  # 30 minutes for batch
)
def publish_batch(
    self,
    user_id: str,
    content_id: str,
    platforms: list[dict],
) -> dict:
    """
    Publish content to multiple platforms.

    Args:
        user_id: User ID
        content_id: Content item ID
        platforms: List of {platform, account_id, post_content}

    Returns:
        Results for each platform
    """
    import asyncio
    from celery import group

    logger.info(f"Batch publishing to {len(platforms)} platforms for user {user_id}")

    # Create a group of tasks
    tasks = []
    for p in platforms:
        task = publish_to_platform.s(
            user_id=user_id,
            content_id=content_id,
            platform=p["platform"],
            account_id=p["account_id"],
            post_content=p["post_content"],
        )
        tasks.append(task)

    # Execute in parallel
    job = group(tasks)
    result = job.apply_async()

    # Wait for completion
    results = result.get(timeout=1800)

    return {
        "total": len(platforms),
        "results": results,
    }
