"""
Podcast Models

"Insta Podcast" - End-to-end podcast production with AI support.
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


class PodcastStatus(str, Enum):
    """Podcast/episode status."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Podcast(Base, UUIDMixin, TimestampMixin):
    """
    Podcast show (series).

    Contains metadata and settings for a podcast series.
    """

    __tablename__ = "podcasts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Basic info
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cover_art_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
    )

    # Host configuration
    host_type: Mapped[str] = mapped_column(
        String(20),
        default="user",  # 'user', 'ai_twin', 'both'
        nullable=False,
    )

    ai_twin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,  # Will link to AI Twin table when implemented
    )

    brand_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_voices.id", ondelete="SET NULL"),
        nullable=True,
    )

    # RSS/Distribution
    rss_feed_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    itunes_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    spotify_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    youtube_playlist_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Intro/Outro settings
    default_intro_audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    default_outro_audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    intro_script: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    outro_script: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Stats
    episode_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    subscriber_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_plays: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    episodes: Mapped[List["PodcastEpisode"]] = relationship(
        "PodcastEpisode",
        back_populates="podcast",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Podcast {self.title}>"


class PodcastEpisode(Base, UUIDMixin, TimestampMixin):
    """
    Individual podcast episode.

    Supports both manual recording and AI generation.
    """

    __tablename__ = "podcast_episodes"

    podcast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("podcasts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Episode info
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    episode_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    season_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Content
    script: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    show_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Generated assets
    audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    waveform_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Host configuration
    host_type: Mapped[str] = mapped_column(
        String(20),
        default="user",  # 'user', 'ai_twin', 'live'
        nullable=False,
    )

    ai_twin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Chapters/timestamps
    chapters: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        # [{"title": "Intro", "start": 0, "end": 60}, ...]
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=PodcastStatus.DRAFT.value,
        nullable=False,
        index=True,
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Publishing
    publish_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Analytics
    play_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    completion_rate: Mapped[float | None] = mapped_column(
        Float,
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

    # Relationships
    podcast: Mapped["Podcast"] = relationship(
        "Podcast",
        back_populates="episodes",
    )

    clips: Mapped[List["PodcastClip"]] = relationship(
        "PodcastClip",
        back_populates="episode",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<PodcastEpisode {self.title}>"


class PodcastClip(Base, UUIDMixin, TimestampMixin):
    """
    Short-form clip extracted from podcast episode.

    Auto-generated for social media distribution.
    """

    __tablename__ = "podcast_clips"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("podcast_episodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Clip info
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timing
    start_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Generated assets
    audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Auto-generated content
    captions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quote_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Target platforms
    target_platforms: Mapped[list] = mapped_column(
        JSONB,
        default=["tiktok", "reels", "shorts"],
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=PodcastStatus.DRAFT.value,
        nullable=False,
    )

    # Publishing
    published_platforms: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Relationships
    episode: Mapped["PodcastEpisode"] = relationship(
        "PodcastEpisode",
        back_populates="clips",
    )

    @property
    def duration_seconds(self) -> int:
        return self.end_time_seconds - self.start_time_seconds

    def __repr__(self) -> str:
        return f"<PodcastClip {self.id}>"


class PodcastLiveSession(Base, UUIDMixin, TimestampMixin):
    """
    Live podcast recording session.
    """

    __tablename__ = "podcast_live_sessions"

    podcast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("podcasts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Scheduling
    scheduled_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Streaming
    stream_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rtmp_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    playback_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Recording
    recording_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("podcast_episodes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",  # 'scheduled', 'live', 'ended', 'cancelled'
        nullable=False,
    )

    viewer_count_peak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PodcastLiveSession {self.title}>"
