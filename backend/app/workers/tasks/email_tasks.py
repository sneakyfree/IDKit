"""
Email Tasks

Background tasks for email sending.
"""

import logging
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    rate_limit="100/m",
)
def send_email(
    self,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    attachments: Optional[list] = None,
) -> dict:
    """
    Send an email.

    Args:
        to_email: Recipient email
        subject: Email subject
        body_html: HTML body
        body_text: Plain text body (optional)
        from_email: Sender email (optional, uses default)
        reply_to: Reply-to address (optional)
        attachments: List of attachments (optional)

    Returns:
        Email send result
    """
    import asyncio
    from app.config import settings

    logger.info(f"Sending email to {to_email}: {subject}")

    async def _send_email():
        # For development, use Mailhog via SMTP
        if settings.environment == "development":
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email or "noreply@idkit.app"
            msg["To"] = to_email

            if reply_to:
                msg["Reply-To"] = reply_to

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            try:
                await aiosmtplib.send(
                    msg,
                    hostname="localhost",
                    port=1025,  # Mailhog port
                )
                return {"success": True, "message_id": None}
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                return {"success": False, "error": str(e)}

        # Production: Use configured email service (SES, SendGrid, Mailgun, or SMTP)
        else:
            from app.services.email.service import email_service, configure_email_service

            # Ensure email service is configured
            if not email_service._primary_provider:
                configure_email_service()

            # Use the unified email service with automatic fallback
            result = await email_service.send(
                to=to_email,
                subject=subject,
                html_body=body_html,
                text_body=body_text,
                from_email=from_email,
                reply_to=reply_to,
                tags=["transactional"],
            )

            return {
                "success": result.success,
                "message_id": result.message_id,
                "provider": result.provider,
                "error": result.error,
            }

    return asyncio.get_event_loop().run_until_complete(_send_email())


@celery_app.task
def send_welcome_email(user_id: str) -> dict:
    """
    Send welcome email to a new user.

    Args:
        user_id: New user ID

    Returns:
        Email send result
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Sending welcome email to user {user_id}")

    async def _send_welcome():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()

            if not user:
                return {"error": "User not found"}

            name = user.full_name or "there"

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #6366f1;">Welcome to IDKit!</h1>
                <p>Hi {name},</p>
                <p>Thanks for joining IDKit - your AI-powered influencer toolkit!</p>
                <p>Here's what you can do:</p>
                <ul>
                    <li>Create your AI Twin for video content</li>
                    <li>Generate scripts and posts with AI</li>
                    <li>Launch podcasts in one click</li>
                    <li>Schedule posts across all platforms</li>
                </ul>
                <p>
                    <a href="https://app.idkit.io/onboarding"
                       style="background: #6366f1; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 6px;">
                        Get Started
                    </a>
                </p>
                <p>Questions? Just reply to this email!</p>
                <p>The IDKit Team</p>
            </body>
            </html>
            """

            return await send_email(
                to_email=user.email,
                subject="Welcome to IDKit!",
                body_html=html,
                body_text=f"Welcome to IDKit, {name}! Start creating at https://app.idkit.io/onboarding",
            )

    return asyncio.get_event_loop().run_until_complete(_send_welcome())


async def _get_weekly_digest_stats(db, user_id: UUID) -> dict:
    """
    Fetch actual analytics data for the weekly digest email.

    Combines:
    - Internal IDKit feed stats (views, likes on user's posts)
    - External platform analytics (via unified analytics service)
    - Follower growth data
    - Top performing content

    Args:
        db: Database session
        user_id: User ID to get stats for

    Returns:
        Dict with views, likes, followers_gained, top_post
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, func
    from app.models.feed import FeedPost, FeedLike, Follow

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    # Get internal feed stats
    internal_views = 0
    internal_likes = 0
    top_post_title = "Your latest content"

    # Sum views and likes from user's posts created/viewed in last 7 days
    posts_result = await db.execute(
        select(
            func.sum(FeedPost.view_count).label("total_views"),
            func.sum(FeedPost.like_count).label("total_likes"),
        ).where(
            FeedPost.user_id == user_id,
            FeedPost.created_at >= start_date,
        )
    )
    posts_row = posts_result.one_or_none()
    if posts_row:
        internal_views = posts_row.total_views or 0
        internal_likes = posts_row.total_likes or 0

    # Get top performing post this week
    top_post_result = await db.execute(
        select(FeedPost)
        .where(
            FeedPost.user_id == user_id,
            FeedPost.created_at >= start_date,
        )
        .order_by(FeedPost.engagement_score.desc())
        .limit(1)
    )
    top_post = top_post_result.scalar_one_or_none()
    if top_post:
        if top_post.content_text:
            # Truncate to first 50 chars
            top_post_title = top_post.content_text[:50]
            if len(top_post.content_text) > 50:
                top_post_title += "..."
        else:
            top_post_title = f"Your {top_post.post_type} post"

    # Count new followers this week
    followers_result = await db.execute(
        select(func.count(Follow.id)).where(
            Follow.following_id == user_id,
            Follow.created_at >= start_date,
        )
    )
    followers_gained = followers_result.scalar() or 0

    # Try to get external platform analytics
    external_views = 0
    external_likes = 0
    external_followers = 0

    try:
        from app.services.analytics.unified_analytics import UnifiedAnalyticsService

        analytics_service = UnifiedAnalyticsService(db)
        unified_metrics = await analytics_service.get_unified_metrics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        external_views = unified_metrics.total_views
        external_likes = unified_metrics.total_likes
        external_followers = unified_metrics.total_follower_change

        # Check if external top content outperforms internal
        if unified_metrics.platform_breakdown:
            for platform in unified_metrics.platform_breakdown:
                if platform.best_post_engagement and top_post:
                    if platform.best_post_engagement > (top_post.engagement_score * 1000):
                        top_post_title = f"Your {platform.platform.title()} content"

    except Exception as e:
        # Log but continue with internal stats only
        logger.warning(f"Failed to fetch external analytics for user {user_id}: {e}")

    # Combine internal and external stats
    return {
        "views": internal_views + external_views,
        "likes": internal_likes + external_likes,
        "followers_gained": followers_gained + external_followers,
        "top_post": top_post_title,
    }


@celery_app.task
def send_weekly_digest() -> dict:
    """
    Send weekly digest emails to all users.

    This runs weekly via Celery Beat.
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Sending weekly digest emails")

    async def _send_digest():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            # Get all active users
            result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()

            sent = 0
            for user in users:
                # Generate personalized digest with actual analytics
                stats = await _get_weekly_digest_stats(db, user.id)

                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #6366f1;">Your Weekly IDKit Digest</h1>
                    <p>Hi {user.full_name or 'there'},</p>
                    <p>Here's how your content performed this week:</p>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                        <p><strong>Views:</strong> {stats['views']:,}</p>
                        <p><strong>Likes:</strong> {stats['likes']:,}</p>
                        <p><strong>New Followers:</strong> +{stats['followers_gained']}</p>
                        <p><strong>Top Performer:</strong> {stats['top_post']}</p>
                    </div>
                    <p style="margin-top: 20px;">
                        <a href="https://app.idkit.io/analytics"
                           style="background: #6366f1; color: white; padding: 12px 24px;
                                  text-decoration: none; border-radius: 6px;">
                            View Full Analytics
                        </a>
                    </p>
                    <p>Keep creating!</p>
                    <p>The IDKit Team</p>
                </body>
                </html>
                """

                await send_email(
                    to_email=user.email,
                    subject="Your Weekly IDKit Digest",
                    body_html=html,
                )
                sent += 1

            return {"total_users": len(users), "sent": sent}

    return asyncio.get_event_loop().run_until_complete(_send_digest())


@celery_app.task
def send_subscription_confirmation(
    user_id: str,
    plan_name: str,
    amount: int,
    currency: str,
    next_billing_date: str,
) -> dict:
    """Send subscription confirmation email."""
    import asyncio
    from app.workers.utils import get_async_db

    async def _send():
        async with get_async_db() as db:
            from sqlalchemy import select
            from app.models.user import User

            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()

            if not user:
                return {"error": "User not found"}

            # Format amount
            amount_formatted = f"${amount / 100:.2f}" if currency == "usd" else f"{amount / 100:.2f} {currency.upper()}"

            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #6366f1;">Subscription Confirmed!</h1>
                <p>Hi {user.full_name or 'there'},</p>
                <p>Your subscription to <strong>IDKit {plan_name}</strong> is now active.</p>
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                    <p><strong>Plan:</strong> {plan_name}</p>
                    <p><strong>Amount:</strong> {amount_formatted}</p>
                    <p><strong>Next billing:</strong> {next_billing_date}</p>
                </div>
                <p style="margin-top: 20px;">
                    <a href="https://app.idkit.io/settings/billing"
                       style="background: #6366f1; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 6px;">
                        Manage Subscription
                    </a>
                </p>
                <p>Thanks for upgrading!</p>
                <p>The IDKit Team</p>
            </body>
            </html>
            """

            return await send_email(
                to_email=user.email,
                subject=f"Welcome to IDKit {plan_name}!",
                body_html=html,
            )

    return asyncio.get_event_loop().run_until_complete(_send())
