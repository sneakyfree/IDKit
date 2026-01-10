"""
Celery Application Configuration

Central Celery app configuration with task discovery and scheduling.
"""

import logging
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "idkit",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result settings
    result_expires=3600,  # 1 hour
    result_extended=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,  # For long-running tasks
    worker_concurrency=4,

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Task routes
    task_routes={
        # High priority tasks
        "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.workers.tasks.email_tasks.*": {"queue": "email"},

        # Content generation (longer running)
        "app.workers.tasks.content_tasks.*": {"queue": "content"},
        "app.workers.tasks.podcast_tasks.*": {"queue": "content"},

        # GPU tasks (separate queue for GPU workers)
        "app.workers.tasks.gpu_tasks.*": {"queue": "gpu"},
        "app.workers.tasks.twin_tasks.*": {"queue": "gpu"},

        # Social media (rate limited)
        "app.workers.tasks.social_tasks.*": {"queue": "social"},
        "app.workers.tasks.publishing_tasks.*": {"queue": "social"},

        # Analytics and reporting
        "app.workers.tasks.analytics_tasks.*": {"queue": "analytics"},

        # Default queue
        "app.workers.tasks.*": {"queue": "default"},
    },

    # Task annotations (rate limits)
    task_annotations={
        "app.workers.tasks.social_tasks.publish_to_platform": {
            "rate_limit": "10/m",  # 10 per minute
        },
        "app.workers.tasks.email_tasks.send_email": {
            "rate_limit": "100/m",  # 100 per minute
        },
    },

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Every minute
        "check-scheduled-posts": {
            "task": "app.workers.tasks.publishing_tasks.check_scheduled_posts",
            "schedule": 60.0,  # Every minute
        },
        "check-scheduled-podcast-distributions": {
            "task": "app.workers.tasks.podcast_tasks.check_scheduled_podcast_distributions",
            "schedule": 60.0,  # Every minute
        },

        # Every 5 minutes
        "sync-social-analytics": {
            "task": "app.workers.tasks.analytics_tasks.sync_social_analytics",
            "schedule": 300.0,  # Every 5 minutes
        },

        # Every 15 minutes
        "process-webhook-queue": {
            "task": "app.workers.tasks.social_tasks.process_webhook_queue",
            "schedule": 900.0,  # Every 15 minutes
        },

        # Every hour
        "cleanup-expired-sessions": {
            "task": "app.workers.tasks.maintenance_tasks.cleanup_expired_sessions",
            "schedule": crontab(minute=0),  # Every hour at minute 0
        },
        "refresh-oauth-tokens": {
            "task": "app.workers.tasks.social_tasks.refresh_expiring_tokens",
            "schedule": crontab(minute=30),  # Every hour at minute 30
        },

        # Daily tasks
        "generate-daily-analytics": {
            "task": "app.workers.tasks.analytics_tasks.generate_daily_report",
            "schedule": crontab(hour=1, minute=0),  # 1:00 AM UTC
        },
        "cleanup-old-jobs": {
            "task": "app.workers.tasks.maintenance_tasks.cleanup_old_jobs",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC
        },
        "detect-trending-topics": {
            "task": "app.workers.tasks.trends_tasks.detect_trending",
            "schedule": crontab(hour=6, minute=0),  # 6:00 AM UTC
        },

        # Weekly tasks
        "generate-weekly-digest": {
            "task": "app.workers.tasks.email_tasks.send_weekly_digest",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM
        },
        "cleanup-orphaned-media": {
            "task": "app.workers.tasks.maintenance_tasks.cleanup_orphaned_media",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.workers.tasks",
])


# Task lifecycle hooks
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "worker": self.request.hostname}


# Error handling
@celery_app.task(bind=True)
def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Global task failure handler."""
    logger.error(
        f"Task {task_id} failed: {exc}\n"
        f"Args: {args}\n"
        f"Kwargs: {kwargs}\n"
        f"Traceback: {einfo}"
    )
