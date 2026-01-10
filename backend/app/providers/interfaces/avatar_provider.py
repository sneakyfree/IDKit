"""
Avatar Provider Interface

Abstract interface for avatar generation services (HeyGen, self-hosted, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional
import uuid


class AvatarJobStatus(str, Enum):
    """Status states for avatar jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AvatarTrainingConfig:
    """Configuration for avatar training."""
    photo_urls: list[str]
    video_urls: list[str] = field(default_factory=list)
    name: str = "My Avatar"

    # Appearance settings
    background_type: str = "solid"  # 'solid', 'transparent', 'image'
    background_color: str = "#ffffff"

    # Animation settings
    enable_gestures: bool = True
    enable_eye_contact: bool = True
    enable_head_movement: bool = True

    # Provider-specific extras
    extras: dict = field(default_factory=dict)


@dataclass
class AvatarGenerationConfig:
    """Configuration for video generation with avatar."""
    avatar_id: str

    # Input (one of these required)
    text: Optional[str] = None
    audio_url: Optional[str] = None

    # Voice settings (if using text input)
    voice_id: Optional[str] = None

    # Video settings
    resolution: str = "1080p"
    aspect_ratio: str = "16:9"  # '16:9', '9:16', '1:1'

    # Background
    background_type: str = "solid"
    background_color: str = "#ffffff"
    background_url: Optional[str] = None

    # Animation
    emotion: str = "neutral"
    gesture_intensity: str = "moderate"

    # Provider-specific extras
    extras: dict = field(default_factory=dict)


@dataclass
class AvatarTrainingResult:
    """Result of avatar training."""
    avatar_id: str
    status: AvatarJobStatus
    preview_url: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class AvatarGenerationResult:
    """Result of avatar video generation."""
    job_id: str
    status: AvatarJobStatus
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    progress: int = 0  # 0-100
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class LiveSessionConfig:
    """Configuration for live avatar streaming."""
    avatar_id: str
    voice_id: Optional[str] = None
    quality: str = "high"
    session_duration_limit: int = 3600  # seconds
    extras: dict = field(default_factory=dict)


@dataclass
class LiveSession:
    """Active live streaming session."""
    session_id: str
    rtmp_url: str
    stream_key: str
    playback_url: str
    status: str  # 'starting', 'active', 'ended'
    avatar_id: str
    created_at: str
    metadata: dict = field(default_factory=dict)


class AvatarProvider(ABC):
    """
    Abstract interface for avatar generation providers.

    Implement this interface to add support for new avatar services
    (HeyGen, self-hosted SadTalker, etc.)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def supports_live_streaming(self) -> bool:
        """Whether this provider supports live avatar streaming."""
        pass

    @property
    @abstractmethod
    def supports_custom_backgrounds(self) -> bool:
        """Whether this provider supports custom backgrounds."""
        pass

    @abstractmethod
    async def create_avatar(
        self,
        config: AvatarTrainingConfig,
    ) -> AvatarTrainingResult:
        """
        Create/train a new avatar from uploaded media.

        Args:
            config: Training configuration with media URLs and settings

        Returns:
            Training result with avatar ID
        """
        pass

    @abstractmethod
    async def get_avatar_status(
        self,
        avatar_id: str,
    ) -> AvatarTrainingResult:
        """
        Get the current status of an avatar (training progress).

        Args:
            avatar_id: The avatar ID to check

        Returns:
            Current training status
        """
        pass

    @abstractmethod
    async def delete_avatar(
        self,
        avatar_id: str,
    ) -> bool:
        """
        Delete an avatar from the provider.

        Args:
            avatar_id: The avatar ID to delete

        Returns:
            True if successfully deleted
        """
        pass

    @abstractmethod
    async def generate_video(
        self,
        config: AvatarGenerationConfig,
    ) -> AvatarGenerationResult:
        """
        Generate a video with the avatar speaking.

        Args:
            config: Generation configuration with text/audio and settings

        Returns:
            Generation result with job ID
        """
        pass

    @abstractmethod
    async def get_video_status(
        self,
        job_id: str,
    ) -> AvatarGenerationResult:
        """
        Get the status of a video generation job.

        Args:
            job_id: The job ID to check

        Returns:
            Current generation status
        """
        pass

    async def stream_video_progress(
        self,
        job_id: str,
        poll_interval: float = 2.0,
    ) -> AsyncIterator[AvatarGenerationResult]:
        """
        Stream video generation progress updates.

        Default implementation polls get_video_status.
        Override for webhook-based providers.

        Args:
            job_id: The job ID to monitor
            poll_interval: Seconds between status checks

        Yields:
            Progress updates until completion
        """
        import asyncio

        while True:
            result = await self.get_video_status(job_id)
            yield result

            if result.status in (AvatarJobStatus.COMPLETED, AvatarJobStatus.FAILED):
                break

            await asyncio.sleep(poll_interval)

    # Optional: Live streaming methods
    async def start_live_session(
        self,
        config: LiveSessionConfig,
    ) -> LiveSession:
        """
        Start a live avatar streaming session.

        Only available if supports_live_streaming is True.
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support live streaming"
        )

    async def send_live_text(
        self,
        session_id: str,
        text: str,
    ) -> bool:
        """
        Send text for the live avatar to speak.
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support live streaming"
        )

    async def end_live_session(
        self,
        session_id: str,
    ) -> dict:
        """
        End a live streaming session.

        Returns session metadata (duration, recording URL if available).
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support live streaming"
        )

    async def validate_media(
        self,
        media_urls: list[str],
        media_type: str,
    ) -> dict:
        """
        Validate media files for avatar training.

        Args:
            media_urls: URLs of media to validate
            media_type: 'photo' or 'video'

        Returns:
            Validation results with quality scores and issues
        """
        # Default implementation - providers can override
        return {
            "valid": True,
            "issues": [],
            "quality_scores": [0.8] * len(media_urls),
        }
