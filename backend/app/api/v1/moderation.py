"""
Content Moderation API

Endpoints for content moderation, reporting, and review.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.services.moderation import (
    moderation_service,
    ModerationResult,
    ModerationCategory,
    ModerationAction,
    ContentType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class ModerateTextRequest(BaseModel):
    """Request to moderate text content."""

    text: str = Field(..., min_length=1, max_length=50000)
    content_type: ContentType = ContentType.TEXT
    content_id: Optional[UUID] = None


class ModerateImageRequest(BaseModel):
    """Request to moderate image content."""

    image_url: str
    content_id: Optional[UUID] = None


class ModeratePostRequest(BaseModel):
    """Request to moderate a complete post."""

    text: Optional[str] = Field(None, max_length=50000)
    media_urls: Optional[list[str]] = Field(None, max_items=10)
    content_id: Optional[UUID] = None


class ModerationResultResponse(BaseModel):
    """Moderation result response."""

    content_id: Optional[str]
    content_type: str
    is_flagged: bool
    action: str
    severity: str
    primary_category: Optional[str]
    confidence: float
    details: Optional[str]
    categories: list[dict]

    class Config:
        from_attributes = True


class ReportContentRequest(BaseModel):
    """Request to report content for moderation."""

    content_id: UUID
    content_type: ContentType
    reason: ModerationCategory
    details: Optional[str] = Field(None, max_length=1000)


class ReportResponse(BaseModel):
    """Report creation response."""

    report_id: UUID
    status: str
    message: str


class ReviewReportRequest(BaseModel):
    """Request to review a report (admin only)."""

    action: ModerationAction
    notes: Optional[str] = Field(None, max_length=1000)


class ModerationStatsResponse(BaseModel):
    """Moderation statistics response."""

    total_reports: int
    pending_reports: int
    reviewed_today: int
    auto_removed_today: int
    top_categories: list[dict]


class ModerationQueueItem(BaseModel):
    """Item in the moderation queue."""

    report_id: UUID
    content_id: UUID
    content_type: str
    reason: str
    reporter_username: Optional[str]
    reported_username: Optional[str]
    details: Optional[str]
    created_at: datetime


class ModerationQueueResponse(BaseModel):
    """Response with moderation queue items."""

    items: list[ModerationQueueItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# User Endpoints
# =============================================================================


@router.post("/text", response_model=ModerationResultResponse)
async def moderate_text(
    request: ModerateTextRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Moderate text content.

    Returns moderation result with flagged status and recommended action.
    """
    result = await moderation_service.moderate_text(
        text=request.text,
        content_type=request.content_type,
        content_id=request.content_id,
        user_id=current_user.id,
    )

    return ModerationResultResponse(
        content_id=str(result.content_id) if result.content_id else None,
        content_type=result.content_type.value,
        is_flagged=result.is_flagged,
        action=result.action.value,
        severity=result.severity.value,
        primary_category=result.primary_category.value if result.primary_category else None,
        confidence=result.confidence,
        details=result.details,
        categories=[
            {
                "category": c.category.value,
                "score": c.score,
                "flagged": c.flagged,
            }
            for c in result.categories
        ],
    )


@router.post("/image", response_model=ModerationResultResponse)
async def moderate_image(
    request: ModerateImageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Moderate image content.

    Uses AI vision to analyze image for policy violations.
    """
    result = await moderation_service.moderate_image(
        image_url=request.image_url,
        content_id=request.content_id,
        user_id=current_user.id,
    )

    return ModerationResultResponse(
        content_id=str(result.content_id) if result.content_id else None,
        content_type=result.content_type.value,
        is_flagged=result.is_flagged,
        action=result.action.value,
        severity=result.severity.value,
        primary_category=result.primary_category.value if result.primary_category else None,
        confidence=result.confidence,
        details=result.details,
        categories=[
            {
                "category": c.category.value,
                "score": c.score,
                "flagged": c.flagged,
            }
            for c in result.categories
        ],
    )


@router.post("/post", response_model=ModerationResultResponse)
async def moderate_post(
    request: ModeratePostRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Moderate a complete post (text + media).

    Combines moderation results from all content types.
    """
    result = await moderation_service.moderate_post(
        text=request.text,
        media_urls=request.media_urls,
        content_id=request.content_id,
        user_id=current_user.id,
    )

    return ModerationResultResponse(
        content_id=str(result.content_id) if result.content_id else None,
        content_type=result.content_type.value,
        is_flagged=result.is_flagged,
        action=result.action.value,
        severity=result.severity.value,
        primary_category=result.primary_category.value if result.primary_category else None,
        confidence=result.confidence,
        details=result.details,
        categories=[
            {
                "category": c.category.value,
                "score": c.score,
                "flagged": c.flagged,
            }
            for c in result.categories
        ],
    )


@router.post("/report", response_model=ReportResponse)
async def report_content(
    request: ReportContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Report content for moderation review.

    Users can report content that violates community guidelines.
    """
    # Check if user has already reported this content
    existing = await db.execute(
        text("""
            SELECT id FROM moderation_reports
            WHERE reporter_id = :reporter_id
            AND content_id = :content_id
            AND status = 'pending'
        """),
        {
            "reporter_id": current_user.id,
            "content_id": request.content_id,
        },
    )

    if existing.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reported this content",
        )

    report = await moderation_service.create_report(
        db=db,
        reporter_id=current_user.id,
        content_id=request.content_id,
        content_type=request.content_type,
        reason=request.reason,
        details=request.details,
    )

    await db.commit()

    return ReportResponse(
        report_id=report.report_id,
        status="pending",
        message="Report submitted successfully. Our team will review it shortly.",
    )


@router.get("/reports/mine")
async def get_my_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get reports submitted by the current user.
    """
    offset = (page - 1) * page_size

    result = await db.execute(
        text("""
            SELECT id, content_id, content_type, reason, details,
                   status, created_at, reviewed_at, action_taken
            FROM moderation_reports
            WHERE reporter_id = :reporter_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {
            "reporter_id": current_user.id,
            "limit": page_size,
            "offset": offset,
        },
    )

    reports = result.fetchall()

    count_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM moderation_reports
            WHERE reporter_id = :reporter_id
        """),
        {"reporter_id": current_user.id},
    )
    total = count_result.scalar()

    return {
        "reports": [
            {
                "report_id": str(r.id),
                "content_id": str(r.content_id),
                "content_type": r.content_type,
                "reason": r.reason,
                "details": r.details,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "action_taken": r.action_taken,
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# =============================================================================
# Admin Endpoints
# =============================================================================


@router.get("/admin/queue", response_model=ModerationQueueResponse)
async def get_moderation_queue(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    status_filter: str = Query("pending", regex="^(pending|reviewed|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get moderation queue for review (admin only).
    """
    offset = (page - 1) * page_size

    status_clause = ""
    if status_filter != "all":
        status_clause = "AND mr.status = :status"

    result = await db.execute(
        text(f"""
            SELECT mr.id as report_id, mr.content_id, mr.content_type,
                   mr.reason, mr.details, mr.created_at,
                   reporter.username as reporter_username,
                   reported.username as reported_username
            FROM moderation_reports mr
            LEFT JOIN users reporter ON mr.reporter_id = reporter.id
            LEFT JOIN feed_posts fp ON mr.content_id = fp.id AND mr.content_type = 'text'
            LEFT JOIN users reported ON fp.user_id = reported.id
            WHERE 1=1 {status_clause}
            ORDER BY mr.created_at ASC
            LIMIT :limit OFFSET :offset
        """),
        {
            "status": status_filter if status_filter != "all" else None,
            "limit": page_size,
            "offset": offset,
        },
    )

    items = result.fetchall()

    count_result = await db.execute(
        text(f"""
            SELECT COUNT(*) FROM moderation_reports mr
            WHERE 1=1 {status_clause}
        """),
        {"status": status_filter if status_filter != "all" else None},
    )
    total = count_result.scalar()

    return ModerationQueueResponse(
        items=[
            ModerationQueueItem(
                report_id=item.report_id,
                content_id=item.content_id,
                content_type=item.content_type,
                reason=item.reason,
                reporter_username=item.reporter_username,
                reported_username=item.reported_username,
                details=item.details,
                created_at=item.created_at,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/admin/reports/{report_id}/review")
async def review_report(
    report_id: UUID,
    request: ReviewReportRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Review and take action on a report (admin only).
    """
    # Get report
    result = await db.execute(
        text("""
            SELECT id, content_id, content_type, reporter_id, reason, status
            FROM moderation_reports
            WHERE id = :report_id
        """),
        {"report_id": report_id},
    )

    report = result.fetchone()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has already been reviewed",
        )

    # Update report status
    await db.execute(
        text("""
            UPDATE moderation_reports
            SET status = 'reviewed',
                reviewed_at = :reviewed_at,
                reviewer_id = :reviewer_id,
                action_taken = :action_taken
            WHERE id = :report_id
        """),
        {
            "report_id": report_id,
            "reviewed_at": datetime.utcnow(),
            "reviewer_id": admin.id,
            "action_taken": request.action.value,
        },
    )

    # Take action based on decision
    if request.action == ModerationAction.AUTO_REMOVE:
        # Remove content
        if report.content_type == "text":
            await db.execute(
                text("UPDATE feed_posts SET visibility = 'removed' WHERE id = :id"),
                {"id": report.content_id},
            )

    elif request.action == ModerationAction.WARN_USER:
        # Send warning notification
        await db.execute(
            text("""
                INSERT INTO notifications
                (id, user_id, type, title, message, created_at)
                SELECT gen_random_uuid(), fp.user_id, 'warning',
                       'Content Warning', 'Your content has been flagged for violating community guidelines.',
                       NOW()
                FROM feed_posts fp WHERE fp.id = :content_id
            """),
            {"content_id": report.content_id},
        )

    elif request.action == ModerationAction.SUSPEND_USER:
        # Suspend the user
        await db.execute(
            text("""
                UPDATE users
                SET is_active = false, suspended_at = NOW(), suspension_reason = :reason
                WHERE id = (SELECT user_id FROM feed_posts WHERE id = :content_id)
            """),
            {
                "content_id": report.content_id,
                "reason": request.notes or "Community guidelines violation",
            },
        )

    # Log the action
    await db.execute(
        text("""
            INSERT INTO moderation_logs
            (id, content_id, content_type, user_id, action, reason,
             automated, confidence, reviewer_id, notes, created_at)
            SELECT gen_random_uuid(), :content_id, :content_type,
                   fp.user_id, :action, :reason,
                   false, 1.0, :reviewer_id, :notes, NOW()
            FROM feed_posts fp WHERE fp.id = :content_id
        """),
        {
            "content_id": report.content_id,
            "content_type": report.content_type,
            "action": request.action.value,
            "reason": report.reason,
            "reviewer_id": admin.id,
            "notes": request.notes,
        },
    )

    await db.commit()

    return {
        "report_id": str(report_id),
        "status": "reviewed",
        "action_taken": request.action.value,
        "message": "Report reviewed successfully",
    }


@router.get("/admin/stats", response_model=ModerationStatsResponse)
async def get_moderation_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get moderation statistics (admin only).
    """
    # Total reports
    total_result = await db.execute(
        text("SELECT COUNT(*) FROM moderation_reports")
    )
    total_reports = total_result.scalar()

    # Pending reports
    pending_result = await db.execute(
        text("SELECT COUNT(*) FROM moderation_reports WHERE status = 'pending'")
    )
    pending_reports = pending_result.scalar()

    # Reviewed today
    reviewed_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM moderation_reports
            WHERE status = 'reviewed'
            AND DATE(reviewed_at) = CURRENT_DATE
        """)
    )
    reviewed_today = reviewed_result.scalar()

    # Auto-removed today
    auto_removed_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM moderation_logs
            WHERE action = 'auto_remove'
            AND automated = true
            AND DATE(created_at) = CURRENT_DATE
        """)
    )
    auto_removed_today = auto_removed_result.scalar()

    # Top categories
    categories_result = await db.execute(
        text("""
            SELECT reason, COUNT(*) as count
            FROM moderation_reports
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY reason
            ORDER BY count DESC
            LIMIT 5
        """)
    )
    top_categories = [
        {"category": r.reason, "count": r.count}
        for r in categories_result.fetchall()
    ]

    return ModerationStatsResponse(
        total_reports=total_reports or 0,
        pending_reports=pending_reports or 0,
        reviewed_today=reviewed_today or 0,
        auto_removed_today=auto_removed_today or 0,
        top_categories=top_categories,
    )


@router.get("/admin/logs")
async def get_moderation_logs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action_filter: Optional[str] = None,
    automated_only: bool = False,
):
    """
    Get moderation action logs (admin only).
    """
    offset = (page - 1) * page_size

    filters = []
    params = {"limit": page_size, "offset": offset}

    if action_filter:
        filters.append("ml.action = :action")
        params["action"] = action_filter

    if automated_only:
        filters.append("ml.automated = true")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await db.execute(
        text(f"""
            SELECT ml.id, ml.content_id, ml.content_type, ml.user_id,
                   ml.action, ml.reason, ml.automated, ml.confidence,
                   ml.reviewer_id, ml.notes, ml.created_at,
                   u.username as user_username,
                   reviewer.username as reviewer_username
            FROM moderation_logs ml
            LEFT JOIN users u ON ml.user_id = u.id
            LEFT JOIN users reviewer ON ml.reviewer_id = reviewer.id
            {where_clause}
            ORDER BY ml.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    logs = result.fetchall()

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM moderation_logs ml {where_clause}"),
        params,
    )
    total = count_result.scalar()

    return {
        "logs": [
            {
                "log_id": str(log.id),
                "content_id": str(log.content_id) if log.content_id else None,
                "content_type": log.content_type,
                "user_username": log.user_username,
                "action": log.action,
                "reason": log.reason,
                "automated": log.automated,
                "confidence": log.confidence,
                "reviewer_username": log.reviewer_username,
                "notes": log.notes,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/admin/bulk-action")
async def bulk_moderation_action(
    content_ids: list[UUID],
    action: ModerationAction,
    reason: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Perform bulk moderation action on multiple content items (admin only).
    """
    if len(content_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 items per bulk action",
        )

    actioned = 0

    for content_id in content_ids:
        try:
            if action == ModerationAction.AUTO_REMOVE:
                await db.execute(
                    text("UPDATE feed_posts SET visibility = 'removed' WHERE id = :id"),
                    {"id": content_id},
                )

            # Log the action
            await db.execute(
                text("""
                    INSERT INTO moderation_logs
                    (id, content_id, content_type, user_id, action, reason,
                     automated, confidence, reviewer_id, notes, created_at)
                    SELECT gen_random_uuid(), :content_id, 'text',
                           fp.user_id, :action, :reason,
                           false, 1.0, :reviewer_id, 'Bulk action', NOW()
                    FROM feed_posts fp WHERE fp.id = :content_id
                """),
                {
                    "content_id": content_id,
                    "action": action.value,
                    "reason": reason,
                    "reviewer_id": admin.id,
                },
            )

            actioned += 1

        except Exception as e:
            logger.error(f"Bulk action failed for {content_id}: {e}")

    await db.commit()

    return {
        "actioned": actioned,
        "total": len(content_ids),
        "action": action.value,
        "message": f"Bulk action completed: {actioned}/{len(content_ids)} items processed",
    }
