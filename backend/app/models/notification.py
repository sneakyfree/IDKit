"""
Notification Models

Handles all notification types for user interactions.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class NotificationType(str, Enum):
    """Types of notifications."""

    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    MENTION = "mention"
    REPLY = "reply"
    SHARE = "share"
    SYSTEM = "system"
    AI_COMPLETE = "ai_complete"  # AI generation completed
    POST_VIRAL = "post_viral"  # Post is going viral


class Notification(Base, UUIDMixin):
    """
    User notification.

    Supports various notification types with flexible metadata.
    """

    __tablename__ = "notifications"

    # Recipient
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Notification type
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Actor (who triggered the notification)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Related content
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        nullable=True,
    )

    comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_comments.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Notification content
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Additional metadata (flexible JSON for different notification types)
    notification_data: Mapped[dict] = mapped_column(
        "metadata",  # Keep original column name in DB for compatibility
        JSONB,
        default=dict,
        nullable=False,
    )

    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type} for user {self.user_id}>"


class NotificationSettings(Base, UUIDMixin):
    """
    User notification preferences.
    """

    __tablename__ = "notification_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Push notification settings
    push_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    push_likes: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    push_comments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    push_follows: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    push_mentions: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    push_ai_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Email notification settings
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    email_digest_frequency: Mapped[str] = mapped_column(
        String(20),
        default="daily",  # 'none', 'instant', 'daily', 'weekly'
        nullable=False,
    )

    # Quiet hours (stored as JSON)
    quiet_hours: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,  # {"enabled": false, "start": "22:00", "end": "08:00"}
        nullable=False,
    )
