"""
Celery Tasks Package

All background tasks organized by domain.
"""

from app.workers.tasks.content_tasks import (
    generate_content,
    repurpose_content,
    generate_script,
)
from app.workers.tasks.publishing_tasks import (
    publish_to_platform,
    check_scheduled_posts,
    publish_batch,
)
from app.workers.tasks.notification_tasks import (
    send_notification,
    send_batch_notifications,
)
from app.workers.tasks.email_tasks import (
    send_email,
    send_welcome_email,
    send_weekly_digest,
)
from app.workers.tasks.analytics_tasks import (
    sync_social_analytics,
    generate_daily_report,
    calculate_engagement_metrics,
)
from app.workers.tasks.twin_tasks import (
    train_avatar,
    clone_voice,
    generate_video,
)
from app.workers.tasks.podcast_tasks import (
    generate_episode,
    extract_clips,
    distribute_episode,
)
from app.workers.tasks.maintenance_tasks import (
    cleanup_expired_sessions,
    cleanup_old_jobs,
    cleanup_orphaned_media,
)

__all__ = [
    # Content
    "generate_content",
    "repurpose_content",
    "generate_script",
    # Publishing
    "publish_to_platform",
    "check_scheduled_posts",
    "publish_batch",
    # Notifications
    "send_notification",
    "send_batch_notifications",
    # Email
    "send_email",
    "send_welcome_email",
    "send_weekly_digest",
    # Analytics
    "sync_social_analytics",
    "generate_daily_report",
    "calculate_engagement_metrics",
    # AI Twin
    "train_avatar",
    "clone_voice",
    "generate_video",
    # Podcast
    "generate_episode",
    "extract_clips",
    "distribute_episode",
    # Maintenance
    "cleanup_expired_sessions",
    "cleanup_old_jobs",
    "cleanup_orphaned_media",
]
