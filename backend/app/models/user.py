"""
User Model

Core user authentication model for IDKit.
Users authenticate via social login only (Google, Apple, etc.).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.feed import UserProfile
    from app.models.payout import ConnectAccount
    from app.models.schedule import ScheduledPost


class User(Base, UUIDMixin, TimestampMixin):
    """
    Core user model for authentication.

    Note: Profile information is stored in UserProfile for separation
    of concerns between auth and social features.
    """

    __tablename__ = "users"

    # Email from OAuth provider
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # OAuth provider info (nullable for email/password users)
    oauth_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # 'google', 'apple', 'email', etc.

    oauth_provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )  # Provider's user ID

    # Password hash (for email/password auth; nullable for OAuth-only users)
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Optional name from OAuth
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Profile picture from OAuth
    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Subscription tier
    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
    )  # 'free', 'pro', 'enterprise'

    # Last login tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        lazy="joined",
    )

    connect_account: Mapped["ConnectAccount"] = relationship(
        "ConnectAccount",
        back_populates="user",
        uselist=False,
        lazy="noload",
    )

    # Scheduled posts relationship (required by ScheduledPost.user back_populates)
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost",
        back_populates="user",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserSettings(Base, UUIDMixin, TimestampMixin):
    """User preferences and settings."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Notification preferences
    notification_preferences: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # Privacy settings
    privacy_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # UI preferences
    theme: Mapped[str] = mapped_column(
        String(20),
        default="system",
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )


class DataRequest(Base, UUIDMixin, TimestampMixin):
    """GDPR data request (export, deletion, access)."""

    __tablename__ = "data_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    request_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'export', 'delete', 'access'

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # 'pending', 'processing', 'completed', 'failed'

    categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    download_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class ConsentLog(Base, UUIDMixin, TimestampMixin):
    """Track user consent for GDPR compliance."""

    __tablename__ = "consent_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    consent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # 'marketing', 'analytics', 'personalization', 'third_party'

    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    granted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[str] = mapped_column(
        String(20),
        default="1.0",
        nullable=False,
    )
