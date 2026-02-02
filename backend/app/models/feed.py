"""
Feed Models

IDKit Social Community models for the internal social network.
Includes profiles, posts, interactions, and follows.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base, UUIDMixin, TimestampMixin):
    """
    User profile within IDKit ecosystem.

    Separate from User model to handle social features independently.
    Every user gets a profile when they sign up.
    """

    __tablename__ = "user_profiles"

    # Link to auth user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Profile info
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cover_image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Cached counts (updated via triggers/workers)
    follower_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    following_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    post_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Verification badge
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Content categorization
    niche_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    posts: Mapped[List["FeedPost"]] = relationship(
        "FeedPost",
        back_populates="author",
        lazy="dynamic",
        primaryjoin="UserProfile.user_id == foreign(FeedPost.user_id)",
    )

    def __repr__(self) -> str:
        return f"<UserProfile @{self.username}>"


class FeedPost(Base, UUIDMixin, TimestampMixin):
    """
    Internal feed post (content shared within IDKit).

    Supports multiple post types: video, image, text, carousel, podcast_clip.
    """

    __tablename__ = "feed_posts"

    # Author
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Content type
    post_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # 'video', 'image', 'text', 'carousel', 'podcast_clip'

    # Content
    content_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    media_urls: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Engagement metrics (for algorithm ranking)
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    like_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    comment_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    share_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    save_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Algorithm scoring (recalculated periodically)
    engagement_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    viral_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    trending_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    # Content metadata
    hashtags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    mentions: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # AI-generated indicator
    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Link to source content if created from Content Studio
    source_content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Visibility
    visibility: Mapped[str] = mapped_column(
        String(20),
        default="public",
        nullable=False,
    )  # 'public', 'followers', 'private'

    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    author: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="posts",
        foreign_keys=[user_id],
        primaryjoin="FeedPost.user_id == UserProfile.user_id",
    )

    likes: Mapped[List["FeedLike"]] = relationship(
        "FeedLike",
        back_populates="post",
        lazy="dynamic",
    )

    comments: Mapped[List["FeedComment"]] = relationship(
        "FeedComment",
        back_populates="post",
        lazy="dynamic",
    )

    saves: Mapped[List["FeedSave"]] = relationship(
        "FeedSave",
        back_populates="post",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<FeedPost {self.id} ({self.post_type})>"


class FeedLike(Base, UUIDMixin):
    """Like on a feed post."""

    __tablename__ = "feed_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_feed_like_post_user"),
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    post: Mapped["FeedPost"] = relationship(
        "FeedPost",
        back_populates="likes",
    )


class FeedComment(Base, UUIDMixin, TimestampMixin):
    """Comment on a feed post."""

    __tablename__ = "feed_comments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Nested comments support
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_comments.id", ondelete="CASCADE"),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    like_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    post: Mapped["FeedPost"] = relationship(
        "FeedPost",
        back_populates="comments",
    )

    replies: Mapped[List["FeedComment"]] = relationship(
        "FeedComment",
        back_populates="parent",
        lazy="dynamic",
    )

    parent: Mapped[Optional["FeedComment"]] = relationship(
        "FeedComment",
        back_populates="replies",
        remote_side="FeedComment.id",
    )


class FeedSave(Base, UUIDMixin):
    """Saved post (bookmark)."""

    __tablename__ = "feed_saves"
    __table_args__ = (
        UniqueConstraint(
            "post_id", "user_id", "collection_name", name="uq_feed_save_post_user_coll"
        ),
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    collection_name: Mapped[str] = mapped_column(
        String(100),
        default="Saved",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    post: Mapped["FeedPost"] = relationship(
        "FeedPost",
        back_populates="saves",
    )


class Follow(Base, UUIDMixin):
    """Follow relationship between users."""

    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_pair"),
    )

    follower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    following_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Hashtag(Base, UUIDMixin, TimestampMixin):
    """Hashtag for content discovery."""

    __tablename__ = "hashtags"

    tag: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    post_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    trending_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Hashtag #{self.tag}>"
