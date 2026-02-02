"""
Social Integration Models

External social media account connections and publishing.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Float, Boolean, Integer, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class SocialPlatform(str, Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"


class PostStatus(str, Enum):
    """Status of a social post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


# ==================== Social Accounts ====================


class SocialAccount(Base, UUIDMixin, TimestampMixin):
    """
    Connected social media account.

    Stores OAuth tokens and account metadata for each platform.
    """

    __tablename__ = "social_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Platform info
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OAuth tokens (encrypted in production)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)  # Primary account for this platform
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Platform-specific data
    account_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'personal', 'business', 'creator'
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)

    # Platform capabilities (varies by account type/tier)
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g., {"can_post_reels": true, "can_access_insights": true}

    # Rate limiting
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    posts: Mapped[List["SocialPost"]] = relationship(
        "SocialPost", back_populates="social_account", cascade="all, delete-orphan"
    )
    analytics: Mapped[List["SocialAnalytics"]] = relationship(
        "SocialAnalytics", back_populates="social_account", cascade="all, delete-orphan"
    )


# ==================== Social Posts ====================


class SocialPost(Base, UUIDMixin, TimestampMixin):
    """
    A post published or scheduled for a social platform.
    """

    __tablename__ = "social_posts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[list] = mapped_column(JSONB, default=list)
    hashtags: Mapped[list] = mapped_column(JSONB, default=list)
    mentions: Mapped[list] = mapped_column(JSONB, default=list)

    # Post type
    post_type: Mapped[str] = mapped_column(String(50), default="post")
    # 'post', 'story', 'reel', 'short', 'tweet', 'thread', 'article'

    # Platform post info
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status and scheduling
    status: Mapped[str] = mapped_column(
        String(20), default=PostStatus.DRAFT.value, nullable=False, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Engagement metrics (synced from platform)
    view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    save_count: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(BigInteger, default=0)

    # Source content (if derived from IDKit content - no FK to allow flexibility)
    source_content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    source_feed_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_posts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Platform-specific metadata
    platform_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    social_account: Mapped["SocialAccount"] = relationship("SocialAccount", back_populates="posts")


# ==================== Publishing Queue ====================


class PublishQueue(Base, UUIDMixin, TimestampMixin):
    """
    Queue for scheduled and pending posts.

    Processed by background workers.
    """

    __tablename__ = "publish_queue"

    social_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Queue management
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # 'pending', 'processing', 'completed', 'failed', 'cancelled'

    locked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Worker ID
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ==================== Social Comments ====================


class SocialComment(Base, UUIDMixin, TimestampMixin):
    """
    Comments on social posts (unified inbox).
    """

    __tablename__ = "social_comments"

    social_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Platform info
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_comment_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Comment content
    author_id: Mapped[str] = mapped_column(String(255), nullable=False)
    author_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    comment_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Threading
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_comments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Engagement
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)

    # Analysis
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'positive', 'neutral', 'negative'
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    is_question: Mapped[bool] = mapped_column(Boolean, default=False)

    # Management
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_replied: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    # Platform timestamp
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ==================== Direct Messages ====================


class SocialDMConversation(Base, UUIDMixin, TimestampMixin):
    """
    Direct message conversation (unified inbox).
    """

    __tablename__ = "social_dm_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Platform info
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Participant info
    participant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    participant_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    participant_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Conversation state
    is_unread: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Management
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[List["SocialDMMessage"]] = relationship(
        "SocialDMMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class SocialDMMessage(Base, UUIDMixin, TimestampMixin):
    """
    Individual direct message.
    """

    __tablename__ = "social_dm_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_dm_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Platform info
    platform_message_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Message content
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[list] = mapped_column(JSONB, default=list)

    # Direction
    is_outgoing: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    conversation: Mapped["SocialDMConversation"] = relationship("SocialDMConversation", back_populates="messages")


# ==================== Analytics ====================


class SocialAnalytics(Base, UUIDMixin, TimestampMixin):
    """
    Daily analytics snapshot per social account.
    """

    __tablename__ = "social_analytics"

    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time period
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Audience metrics
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    follower_change: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)

    # Engagement metrics
    total_reach: Mapped[int] = mapped_column(BigInteger, default=0)
    total_impressions: Mapped[int] = mapped_column(BigInteger, default=0)
    total_engagements: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Content metrics
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    stories_count: Mapped[int] = mapped_column(Integer, default=0)
    reels_count: Mapped[int] = mapped_column(Integer, default=0)

    # Interaction breakdown
    likes_received: Mapped[int] = mapped_column(Integer, default=0)
    comments_received: Mapped[int] = mapped_column(Integer, default=0)
    shares_received: Mapped[int] = mapped_column(Integer, default=0)
    saves_received: Mapped[int] = mapped_column(Integer, default=0)

    # Profile metrics
    profile_visits: Mapped[int] = mapped_column(Integer, default=0)
    website_clicks: Mapped[int] = mapped_column(Integer, default=0)

    # Demographics (JSONB for flexibility)
    audience_demographics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g., {"age_ranges": {...}, "genders": {...}, "locations": {...}}

    # Best performing content
    top_posts: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    social_account: Mapped["SocialAccount"] = relationship("SocialAccount", back_populates="analytics")


# ==================== Webhook Events ====================


class SocialWebhookEvent(Base, UUIDMixin, TimestampMixin):
    """
    Incoming webhook events from social platforms.
    """

    __tablename__ = "social_webhook_events"

    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event data
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # 'pending', 'processing', 'processed', 'failed', 'ignored'

    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Related entities (if identified)
    social_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    social_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_posts.id", ondelete="SET NULL"),
        nullable=True,
    )


# ==================== Daily Analytics ====================


class AnalyticsDaily(Base, UUIDMixin, TimestampMixin):
    """
    Daily analytics per social account and optionally per post.
    
    Used for time series analytics and trend analysis.
    """

    __tablename__ = "analytics_daily"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date for this analytics record
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Optional post-level tracking
    post_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Metrics
    impressions: Mapped[int] = mapped_column(BigInteger, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    watch_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    follower_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


# ==================== Backward Compatibility Aliases ====================
# These aliases support older code that uses shorter names

Comment = SocialComment
DmMessage = SocialDMMessage
DmConversation = SocialDMConversation
