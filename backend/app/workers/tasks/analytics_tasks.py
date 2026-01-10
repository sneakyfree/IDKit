"""
Analytics Tasks

Background tasks for analytics processing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def sync_social_analytics() -> dict:
    """
    Sync analytics from all connected social platforms.

    This runs every 5 minutes via Celery Beat.
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Syncing social analytics")

    async def _sync():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.social import SocialAccount

            # Get all connected accounts
            result = await db.execute(
                select(SocialAccount).where(SocialAccount.is_active == True)
            )
            accounts = result.scalars().all()

            synced = 0
            errors = 0

            for account in accounts:
                try:
                    # Get appropriate adapter
                    from app.adapters import get_adapter

                    adapter = get_adapter(account.platform)
                    if adapter:
                        # Fetch latest analytics
                        analytics = await adapter.get_analytics(
                            account.access_token,
                            days=1,
                        )

                        # Store analytics
                        from app.services.analytics.unified_analytics import (
                            UnifiedAnalyticsService,
                        )

                        analytics_service = UnifiedAnalyticsService(db)
                        await analytics_service.store_platform_analytics(
                            account_id=account.id,
                            platform=account.platform,
                            analytics_data=analytics,
                        )
                        synced += 1

                except Exception as e:
                    logger.error(
                        f"Failed to sync analytics for account {account.id}: {e}"
                    )
                    errors += 1

            return {"accounts": len(accounts), "synced": synced, "errors": errors}

    return asyncio.get_event_loop().run_until_complete(_sync())


@celery_app.task
def generate_daily_report() -> dict:
    """
    Generate daily analytics reports for all users.

    This runs daily at 1 AM UTC via Celery Beat.
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Generating daily analytics reports")

    async def _generate():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            # Get all active users
            result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()

            generated = 0
            yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

            for user in users:
                try:
                    from app.services.analytics.unified_analytics import (
                        UnifiedAnalyticsService,
                    )

                    analytics_service = UnifiedAnalyticsService(db)

                    # Generate daily summary
                    summary = await analytics_service.generate_daily_summary(
                        user_id=user.id,
                        date=yesterday,
                    )

                    # Store the report
                    await analytics_service.store_daily_report(
                        user_id=user.id,
                        date=yesterday,
                        report=summary,
                    )
                    generated += 1

                except Exception as e:
                    logger.error(f"Failed to generate report for user {user.id}: {e}")

            return {"users": len(users), "generated": generated}

    return asyncio.get_event_loop().run_until_complete(_generate())


@celery_app.task
def calculate_engagement_metrics(
    user_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """
    Calculate engagement metrics for a user.

    Args:
        user_id: User ID
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        Calculated metrics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Calculating engagement metrics for user {user_id}")

    async def _calculate():
        async with get_async_db() as db:
            from app.services.analytics.unified_analytics import UnifiedAnalyticsService

            service = UnifiedAnalyticsService(db)

            # Parse dates
            start_date = None
            end_date = None

            if date_from:
                start_date = datetime.fromisoformat(date_from)
            if date_to:
                end_date = datetime.fromisoformat(date_to)

            metrics = await service.calculate_engagement_metrics(
                user_id=UUID(user_id),
                date_from=start_date,
                date_to=end_date,
            )

            return metrics

    return asyncio.get_event_loop().run_until_complete(_calculate())


@celery_app.task
def calculate_best_posting_times(user_id: str) -> dict:
    """
    Analyze past performance to find best posting times.

    Args:
        user_id: User ID

    Returns:
        Best posting times by day and platform
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Calculating best posting times for user {user_id}")

    async def _calculate():
        async with get_async_db() as db:
            from app.services.analytics.unified_analytics import UnifiedAnalyticsService

            service = UnifiedAnalyticsService(db)

            results = await service.calculate_best_posting_times(
                user_id=UUID(user_id),
                days_to_analyze=90,
            )

            return results

    return asyncio.get_event_loop().run_until_complete(_calculate())


@celery_app.task
def update_viral_scores() -> dict:
    """
    Update viral prediction scores for recent content.

    This runs periodically to recalculate scores.
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Updating viral scores")

    async def _update():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.content import ContentItem
            from app.services.analytics.viral_predictor import ViralPredictor

            # Get recent content (last 7 days)
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)

            result = await db.execute(
                select(ContentItem).where(
                    ContentItem.created_at >= cutoff
                )
            )
            content_items = result.scalars().all()

            predictor = ViralPredictor(db)
            updated = 0

            for item in content_items:
                try:
                    score = await predictor.calculate_score(item)
                    item.viral_score = score
                    updated += 1
                except Exception as e:
                    logger.error(f"Failed to update viral score for {item.id}: {e}")

            await db.commit()

            return {"total": len(content_items), "updated": updated}

    return asyncio.get_event_loop().run_until_complete(_update())
