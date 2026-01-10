"""
Content Models

Unified content storage for AI-generated and manual content.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ContentType(str, Enum):
    """Types of content that can be generated."""

    VIDEO_SCRIPT = "video_script"
    SHORT_SCRIPT = "short_script"  # TikTok, Reels, Shorts
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"  # Twitter, LinkedIn, Facebook
    EMAIL = "email"
    PODCAST_SCRIPT = "podcast_script"
    CAROUSEL = "carousel"
    THREAD = "thread"  # Twitter/X threads


class ContentStatus(str, Enum):
    """Content generation status."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class ContentItem(Base, UUIDMixin, TimestampMixin):
    """
    Unified content item.

    Stores both AI-generated and manually created content
    with version history and platform-specific variations.
    """

    __tablename__ = "content_items"

    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Content type and status
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=ContentStatus.DRAFT.value,
        nullable=False,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # For video/audio content
    script: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Media attachments
    media_urls: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # AI generation metadata
    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    generation_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    generation_params: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Brand voice reference
    brand_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_voices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Template reference
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_templates.id", ondelete="SET NULL"),
        nullable=True,
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

    # Target platforms for publishing
    target_platforms: Mapped[list] = mapped_column(
        JSONB,
        default=list,  # ['tiktok', 'instagram', 'youtube', etc.]
        nullable=False,
    )

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Version tracking
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quality metrics
    quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ContentItem {self.id} ({self.content_type})>"


class BrandVoice(Base, UUIDMixin, TimestampMixin):
    """
    Brand voice profile for consistent content generation.

    Defines tone, style, and personality for AI content.
    """

    __tablename__ = "brand_voices"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Voice characteristics
    tone: Mapped[str] = mapped_column(
        String(50),
        default="professional",  # casual, professional, friendly, authoritative, etc.
        nullable=False,
    )

    personality_traits: Mapped[list] = mapped_column(
        JSONB,
        default=list,  # ['witty', 'informative', 'encouraging', etc.]
        nullable=False,
    )

    # Writing style
    sentence_style: Mapped[str] = mapped_column(
        String(50),
        default="mixed",  # short, long, mixed
        nullable=False,
    )

    vocabulary_level: Mapped[str] = mapped_column(
        String(50),
        default="general",  # simple, general, technical, academic
        nullable=False,
    )

    # Emoji and formatting preferences
    use_emojis: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    emoji_frequency: Mapped[str] = mapped_column(
        String(20),
        default="moderate",  # none, minimal, moderate, heavy
        nullable=False,
    )

    # Content preferences
    preferred_cta: Mapped[list] = mapped_column(
        JSONB,
        default=list,  # Preferred call-to-action phrases
        nullable=False,
    )

    avoid_words: Mapped[list] = mapped_column(
        JSONB,
        default=list,  # Words/phrases to avoid
        nullable=False,
    )

    # Sample content for style matching
    sample_content: Mapped[list] = mapped_column(
        JSONB,
        default=list,  # List of sample posts/content
        nullable=False,
    )

    # Active status
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BrandVoice {self.name}>"


class ContentTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Reusable content templates.

    Can be system templates or user-created.
    """

    __tablename__ = "content_templates"

    # Owner (null for system templates)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Template type
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Template content with variables
    template_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Variable definitions
    variables: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        # [{"name": "topic", "type": "string", "required": true, "description": "..."}]
        nullable=False,
    )

    # Target platforms
    target_platforms: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Categorization
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Usage stats
    use_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # System template flag
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ContentTemplate {self.name}>"


class GenerationJob(Base, UUIDMixin, TimestampMixin):
    """
    Track AI generation jobs.
    """

    __tablename__ = "generation_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Job type
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # content, video, audio, avatar, etc.

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, processing, completed, failed

    # Progress (0-100)
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Input parameters
    input_params: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Output
    output_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Related content
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Priority (higher = more urgent)
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<GenerationJob {self.id} ({self.job_type}: {self.status})>"
