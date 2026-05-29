"""
Admin Dashboard API

Comprehensive admin endpoints for platform management, user administration,
system monitoring, and analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db, require_admin
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class DashboardStatsResponse(BaseModel):
    """Main dashboard statistics."""

    # Users
    total_users: int
    active_users_24h: int
    active_users_7d: int
    active_users_30d: int
    new_users_today: int
    new_users_7d: int

    # Content
    total_posts: int
    posts_today: int
    posts_7d: int

    # Engagement
    total_likes: int
    total_comments: int
    likes_today: int
    comments_today: int

    # AI Features
    total_twins: int
    videos_generated_today: int
    podcasts_generated_today: int

    # Revenue
    total_revenue_30d: float
    active_subscriptions: int
    mrr: float  # Monthly recurring revenue

    # System
    pending_moderation: int
    failed_jobs_24h: int


class UserListItem(BaseModel):
    """User item for admin list."""

    id: UUID
    email: str
    username: Optional[str]
    display_name: Optional[str]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    created_at: datetime
    last_login: Optional[datetime]
    post_count: int
    follower_count: int


class UserListResponse(BaseModel):
    """Response with paginated user list."""

    users: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserDetailResponse(BaseModel):
    """Detailed user information for admin."""

    id: UUID
    email: str
    username: Optional[str]
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    subscription_tier: str
    stripe_customer_id: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

    # Stats
    post_count: int
    follower_count: int
    following_count: int
    like_count: int
    comment_count: int

    # AI Usage
    twin_count: int
    videos_generated: int
    podcasts_generated: int

    # Moderation
    flags_received: int
    reports_made: int
    warnings_count: int


class UpdateUserRequest(BaseModel):
    """Request to update user details."""

    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None
    subscription_tier: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)


class SuspendUserRequest(BaseModel):
    """Request to suspend a user."""

    reason: str = Field(..., min_length=10, max_length=500)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    permanent: bool = False


class SystemHealthResponse(BaseModel):
    """System health status."""

    status: str
    timestamp: datetime
    database: dict
    redis: dict
    celery: dict
    storage: dict
    api_latency_ms: float


class JobQueueStats(BaseModel):
    """Background job queue statistics."""

    queue_name: str
    pending: int
    active: int
    completed_24h: int
    failed_24h: int
    avg_processing_time_ms: float


class FeatureFlagConfig(BaseModel):
    """Feature flag configuration."""

    name: str
    enabled: bool
    description: Optional[str]
    rollout_percentage: int = 100
    user_ids: list[UUID] = []


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get main dashboard statistics.

    Provides overview metrics for platform health and growth.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # User stats
    users_result = await db.execute(
        text("""
            SELECT
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE last_login > :day_ago) as active_24h,
                COUNT(*) FILTER (WHERE last_login > :week_ago) as active_7d,
                COUNT(*) FILTER (WHERE last_login > :month_ago) as active_30d,
                COUNT(*) FILTER (WHERE created_at >= :today) as new_today,
                COUNT(*) FILTER (WHERE created_at >= :week_ago) as new_7d
            FROM users
        """),
        {
            "day_ago": now - timedelta(days=1),
            "week_ago": week_ago,
            "month_ago": month_ago,
            "today": today_start,
        },
    )
    users = users_result.fetchone()

    # Post stats
    posts_result = await db.execute(
        text("""
            SELECT
                COUNT(*) as total_posts,
                COUNT(*) FILTER (WHERE created_at >= :today) as posts_today,
                COUNT(*) FILTER (WHERE created_at >= :week_ago) as posts_7d
            FROM feed_posts
            WHERE visibility = 'public'
        """),
        {"today": today_start, "week_ago": week_ago},
    )
    posts = posts_result.fetchone()

    # Engagement stats
    engagement_result = await db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM feed_likes) as total_likes,
                (SELECT COUNT(*) FROM feed_comments) as total_comments,
                (SELECT COUNT(*) FROM feed_likes WHERE created_at >= :today) as likes_today,
                (SELECT COUNT(*) FROM feed_comments WHERE created_at >= :today) as comments_today
        """),
        {"today": today_start},
    )
    engagement = engagement_result.fetchone()

    # AI features stats
    ai_result = await db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM ai_twins) as total_twins,
                (SELECT COUNT(*) FROM gpu_jobs WHERE job_type = 'video' AND created_at >= :today) as videos_today,
                (SELECT COUNT(*) FROM podcast_episodes WHERE created_at >= :today) as podcasts_today
        """),
        {"today": today_start},
    )
    ai_stats = ai_result.fetchone()

    # Revenue stats
    revenue_result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(amount) / 100.0, 0) as revenue_30d,
                (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subs
            FROM payments
            WHERE status = 'succeeded'
            AND created_at >= :month_ago
        """),
        {"month_ago": month_ago},
    )
    revenue = revenue_result.fetchone()

    # Calculate MRR (Monthly Recurring Revenue)
    mrr_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(sp.price_monthly) / 100.0, 0) as mrr
            FROM subscriptions s
            JOIN subscription_plans sp ON s.plan_id = sp.id
            WHERE s.status = 'active'
        """)
    )
    mrr = mrr_result.scalar() or 0

    # System stats
    system_result = await db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM moderation_reports WHERE status = 'pending') as pending_mod,
                (SELECT COUNT(*) FROM gpu_jobs WHERE status = 'failed' AND updated_at >= :day_ago) as failed_jobs
        """),
        {"day_ago": now - timedelta(days=1)},
    )
    system = system_result.fetchone()

    return DashboardStatsResponse(
        total_users=users.total_users or 0,
        active_users_24h=users.active_24h or 0,
        active_users_7d=users.active_7d or 0,
        active_users_30d=users.active_30d or 0,
        new_users_today=users.new_today or 0,
        new_users_7d=users.new_7d or 0,
        total_posts=posts.total_posts or 0,
        posts_today=posts.posts_today or 0,
        posts_7d=posts.posts_7d or 0,
        total_likes=engagement.total_likes or 0,
        total_comments=engagement.total_comments or 0,
        likes_today=engagement.likes_today or 0,
        comments_today=engagement.comments_today or 0,
        total_twins=ai_stats.total_twins or 0,
        videos_generated_today=ai_stats.videos_today or 0,
        podcasts_generated_today=ai_stats.podcasts_today or 0,
        total_revenue_30d=revenue.revenue_30d or 0,
        active_subscriptions=revenue.active_subs or 0,
        mrr=mrr,
        pending_moderation=system.pending_mod or 0,
        failed_jobs_24h=system.failed_jobs or 0,
    )


@router.get("/dashboard/charts/users")
async def get_user_growth_chart(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    days: int = Query(30, ge=7, le=90),
):
    """
    Get user growth chart data.
    """
    result = await db.execute(
        text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as new_users,
                SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as cumulative
            FROM users
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """).bindparams(days=days)
    )

    data = result.fetchall()

    return {
        "labels": [str(row.date) for row in data],
        "datasets": [
            {
                "label": "New Users",
                "data": [row.new_users for row in data],
            },
            {
                "label": "Total Users",
                "data": [row.cumulative for row in data],
            },
        ],
    }


@router.get("/dashboard/charts/revenue")
async def get_revenue_chart(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    days: int = Query(30, ge=7, le=90),
):
    """
    Get revenue chart data.
    """
    result = await db.execute(
        text("""
            SELECT
                DATE(created_at) as date,
                COALESCE(SUM(amount) / 100.0, 0) as revenue
            FROM payments
            WHERE status = 'succeeded'
            AND created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """).bindparams(days=days)
    )

    data = result.fetchall()

    return {
        "labels": [str(row.date) for row in data],
        "datasets": [
            {
                "label": "Revenue ($)",
                "data": [float(row.revenue) for row in data],
            },
        ],
    }


@router.get("/dashboard/charts/engagement")
async def get_engagement_chart(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    days: int = Query(30, ge=7, le=90),
):
    """
    Get engagement metrics chart data.
    """
    result = await db.execute(
        text("""
            WITH dates AS (
                SELECT generate_series(
                    NOW() - INTERVAL ':days days',
                    NOW(),
                    '1 day'
                )::date as date
            )
            SELECT
                d.date,
                COALESCE(p.posts, 0) as posts,
                COALESCE(l.likes, 0) as likes,
                COALESCE(c.comments, 0) as comments
            FROM dates d
            LEFT JOIN (
                SELECT DATE(created_at) as date, COUNT(*) as posts
                FROM feed_posts GROUP BY DATE(created_at)
            ) p ON d.date = p.date
            LEFT JOIN (
                SELECT DATE(created_at) as date, COUNT(*) as likes
                FROM feed_likes GROUP BY DATE(created_at)
            ) l ON d.date = l.date
            LEFT JOIN (
                SELECT DATE(created_at) as date, COUNT(*) as comments
                FROM feed_comments GROUP BY DATE(created_at)
            ) c ON d.date = c.date
            ORDER BY d.date
        """).bindparams(days=days)
    )

    data = result.fetchall()

    return {
        "labels": [str(row.date) for row in data],
        "datasets": [
            {"label": "Posts", "data": [row.posts for row in data]},
            {"label": "Likes", "data": [row.likes for row in data]},
            {"label": "Comments", "data": [row.comments for row in data]},
        ],
    }


# =============================================================================
# User Management Endpoints
# =============================================================================


@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|last_login|email|username)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """
    List all users with filtering and pagination.
    """
    offset = (page - 1) * page_size

    # Build filters
    filters = []
    params = {"limit": page_size, "offset": offset}

    if search:
        filters.append(
            "(u.email ILIKE :search OR u.username ILIKE :search OR up.display_name ILIKE :search)"
        )
        params["search"] = f"%{search}%"

    if subscription_tier:
        filters.append("u.subscription_tier = :tier")
        params["tier"] = subscription_tier

    if is_active is not None:
        filters.append("u.is_active = :is_active")
        params["is_active"] = is_active

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await db.execute(
        text(f"""
            SELECT
                u.id, u.email, u.username, u.is_active, u.is_verified,
                u.subscription_tier, u.created_at, u.last_login,
                up.display_name,
                COALESCE(up.post_count, 0) as post_count,
                COALESCE(up.follower_count, 0) as follower_count
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            {where_clause}
            ORDER BY u.{sort_by} {sort_order}
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    users = result.fetchall()

    # Get total count
    count_result = await db.execute(
        text(f"""
            SELECT COUNT(*)
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            {where_clause}
        """),
        params,
    )
    total = count_result.scalar()

    return UserListResponse(
        users=[
            UserListItem(
                id=u.id,
                email=u.email,
                username=u.username,
                display_name=u.display_name,
                is_active=u.is_active,
                is_verified=u.is_verified,
                subscription_tier=u.subscription_tier or "free",
                created_at=u.created_at,
                last_login=u.last_login,
                post_count=u.post_count,
                follower_count=u.follower_count,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get detailed user information.
    """
    result = await db.execute(
        text("""
            SELECT
                u.id, u.email, u.username, u.is_active, u.is_verified, u.is_admin,
                u.subscription_tier, u.stripe_customer_id, u.created_at, u.last_login,
                up.display_name, up.bio, up.avatar_url,
                COALESCE(up.post_count, 0) as post_count,
                COALESCE(up.follower_count, 0) as follower_count,
                COALESCE(up.following_count, 0) as following_count,
                (SELECT COUNT(*) FROM feed_likes WHERE user_id = u.id) as like_count,
                (SELECT COUNT(*) FROM feed_comments WHERE user_id = u.id) as comment_count,
                (SELECT COUNT(*) FROM ai_twins WHERE user_id = u.id) as twin_count,
                (SELECT COUNT(*) FROM gpu_jobs WHERE user_id = u.id AND job_type = 'video') as videos_generated,
                (SELECT COUNT(*) FROM podcast_episodes WHERE user_id = u.id) as podcasts_generated,
                (SELECT COUNT(*) FROM moderation_logs WHERE user_id = u.id AND action IN ('flag_for_review', 'auto_remove')) as flags_received,
                (SELECT COUNT(*) FROM moderation_reports WHERE reporter_id = u.id) as reports_made,
                (SELECT COUNT(*) FROM moderation_logs WHERE user_id = u.id AND action = 'warn_user') as warnings_count
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id = :user_id
        """),
        {"user_id": user_id},
    )

    user = result.fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin or False,
        subscription_tier=user.subscription_tier or "free",
        stripe_customer_id=user.stripe_customer_id,
        created_at=user.created_at,
        last_login=user.last_login,
        post_count=user.post_count,
        follower_count=user.follower_count,
        following_count=user.following_count,
        like_count=user.like_count,
        comment_count=user.comment_count,
        twin_count=user.twin_count,
        videos_generated=user.videos_generated,
        podcasts_generated=user.podcasts_generated,
        flags_received=user.flags_received,
        reports_made=user.reports_made,
        warnings_count=user.warnings_count,
    )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update user settings (admin only).
    """
    # Check user exists
    result = await db.execute(
        text("SELECT id, email FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update query
    updates = []
    params = {"user_id": user_id}

    if request.is_active is not None:
        updates.append("is_active = :is_active")
        params["is_active"] = request.is_active

    if request.is_verified is not None:
        updates.append("is_verified = :is_verified")
        params["is_verified"] = request.is_verified

    if request.is_admin is not None:
        updates.append("is_admin = :is_admin")
        params["is_admin"] = request.is_admin

    if request.subscription_tier is not None:
        updates.append("subscription_tier = :subscription_tier")
        params["subscription_tier"] = request.subscription_tier

    if updates:
        await db.execute(
            text(f"UPDATE users SET {', '.join(updates)} WHERE id = :user_id"),
            params,
        )

    # Log admin action
    await db.execute(
        text("""
            INSERT INTO admin_audit_log
            (id, admin_id, action, target_type, target_id, details, created_at)
            VALUES (gen_random_uuid(), :admin_id, 'update_user', 'user', :user_id, :details, NOW())
        """),
        {
            "admin_id": admin.id,
            "user_id": user_id,
            "details": request.model_dump_json(),
        },
    )

    await db.commit()

    return {"status": "updated", "user_id": str(user_id)}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: UUID,
    request: SuspendUserRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Suspend a user account.
    """
    # Check user exists and is not an admin
    result = await db.execute(
        text("SELECT id, email, is_admin FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot suspend admin users")

    # Calculate suspension end date
    suspension_end = None
    if not request.permanent and request.duration_days:
        suspension_end = datetime.utcnow() + timedelta(days=request.duration_days)

    # Suspend user
    await db.execute(
        text("""
            UPDATE users
            SET is_active = false,
                suspended_at = NOW(),
                suspension_reason = :reason,
                suspension_end = :suspension_end
            WHERE id = :user_id
        """),
        {
            "user_id": user_id,
            "reason": request.reason,
            "suspension_end": suspension_end,
        },
    )

    # Log action
    await db.execute(
        text("""
            INSERT INTO admin_audit_log
            (id, admin_id, action, target_type, target_id, details, created_at)
            VALUES (gen_random_uuid(), :admin_id, 'suspend_user', 'user', :user_id, :details, NOW())
        """),
        {
            "admin_id": admin.id,
            "user_id": user_id,
            "details": request.model_dump_json(),
        },
    )

    await db.commit()

    return {
        "status": "suspended",
        "user_id": str(user_id),
        "permanent": request.permanent,
        "suspension_end": suspension_end.isoformat() if suspension_end else None,
    }


@router.post("/users/{user_id}/unsuspend")
async def unsuspend_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Remove suspension from a user account.
    """
    await db.execute(
        text("""
            UPDATE users
            SET is_active = true,
                suspended_at = NULL,
                suspension_reason = NULL,
                suspension_end = NULL
            WHERE id = :user_id
        """),
        {"user_id": user_id},
    )

    # Log action
    await db.execute(
        text("""
            INSERT INTO admin_audit_log
            (id, admin_id, action, target_type, target_id, details, created_at)
            VALUES (gen_random_uuid(), :admin_id, 'unsuspend_user', 'user', :user_id, '{}', NOW())
        """),
        {"admin_id": admin.id, "user_id": user_id},
    )

    await db.commit()

    return {"status": "unsuspended", "user_id": str(user_id)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    hard_delete: bool = Query(False),
):
    """
    Delete a user account.

    By default performs soft delete. Use hard_delete=true for permanent removal.
    """
    # Check user exists
    result = await db.execute(
        text("SELECT id, email, is_admin FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin users")

    if hard_delete:
        # Permanent deletion - cascade will handle related records
        await db.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
    else:
        # Soft delete
        await db.execute(
            text("""
                UPDATE users
                SET is_active = false,
                    email = CONCAT('deleted_', id::text, '@deleted.idkit.com'),
                    deleted_at = NOW()
                WHERE id = :user_id
            """),
            {"user_id": user_id},
        )

    # Log action
    await db.execute(
        text("""
            INSERT INTO admin_audit_log
            (id, admin_id, action, target_type, target_id, details, created_at)
            VALUES (gen_random_uuid(), :admin_id, :action, 'user', :user_id, '{}', NOW())
        """),
        {
            "admin_id": admin.id,
            "user_id": user_id,
            "action": "hard_delete_user" if hard_delete else "soft_delete_user",
        },
    )

    await db.commit()

    return {
        "status": "deleted",
        "user_id": str(user_id),
        "hard_delete": hard_delete,
    }


# =============================================================================
# System Management Endpoints
# =============================================================================


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get comprehensive system health status.
    """
    import time
    from app.core.redis import get_redis

    start = time.time()
    health_status = "healthy"
    issues = []

    # Database health
    db_health = {"status": "healthy", "latency_ms": 0}
    try:
        db_start = time.time()
        await db.execute(text("SELECT 1"))
        db_health["latency_ms"] = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        db_health = {"status": "unhealthy", "error": str(e)}
        health_status = "degraded"

    # Redis health
    redis_health = {"status": "healthy", "latency_ms": 0}
    try:
        redis = await get_redis()
        if redis:
            redis_start = time.time()
            await redis.ping()
            redis_health["latency_ms"] = round((time.time() - redis_start) * 1000, 2)
            info = await redis.info()
            redis_health["memory_used_mb"] = round(
                info.get("used_memory", 0) / (1024 * 1024), 2
            )
        else:
            redis_health = {"status": "unavailable"}
    except Exception as e:
        redis_health = {"status": "unhealthy", "error": str(e)}
        health_status = "degraded"

    # Celery health
    celery_health = {"status": "unknown"}
    try:
        from app.workers.celery_app import celery_app

        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        if active_workers:
            celery_health = {
                "status": "healthy",
                "workers": len(active_workers),
                "active_tasks": sum(len(tasks) for tasks in active_workers.values()),
            }
        else:
            celery_health = {"status": "no_workers"}
            health_status = "degraded"
    except Exception as e:
        celery_health = {"status": "unhealthy", "error": str(e)}

    # Storage health (S3/MinIO)
    storage_health = {"status": "unknown"}
    try:
        from app.services.storage import storage_service

        if storage_service:
            # Try to list bucket
            storage_health = {"status": "healthy"}
    except Exception as e:
        storage_health = {"status": "unhealthy", "error": str(e)}

    api_latency = round((time.time() - start) * 1000, 2)

    return SystemHealthResponse(
        status=health_status,
        timestamp=datetime.utcnow(),
        database=db_health,
        redis=redis_health,
        celery=celery_health,
        storage=storage_health,
        api_latency_ms=api_latency,
    )


@router.get("/system/jobs", response_model=list[JobQueueStats])
async def get_job_queue_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get background job queue statistics.
    """
    from app.core.redis import get_redis

    queues = ["default", "notifications", "email", "content", "gpu", "social", "analytics"]
    stats = []

    redis = await get_redis()

    for queue in queues:
        queue_stats = JobQueueStats(
            queue_name=queue,
            pending=0,
            active=0,
            completed_24h=0,
            failed_24h=0,
            avg_processing_time_ms=0,
        )

        if redis:
            try:
                # Get pending count from Redis
                pending = await redis.llen(f"celery:{queue}")
                queue_stats.pending = pending or 0
            except Exception:
                pass

        # Get completed/failed from DB
        result = await db.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed' AND updated_at > NOW() - INTERVAL '24 hours') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '24 hours') as failed
                FROM gpu_jobs
                WHERE queue_name = :queue
            """),
            {"queue": queue},
        )
        row = result.fetchone()
        if row:
            queue_stats.completed_24h = row.completed or 0
            queue_stats.failed_24h = row.failed or 0

        stats.append(queue_stats)

    return stats


@router.post("/system/jobs/{job_id}/retry")
async def retry_failed_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retry a failed background job.
    """
    result = await db.execute(
        text("SELECT id, task_name, args, status FROM gpu_jobs WHERE id = :job_id"),
        {"job_id": job_id},
    )
    job = result.fetchone()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    # Reset job status
    await db.execute(
        text("""
            UPDATE gpu_jobs
            SET status = 'pending', error = NULL, retries = retries + 1
            WHERE id = :job_id
        """),
        {"job_id": job_id},
    )

    await db.commit()

    # Re-queue the task
    from app.workers.celery_app import celery_app
    import json

    celery_app.send_task(
        job.task_name,
        args=json.loads(job.args) if job.args else [],
    )

    return {"status": "retried", "job_id": str(job_id)}


@router.get("/system/audit-log")
async def get_audit_log(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action_filter: Optional[str] = None,
):
    """
    Get admin audit log.
    """
    offset = (page - 1) * page_size
    params = {"limit": page_size, "offset": offset}

    where_clause = ""
    if action_filter:
        where_clause = "WHERE al.action = :action"
        params["action"] = action_filter

    result = await db.execute(
        text(f"""
            SELECT al.id, al.admin_id, al.action, al.target_type, al.target_id,
                   al.details, al.created_at, u.email as admin_email
            FROM admin_audit_log al
            JOIN users u ON al.admin_id = u.id
            {where_clause}
            ORDER BY al.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    logs = result.fetchall()

    return {
        "logs": [
            {
                "id": str(log.id),
                "admin_email": log.admin_email,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": str(log.target_id) if log.target_id else None,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "page": page,
        "page_size": page_size,
    }


# =============================================================================
# Feature Flags Endpoints
# =============================================================================


@router.get("/feature-flags")
async def list_feature_flags(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all feature flags.
    """
    result = await db.execute(
        text("""
            SELECT name, enabled, description, rollout_percentage, user_ids, updated_at
            FROM feature_flags
            ORDER BY name
        """)
    )

    flags = result.fetchall()

    return {
        "flags": [
            {
                "name": f.name,
                "enabled": f.enabled,
                "description": f.description,
                "rollout_percentage": f.rollout_percentage,
                "user_ids": f.user_ids or [],
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in flags
        ]
    }


@router.put("/feature-flags/{flag_name}")
async def update_feature_flag(
    flag_name: str,
    config: FeatureFlagConfig,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update or create a feature flag.
    """
    await db.execute(
        text("""
            INSERT INTO feature_flags (name, enabled, description, rollout_percentage, user_ids, updated_at)
            VALUES (:name, :enabled, :description, :rollout_percentage, :user_ids, NOW())
            ON CONFLICT (name) DO UPDATE SET
                enabled = :enabled,
                description = :description,
                rollout_percentage = :rollout_percentage,
                user_ids = :user_ids,
                updated_at = NOW()
        """),
        {
            "name": config.name,
            "enabled": config.enabled,
            "description": config.description,
            "rollout_percentage": config.rollout_percentage,
            "user_ids": [str(uid) for uid in config.user_ids],
        },
    )

    await db.commit()

    return {"status": "updated", "flag_name": flag_name}


@router.delete("/feature-flags/{flag_name}")
async def delete_feature_flag(
    flag_name: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a feature flag.
    """
    await db.execute(
        text("DELETE FROM feature_flags WHERE name = :name"),
        {"name": flag_name},
    )
    await db.commit()

    return {"status": "deleted", "flag_name": flag_name}


# =============================================================================
# Announcements Endpoints
# =============================================================================


@router.get("/announcements")
async def list_announcements(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all announcements.
    """
    result = await db.execute(
        text("""
            SELECT id, title, content, type, is_active, target_audience,
                   start_date, end_date, created_at
            FROM announcements
            ORDER BY created_at DESC
        """)
    )

    announcements = result.fetchall()

    return {
        "announcements": [
            {
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "type": a.type,
                "is_active": a.is_active,
                "target_audience": a.target_audience,
                "start_date": a.start_date.isoformat() if a.start_date else None,
                "end_date": a.end_date.isoformat() if a.end_date else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in announcements
        ]
    }


@router.post("/announcements")
async def create_announcement(
    title: str,
    content: str,
    type: str = "info",  # info, warning, maintenance
    target_audience: str = "all",  # all, free, premium, enterprise
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new announcement.
    """
    result = await db.execute(
        text("""
            INSERT INTO announcements
            (id, title, content, type, is_active, target_audience, start_date, end_date, created_at)
            VALUES (gen_random_uuid(), :title, :content, :type, true, :audience, :start_date, :end_date, NOW())
            RETURNING id
        """),
        {
            "title": title,
            "content": content,
            "type": type,
            "audience": target_audience,
            "start_date": start_date or datetime.utcnow(),
            "end_date": end_date,
        },
    )

    announcement_id = result.scalar()
    await db.commit()

    return {"status": "created", "announcement_id": str(announcement_id)}


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete an announcement.
    """
    await db.execute(
        text("DELETE FROM announcements WHERE id = :id"),
        {"id": announcement_id},
    )
    await db.commit()

    return {"status": "deleted", "announcement_id": str(announcement_id)}


@router.get("/exports")
async def _qa_list_exports():
    return []
