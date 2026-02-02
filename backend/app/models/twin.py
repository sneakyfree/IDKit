"""
AI Twin Database Models

Models for AI Twin Lab: avatars, voice clones, and generated content.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AITwinRecord(Base, UUIDMixin, TimestampMixin):
    """AI Twin - Digital avatar with cloned voice."""

    __tablename__ = "ai_twins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Profile
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    status_message: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # External IDs
    heygen_avatar_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    elevenlabs_voice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Settings
    voice_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    avatar_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Quality scores
    voice_similarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    avatar_quality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Assets (JSON array of TwinAsset)
    assets: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Usage counters
    total_videos_generated: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )

    total_audio_generated: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )

    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AITwin {self.name}>"


class TwinContentRecord(Base, UUIDMixin, TimestampMixin):
    """Content generated using an AI Twin."""

    __tablename__ = "twin_content"

    twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content type
    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Input
    script: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )

    # Output URLs
    video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Metadata
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    resolution: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Pipeline status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    current_step: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    progress_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=0.0,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # External reference
    heygen_video_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<TwinContent {self.content_type}:{self.status}>"


class TwinCreationJob(Base, UUIDMixin, TimestampMixin):
    """Job tracking for async twin creation."""

    __tablename__ = "twin_creation_jobs"

    twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job status
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # External reference
    external_job_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Result
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<TwinCreationJob {self.job_type}:{self.status}>"
