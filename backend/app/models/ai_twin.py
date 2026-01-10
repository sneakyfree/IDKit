"""
AI Twin Models

Digital clone/avatar system with voice and appearance configuration.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Float, Boolean, Integer, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TwinStatus(str, Enum):
    """AI Twin status states."""
    DRAFT = "draft"
    TRAINING = "training"
    READY = "ready"
    ERROR = "error"


class TrainingJobStatus(str, Enum):
    """Training job status states."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaType(str, Enum):
    """Media upload types."""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"


# ==================== AI Twin ====================


class AiTwin(Base, UUIDMixin, TimestampMixin):
    """
    Main AI Twin entity.

    Combines avatar (visual) and voice (audio) into a digital clone.
    """

    __tablename__ = "ai_twins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=TwinStatus.DRAFT.value, nullable=False
    )

    # Avatar (visual appearance)
    avatar_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # External provider ID
    avatar_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'heygen', 'self_hosted'
    avatar_preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_status: Mapped[str] = mapped_column(
        String(20), default=TwinStatus.DRAFT.value, nullable=False
    )

    # Voice (audio appearance)
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # External provider ID
    voice_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'elevenlabs', 'self_hosted'
    voice_preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_status: Mapped[str] = mapped_column(
        String(20), default=TwinStatus.DRAFT.value, nullable=False
    )

    # Personality configuration (for AI responses)
    personality_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    communication_style: Mapped[str] = mapped_column(String(50), default="conversational")

    # Settings
    default_language: Mapped[str] = mapped_column(String(10), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage stats
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    audio_count: Mapped[int] = mapped_column(Integer, default=0)
    total_minutes_generated: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    media_uploads: Mapped[List["TwinMediaUpload"]] = relationship(
        "TwinMediaUpload", back_populates="ai_twin", cascade="all, delete-orphan"
    )
    avatar_config: Mapped[Optional["AvatarConfig"]] = relationship(
        "AvatarConfig", back_populates="ai_twin", uselist=False, cascade="all, delete-orphan"
    )
    voice_config: Mapped[Optional["VoiceConfig"]] = relationship(
        "VoiceConfig", back_populates="ai_twin", uselist=False, cascade="all, delete-orphan"
    )
    training_jobs: Mapped[List["TwinTrainingJob"]] = relationship(
        "TwinTrainingJob", back_populates="ai_twin", cascade="all, delete-orphan"
    )


# ==================== Media Uploads ====================


class TwinMediaUpload(Base, UUIDMixin, TimestampMixin):
    """
    Media files uploaded for AI Twin training.

    Can be photos (for avatar), videos (for avatar motion), or audio (for voice).
    """

    __tablename__ = "twin_media_uploads"

    ai_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Media info
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'photo', 'video', 'audio'
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # 'avatar_training', 'voice_training'

    # File details
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)  # For audio/video

    # Quality analysis
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1 score
    quality_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # List of issues found
    face_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    face_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    ai_twin: Mapped["AiTwin"] = relationship("AiTwin", back_populates="media_uploads")


# ==================== Avatar Configuration ====================


class AvatarConfig(Base, UUIDMixin, TimestampMixin):
    """
    Avatar appearance configuration.

    Stores settings for how the AI avatar should look and behave.
    """

    __tablename__ = "avatar_configs"

    ai_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Appearance settings
    background_type: Mapped[str] = mapped_column(String(50), default="solid")  # 'solid', 'image', 'video', 'transparent'
    background_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    background_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Framing
    camera_angle: Mapped[str] = mapped_column(String(50), default="front")  # 'front', 'slight_left', 'slight_right'
    zoom_level: Mapped[str] = mapped_column(String(50), default="medium")  # 'close', 'medium', 'wide'

    # Animation style
    emotion_default: Mapped[str] = mapped_column(String(50), default="neutral")  # 'neutral', 'happy', 'serious'
    gesture_intensity: Mapped[str] = mapped_column(String(50), default="moderate")  # 'minimal', 'moderate', 'expressive'
    eye_contact: Mapped[bool] = mapped_column(Boolean, default=True)
    head_movement: Mapped[bool] = mapped_column(Boolean, default=True)

    # Output settings
    default_resolution: Mapped[str] = mapped_column(String(20), default="1080p")  # '720p', '1080p', '4k'
    default_aspect_ratio: Mapped[str] = mapped_column(String(20), default="16:9")  # '16:9', '9:16', '1:1'

    # Provider-specific settings
    provider_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    ai_twin: Mapped["AiTwin"] = relationship("AiTwin", back_populates="avatar_config")


# ==================== Voice Configuration ====================


class VoiceConfig(Base, UUIDMixin, TimestampMixin):
    """
    Voice cloning configuration.

    Stores settings for how the AI voice should sound.
    """

    __tablename__ = "voice_configs"

    ai_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Voice characteristics
    stability: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1, higher = more consistent
    similarity_boost: Mapped[float] = mapped_column(Float, default=0.75)  # 0-1, higher = more like original
    style: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1, style exaggeration

    # Speech settings
    speaking_rate: Mapped[float] = mapped_column(Float, default=1.0)  # 0.5-2.0
    pitch: Mapped[float] = mapped_column(Float, default=0.0)  # -20 to 20 semitones

    # Language settings
    primary_language: Mapped[str] = mapped_column(String(10), default="en")
    supported_languages: Mapped[list] = mapped_column(JSONB, default=list)

    # Audio output settings
    output_format: Mapped[str] = mapped_column(String(20), default="mp3_44100_128")
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100)

    # Provider-specific settings
    provider_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    ai_twin: Mapped["AiTwin"] = relationship("AiTwin", back_populates="voice_config")


# ==================== Training Jobs ====================


class TwinTrainingJob(Base, UUIDMixin, TimestampMixin):
    """
    Training job for AI Twin avatar or voice.

    Tracks GPU job status and progress.
    """

    __tablename__ = "twin_training_jobs"

    ai_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Job type
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'avatar_training', 'voice_training'

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default=TrainingJobStatus.PENDING.value, nullable=False, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Provider info
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # GPU info (for self-hosted)
    gpu_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'vastai', 'runpod', 'lambda'
    gpu_instance_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gpu_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_completion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Results
    result_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # External ID (avatar_id or voice_id)
    result_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    input_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    ai_twin: Mapped["AiTwin"] = relationship("AiTwin", back_populates="training_jobs")


# ==================== Generated Assets ====================


class TwinGeneratedAsset(Base, UUIDMixin, TimestampMixin):
    """
    Assets generated by AI Twin (videos, audio clips).
    """

    __tablename__ = "twin_generated_assets"

    ai_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Asset type
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'video', 'audio'

    # Generation input
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Output
    output_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="ready", nullable=False)

    # Provider info
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generation_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Settings used
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
