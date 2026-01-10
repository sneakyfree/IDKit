"""
Maintenance Tasks

Background tasks for cleanup, maintenance, and system health.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    soft_time_limit=600,
)
def cleanup_expired_sessions(self) -> dict:
    """
    Clean up expired user sessions and tokens.

    Returns:
        Cleanup statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Running expired sessions cleanup")

    async def _cleanup():
        async with get_async_db() as db:
            from sqlalchemy import delete, text

            # Delete expired refresh tokens (older than 7 days)
            expiry_date = datetime.utcnow() - timedelta(days=7)

            # Clean up refresh tokens table if exists
            try:
                result = await db.execute(
                    text("""
                        DELETE FROM refresh_tokens
                        WHERE created_at < :expiry_date
                    """),
                    {"expiry_date": expiry_date},
                )
                deleted_tokens = result.rowcount
            except Exception:
                deleted_tokens = 0

            # Clean up WebSocket session records if tracked in DB
            try:
                result = await db.execute(
                    text("""
                        DELETE FROM websocket_sessions
                        WHERE last_active < :expiry_date
                    """),
                    {"expiry_date": datetime.utcnow() - timedelta(hours=24)},
                )
                deleted_ws_sessions = result.rowcount
            except Exception:
                deleted_ws_sessions = 0

            await db.commit()

            return {
                "deleted_tokens": deleted_tokens,
                "deleted_websocket_sessions": deleted_ws_sessions,
                "cleanup_time": datetime.utcnow().isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(
    bind=True,
    soft_time_limit=600,
)
def cleanup_old_jobs(self, days_old: int = 30) -> dict:
    """
    Clean up old completed/failed jobs.

    Args:
        days_old: Delete jobs older than this many days

    Returns:
        Cleanup statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Cleaning up jobs older than {days_old} days")

    async def _cleanup():
        async with get_async_db() as db:
            from sqlalchemy import text

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Clean up GPU jobs
            try:
                result = await db.execute(
                    text("""
                        DELETE FROM gpu_jobs
                        WHERE status IN ('completed', 'failed', 'cancelled')
                        AND updated_at < :cutoff_date
                    """),
                    {"cutoff_date": cutoff_date},
                )
                deleted_gpu_jobs = result.rowcount
            except Exception:
                deleted_gpu_jobs = 0

            # Clean up content generation jobs
            try:
                result = await db.execute(
                    text("""
                        DELETE FROM generation_jobs
                        WHERE status IN ('completed', 'failed')
                        AND created_at < :cutoff_date
                    """),
                    {"cutoff_date": cutoff_date},
                )
                deleted_gen_jobs = result.rowcount
            except Exception:
                deleted_gen_jobs = 0

            # Clean up publishing jobs
            try:
                result = await db.execute(
                    text("""
                        DELETE FROM publishing_jobs
                        WHERE status IN ('published', 'failed')
                        AND created_at < :cutoff_date
                    """),
                    {"cutoff_date": cutoff_date},
                )
                deleted_pub_jobs = result.rowcount
            except Exception:
                deleted_pub_jobs = 0

            await db.commit()

            return {
                "deleted_gpu_jobs": deleted_gpu_jobs,
                "deleted_generation_jobs": deleted_gen_jobs,
                "deleted_publishing_jobs": deleted_pub_jobs,
                "cutoff_date": cutoff_date.isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(
    bind=True,
    soft_time_limit=1800,  # 30 minutes
)
def cleanup_orphaned_media(self) -> dict:
    """
    Clean up orphaned media files not referenced by any content.

    Returns:
        Cleanup statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Running orphaned media cleanup")

    async def _cleanup():
        async with get_async_db() as db:
            from sqlalchemy import text
            from app.services.storage import storage_service

            # Find orphaned media uploads (not referenced anywhere)
            result = await db.execute(
                text("""
                    SELECT m.id, m.storage_key, m.file_size
                    FROM media_uploads m
                    LEFT JOIN ai_twins t ON m.id = ANY(t.media_ids)
                    LEFT JOIN feed_posts p ON m.storage_key = ANY(p.media_urls::text[])
                    LEFT JOIN podcast_episodes e ON m.storage_key IN (e.audio_url, e.video_url, e.thumbnail_url)
                    WHERE t.id IS NULL
                    AND p.id IS NULL
                    AND e.id IS NULL
                    AND m.created_at < :cutoff_date
                """),
                {"cutoff_date": datetime.utcnow() - timedelta(days=7)},
            )

            orphaned = result.fetchall()
            deleted_count = 0
            freed_bytes = 0
            errors = []

            for media in orphaned:
                try:
                    # Delete from storage
                    await storage_service.delete(media.storage_key)

                    # Delete from database
                    await db.execute(
                        text("DELETE FROM media_uploads WHERE id = :id"),
                        {"id": media.id},
                    )

                    deleted_count += 1
                    freed_bytes += media.file_size or 0

                except Exception as e:
                    errors.append({"id": str(media.id), "error": str(e)})

            await db.commit()

            return {
                "orphaned_found": len(orphaned),
                "deleted_count": deleted_count,
                "freed_bytes": freed_bytes,
                "freed_mb": round(freed_bytes / (1024 * 1024), 2),
                "errors": errors[:10],  # Limit error list
            }

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def cleanup_old_notifications(self, days_old: int = 90) -> dict:
    """
    Clean up old read notifications.

    Args:
        days_old: Delete notifications older than this many days

    Returns:
        Cleanup statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Cleaning up notifications older than {days_old} days")

    async def _cleanup():
        async with get_async_db() as db:
            from sqlalchemy import text

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Delete old read notifications
            result = await db.execute(
                text("""
                    DELETE FROM notifications
                    WHERE is_read = true
                    AND created_at < :cutoff_date
                """),
                {"cutoff_date": cutoff_date},
            )

            deleted_count = result.rowcount
            await db.commit()

            return {
                "deleted_notifications": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(
    bind=True,
    soft_time_limit=600,
)
def vacuum_database(self) -> dict:
    """
    Run database vacuum and analyze for performance.

    Returns:
        Vacuum result
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Running database vacuum")

    async def _vacuum():
        async with get_async_db() as db:
            from sqlalchemy import text

            # Get table sizes before
            size_before = await db.execute(
                text("""
                    SELECT pg_database_size(current_database()) as size
                """)
            )
            before = size_before.fetchone().size

            # Run analyze on key tables
            tables = [
                "users",
                "feed_posts",
                "feed_likes",
                "feed_comments",
                "follows",
                "notifications",
                "content_items",
                "ai_twins",
            ]

            for table in tables:
                try:
                    await db.execute(text(f"ANALYZE {table}"))
                except Exception:
                    pass  # Table might not exist

            # Get table sizes after
            size_after = await db.execute(
                text("""
                    SELECT pg_database_size(current_database()) as size
                """)
            )
            after = size_after.fetchone().size

            return {
                "size_before_mb": round(before / (1024 * 1024), 2),
                "size_after_mb": round(after / (1024 * 1024), 2),
                "tables_analyzed": tables,
                "vacuum_time": datetime.utcnow().isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_vacuum())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def cleanup_rate_limit_data(self) -> dict:
    """
    Clean up old rate limit tracking data from Redis.

    Returns:
        Cleanup statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Cleaning up rate limit data")

    async def _cleanup():
        from app.core.redis import get_redis

        redis = await get_redis()
        if not redis:
            return {"status": "skipped", "reason": "Redis not available"}

        # Find and delete old rate limit keys
        deleted_count = 0

        # Pattern for rate limit keys
        patterns = [
            "rate_limit:*",
            "api_rate:*",
            "request_count:*",
        ]

        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    ttl = await redis.ttl(key)
                    # Delete keys with no TTL or very old keys
                    if ttl == -1:  # No expiration set
                        await redis.delete(key)
                        deleted_count += 1

                if cursor == 0:
                    break

        return {
            "deleted_keys": deleted_count,
            "cleanup_time": datetime.utcnow().isoformat(),
        }

    return asyncio.get_event_loop().run_until_complete(_cleanup())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def update_user_stats(self) -> dict:
    """
    Update cached user statistics (follower counts, post counts, etc.).

    Returns:
        Update statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Updating user statistics")

    async def _update():
        async with get_async_db() as db:
            from sqlalchemy import text

            # Update follower counts
            await db.execute(
                text("""
                    UPDATE user_profiles up
                    SET follower_count = (
                        SELECT COUNT(*) FROM follows f
                        WHERE f.following_id = up.user_id
                    )
                """)
            )

            # Update following counts
            await db.execute(
                text("""
                    UPDATE user_profiles up
                    SET following_count = (
                        SELECT COUNT(*) FROM follows f
                        WHERE f.follower_id = up.user_id
                    )
                """)
            )

            # Update post counts
            await db.execute(
                text("""
                    UPDATE user_profiles up
                    SET post_count = (
                        SELECT COUNT(*) FROM feed_posts fp
                        WHERE fp.user_id = up.user_id
                        AND fp.visibility = 'public'
                    )
                """)
            )

            await db.commit()

            # Get update summary
            result = await db.execute(
                text("SELECT COUNT(*) as count FROM user_profiles")
            )
            profile_count = result.fetchone().count

            return {
                "profiles_updated": profile_count,
                "update_time": datetime.utcnow().isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_update())


@celery_app.task(
    bind=True,
    soft_time_limit=600,
)
def generate_system_health_report(self) -> dict:
    """
    Generate a system health report.

    Returns:
        Health report data
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Generating system health report")

    async def _report():
        async with get_async_db() as db:
            from sqlalchemy import text
            from app.core.redis import get_redis

            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "database": {},
                "redis": {},
                "users": {},
                "content": {},
                "jobs": {},
            }

            # Database stats
            try:
                result = await db.execute(
                    text("SELECT pg_database_size(current_database()) as size")
                )
                report["database"]["size_mb"] = round(
                    result.fetchone().size / (1024 * 1024), 2
                )

                result = await db.execute(
                    text("""
                        SELECT schemaname, relname, n_live_tup
                        FROM pg_stat_user_tables
                        ORDER BY n_live_tup DESC
                        LIMIT 10
                    """)
                )
                report["database"]["largest_tables"] = [
                    {"table": r.relname, "rows": r.n_live_tup}
                    for r in result.fetchall()
                ]
            except Exception as e:
                report["database"]["error"] = str(e)

            # Redis stats
            try:
                redis = await get_redis()
                if redis:
                    info = await redis.info()
                    report["redis"]["used_memory_mb"] = round(
                        info.get("used_memory", 0) / (1024 * 1024), 2
                    )
                    report["redis"]["connected_clients"] = info.get("connected_clients", 0)
                    report["redis"]["total_keys"] = await redis.dbsize()
            except Exception as e:
                report["redis"]["error"] = str(e)

            # User stats
            try:
                result = await db.execute(text("SELECT COUNT(*) FROM users"))
                report["users"]["total"] = result.fetchone()[0]

                result = await db.execute(
                    text("""
                        SELECT COUNT(*) FROM users
                        WHERE last_login > :date
                    """),
                    {"date": datetime.utcnow() - timedelta(days=7)},
                )
                report["users"]["active_7d"] = result.fetchone()[0]

                result = await db.execute(
                    text("""
                        SELECT COUNT(*) FROM users
                        WHERE created_at > :date
                    """),
                    {"date": datetime.utcnow() - timedelta(days=7)},
                )
                report["users"]["new_7d"] = result.fetchone()[0]
            except Exception as e:
                report["users"]["error"] = str(e)

            # Content stats
            try:
                result = await db.execute(text("SELECT COUNT(*) FROM feed_posts"))
                report["content"]["total_posts"] = result.fetchone()[0]

                result = await db.execute(
                    text("""
                        SELECT COUNT(*) FROM feed_posts
                        WHERE created_at > :date
                    """),
                    {"date": datetime.utcnow() - timedelta(days=7)},
                )
                report["content"]["posts_7d"] = result.fetchone()[0]
            except Exception as e:
                report["content"]["error"] = str(e)

            return report

    return asyncio.get_event_loop().run_until_complete(_report())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def expire_stale_subscriptions(self) -> dict:
    """
    Handle expired subscriptions and downgrade users.

    Returns:
        Processing statistics
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Processing expired subscriptions")

    async def _process():
        async with get_async_db() as db:
            from sqlalchemy import text

            # Find expired subscriptions
            result = await db.execute(
                text("""
                    UPDATE subscriptions
                    SET status = 'expired'
                    WHERE status = 'active'
                    AND current_period_end < :now
                    RETURNING id, user_id
                """),
                {"now": datetime.utcnow()},
            )

            expired = result.fetchall()
            expired_count = len(expired)

            # Downgrade users to free tier
            for sub in expired:
                await db.execute(
                    text("""
                        UPDATE users
                        SET subscription_tier = 'free'
                        WHERE id = :user_id
                    """),
                    {"user_id": sub.user_id},
                )

            await db.commit()

            return {
                "expired_subscriptions": expired_count,
                "users_downgraded": expired_count,
                "process_time": datetime.utcnow().isoformat(),
            }

    return asyncio.get_event_loop().run_until_complete(_process())
