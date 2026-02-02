"""
TASK 5.2.1: Scheduling API Endpoints

REST API for content scheduling with conflict detection
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.schedule import (
    ScheduledPost,
    ScheduleStatus,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleCreateResponse,
    CalendarEvent,
    SchedulingConflictChecker,
)

router = APIRouter()


# ============================================================================
# Schedule CRUD Endpoints
# ============================================================================

@router.post("/", response_model=ScheduleCreateResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Schedule content for future publishing.
    
    - Validates scheduled time is in the future
    - Checks for conflicts (max 10 posts/hour, 3 per platform/hour)
    - Returns warnings if conflicts detected
    """
    # Check for conflicts
    conflicts = await SchedulingConflictChecker.check_conflicts(
        user_id=current_user.id,
        scheduled_at=schedule_data.scheduled_at,
        platform=schedule_data.platform,
        db_session=db,
    )
    
    # Block if there's an error-level conflict
    error_conflicts = [c for c in conflicts if c.severity == "error"]
    if error_conflicts:
        raise HTTPException(
            status_code=409,
            detail=error_conflicts[0].message,
        )
    
    # Create scheduled post
    scheduled_post = ScheduledPost(
        user_id=current_user.id,
        content_id=schedule_data.content_id,
        scheduled_at=schedule_data.scheduled_at,
        timezone=schedule_data.timezone,
        platform=schedule_data.platform,
        platform_account_id=schedule_data.platform_account_id,
        status=ScheduleStatus.PENDING,
    )
    
    db.add(scheduled_post)
    await db.commit()
    await db.refresh(scheduled_post)
    
    return ScheduleCreateResponse(
        schedule=ScheduleResponse.model_validate(scheduled_post),
        conflicts=[c for c in conflicts if c.severity == "warning"],
    )


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    status: Optional[ScheduleStatus] = None,
    platform: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List scheduled posts with optional filters.
    """
    query = select(ScheduledPost).where(
        ScheduledPost.user_id == current_user.id
    ).order_by(ScheduledPost.scheduled_at.asc())
    
    if status:
        query = query.where(ScheduledPost.status == status)
    if platform:
        query = query.where(ScheduledPost.platform == platform)
    if start_date:
        query = query.where(ScheduledPost.scheduled_at >= start_date)
    if end_date:
        query = query.where(ScheduledPost.scheduled_at <= end_date)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [ScheduleResponse.model_validate(p) for p in posts]


@router.get("/calendar", response_model=List[CalendarEvent])
async def get_calendar_events(
    start: datetime = Query(..., description="Start of calendar view"),
    end: datetime = Query(..., description="End of calendar view"),
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get calendar events for the schedule view.
    Returns events formatted for FullCalendar.js
    """
    query = select(ScheduledPost).where(
        and_(
            ScheduledPost.user_id == current_user.id,
            ScheduledPost.scheduled_at >= start,
            ScheduledPost.scheduled_at <= end,
        )
    ).order_by(ScheduledPost.scheduled_at)
    
    if platform:
        query = query.where(ScheduledPost.platform == platform)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # TODO: Join with content table to get titles
    events = []
    for post in posts:
        events.append(CalendarEvent(
            id=post.id,
            title=f"Post to {post.platform.title()}",  # Placeholder
            start=post.scheduled_at,
            end=post.scheduled_at + timedelta(minutes=30),
            platform=post.platform,
            status=post.status,
            color=_get_platform_color(post.platform),
        ))
    
    return events


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific scheduled post.
    """
    result = await db.execute(
        select(ScheduledPost).where(
            and_(
                ScheduledPost.id == schedule_id,
                ScheduledPost.user_id == current_user.id,
            )
        )
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return ScheduleResponse.model_validate(post)


@router.patch("/{schedule_id}", response_model=ScheduleCreateResponse)
async def update_schedule(
    schedule_id: UUID,
    update_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a scheduled post (reschedule).
    
    Only pending posts can be rescheduled.
    """
    result = await db.execute(
        select(ScheduledPost).where(
            and_(
                ScheduledPost.id == schedule_id,
                ScheduledPost.user_id == current_user.id,
            )
        )
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if post.status != ScheduleStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update schedule with status: {post.status}",
        )
    
    # Check conflicts if rescheduling
    conflicts = []
    if update_data.scheduled_at:
        conflicts = await SchedulingConflictChecker.check_conflicts(
            user_id=current_user.id,
            scheduled_at=update_data.scheduled_at,
            platform=post.platform,
            db_session=db,
            exclude_id=schedule_id,
        )
        
        error_conflicts = [c for c in conflicts if c.severity == "error"]
        if error_conflicts:
            raise HTTPException(status_code=409, detail=error_conflicts[0].message)
        
        post.scheduled_at = update_data.scheduled_at
    
    if update_data.timezone:
        post.timezone = update_data.timezone
    
    if update_data.status:
        post.status = update_data.status
    
    await db.commit()
    await db.refresh(post)
    
    return ScheduleCreateResponse(
        schedule=ScheduleResponse.model_validate(post),
        conflicts=[c for c in conflicts if c.severity == "warning"],
    )


@router.delete("/{schedule_id}")
async def cancel_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a scheduled post.
    """
    result = await db.execute(
        select(ScheduledPost).where(
            and_(
                ScheduledPost.id == schedule_id,
                ScheduledPost.user_id == current_user.id,
            )
        )
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if post.status == ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a post that has already been published",
        )
    
    post.status = ScheduleStatus.CANCELLED
    await db.commit()
    
    return {"status": "cancelled", "id": str(schedule_id)}


# ============================================================================
# Helper Functions
# ============================================================================

def _get_platform_color(platform: str) -> str:
    """Get color for platform in calendar view"""
    colors = {
        "instagram": "#E1306C",
        "tiktok": "#000000",
        "youtube": "#FF0000",
        "twitter": "#1DA1F2",
        "linkedin": "#0A66C2",
        "facebook": "#1877F2",
    }
    return colors.get(platform, "#8B5CF6")
