"""
Notifications API Endpoints

User notification management and settings.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.dependencies import DB, CurrentUser
from app.models.notification import NotificationType
from app.services.notification import NotificationService

router = APIRouter()


# ==================== Schemas ====================


class NotificationResponse(BaseModel):
    """Notification response."""

    id: uuid.UUID
    notification_type: str
    title: str
    body: Optional[str]
    actor_id: Optional[uuid.UUID]
    post_id: Optional[uuid.UUID]
    comment_id: Optional[uuid.UUID]
    metadata: dict
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    notifications: List[NotificationResponse]
    unread_count: int
    page: int
    page_size: int


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""

    notification_ids: Optional[List[uuid.UUID]] = None  # None = mark all as read


class MarkReadResponse(BaseModel):
    """Response after marking notifications as read."""

    marked_count: int
    unread_count: int


class NotificationSettingsResponse(BaseModel):
    """User notification settings."""

    push_enabled: bool
    push_likes: bool
    push_comments: bool
    push_follows: bool
    push_mentions: bool
    push_ai_complete: bool
    email_enabled: bool
    email_digest_frequency: str
    quiet_hours: dict


class UpdateSettingsRequest(BaseModel):
    """Request to update notification settings."""

    push_enabled: Optional[bool] = None
    push_likes: Optional[bool] = None
    push_comments: Optional[bool] = None
    push_follows: Optional[bool] = None
    push_mentions: Optional[bool] = None
    push_ai_complete: Optional[bool] = None
    email_enabled: Optional[bool] = None
    email_digest_frequency: Optional[str] = Field(
        None, regex="^(none|instant|daily|weekly)$"
    )
    quiet_hours: Optional[dict] = None


# ==================== Endpoints ====================


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    unread_only: bool = Query(default=False),
):
    """Get user notifications with pagination."""
    service = NotificationService(db)

    notifications = await service.get_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )

    unread_count = await service.get_unread_count(current_user.id)

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                notification_type=n.notification_type,
                title=n.title,
                body=n.body,
                actor_id=n.actor_id,
                post_id=n.post_id,
                comment_id=n.comment_id,
                metadata=n.metadata,
                is_read=n.is_read,
                created_at=n.created_at.isoformat(),
            )
            for n in notifications
        ],
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count")
async def get_unread_count(
    db: DB,
    current_user: CurrentUser,
):
    """Get unread notification count."""
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)

    return {"unread_count": count}


@router.post("/read", response_model=MarkReadResponse)
async def mark_as_read(
    request: MarkReadRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Mark notifications as read.

    If notification_ids is not provided, marks all notifications as read.
    """
    service = NotificationService(db)

    marked_count = await service.mark_as_read(
        user_id=current_user.id,
        notification_ids=request.notification_ids,
    )

    unread_count = await service.get_unread_count(current_user.id)

    return MarkReadResponse(
        marked_count=marked_count,
        unread_count=unread_count,
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete a specific notification."""
    service = NotificationService(db)

    success = await service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"success": True}


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: DB,
    current_user: CurrentUser,
):
    """Get user notification settings."""
    from sqlalchemy import select
    from app.models.notification import NotificationSettings

    result = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.user_id == current_user.id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Return defaults
        return NotificationSettingsResponse(
            push_enabled=True,
            push_likes=True,
            push_comments=True,
            push_follows=True,
            push_mentions=True,
            push_ai_complete=True,
            email_enabled=True,
            email_digest_frequency="daily",
            quiet_hours={},
        )

    return NotificationSettingsResponse(
        push_enabled=settings.push_enabled,
        push_likes=settings.push_likes,
        push_comments=settings.push_comments,
        push_follows=settings.push_follows,
        push_mentions=settings.push_mentions,
        push_ai_complete=settings.push_ai_complete,
        email_enabled=settings.email_enabled,
        email_digest_frequency=settings.email_digest_frequency,
        quiet_hours=settings.quiet_hours,
    )


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: UpdateSettingsRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Update user notification settings."""
    from sqlalchemy import select
    from app.models.notification import NotificationSettings

    result = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.user_id == current_user.id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create new settings
        settings = NotificationSettings(user_id=current_user.id)
        db.add(settings)

    # Update fields if provided
    if request.push_enabled is not None:
        settings.push_enabled = request.push_enabled
    if request.push_likes is not None:
        settings.push_likes = request.push_likes
    if request.push_comments is not None:
        settings.push_comments = request.push_comments
    if request.push_follows is not None:
        settings.push_follows = request.push_follows
    if request.push_mentions is not None:
        settings.push_mentions = request.push_mentions
    if request.push_ai_complete is not None:
        settings.push_ai_complete = request.push_ai_complete
    if request.email_enabled is not None:
        settings.email_enabled = request.email_enabled
    if request.email_digest_frequency is not None:
        settings.email_digest_frequency = request.email_digest_frequency
    if request.quiet_hours is not None:
        settings.quiet_hours = request.quiet_hours

    await db.commit()
    await db.refresh(settings)

    return NotificationSettingsResponse(
        push_enabled=settings.push_enabled,
        push_likes=settings.push_likes,
        push_comments=settings.push_comments,
        push_follows=settings.push_follows,
        push_mentions=settings.push_mentions,
        push_ai_complete=settings.push_ai_complete,
        email_enabled=settings.email_enabled,
        email_digest_frequency=settings.email_digest_frequency,
        quiet_hours=settings.quiet_hours,
    )
