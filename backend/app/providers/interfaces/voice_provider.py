"""
Voice Provider Interface

Abstract interface for voice cloning/synthesis services (ElevenLabs, self-hosted, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional
import uuid


class VoiceJobStatus(str, Enum):
    """Status states for voice jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VoiceCloningConfig:
    """Configuration for voice cloning."""
    audio_urls: list[str]  # Audio samples for cloning
    name: str = "My Voice"
    description: Optional[str] = None

    # Voice characteristics hints
    gender: Optional[str] = None  # 'male', 'female', 'neutral'
    age: Optional[str] = None  # 'young', 'middle', 'old'
    accent: Optional[str] = None  # 'american', 'british', etc.

    # Quality settings
    remove_background_noise: bool = True
    enhance_quality: bool = True

    # Provider-specific extras
    extras: dict = field(default_factory=dict)


@dataclass
class VoiceSynthesisConfig:
    """Configuration for speech synthesis."""
    voice_id: str
    text: str

    # Voice settings
    stability: float = 0.5  # 0-1, higher = more consistent
    similarity_boost: float = 0.75  # 0-1, higher = more like original
    style: float = 0.0  # 0-1, style exaggeration

    # Speech settings
    speaking_rate: float = 1.0  # 0.5-2.0
    pitch: float = 0.0  # Adjustment in semitones

    # Output settings
    output_format: str = "mp3_44100_128"  # Format specification
    sample_rate: int = 44100

    # Language (for multilingual voices)
    language: str = "en"

    # Provider-specific extras
    extras: dict = field(default_factory=dict)


@dataclass
class VoiceCloningResult:
    """Result of voice cloning."""
    voice_id: str
    status: VoiceJobStatus
    preview_url: Optional[str] = None
    samples_used: int = 0
    quality_score: Optional[float] = None  # 0-1
    metadata: dict = field(default_factory=dict)


@dataclass
class VoiceSynthesisResult:
    """Result of speech synthesis."""
    audio_url: Optional[str] = None
    audio_data: Optional[bytes] = None  # For streaming
    duration_seconds: Optional[float] = None
    character_count: int = 0
    cost: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class VoiceInfo:
    """Information about a voice."""
    voice_id: str
    name: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    is_cloned: bool = True
    languages: list[str] = field(default_factory=lambda: ["en"])
    gender: Optional[str] = None
    age: Optional[str] = None
    use_count: int = 0
    created_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class VoiceProvider(ABC):
    """
    Abstract interface for voice cloning/synthesis providers.

    Implement this interface to add support for new voice services
    (ElevenLabs, self-hosted Tortoise-TTS, etc.)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def supports_voice_cloning(self) -> bool:
        """Whether this provider supports voice cloning."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming audio generation."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        """List of supported language codes."""
        pass

    @property
    def max_text_length(self) -> int:
        """Maximum text length per request."""
        return 5000

    @abstractmethod
    async def clone_voice(
        self,
        config: VoiceCloningConfig,
    ) -> VoiceCloningResult:
        """
        Clone a voice from audio samples.

        Args:
            config: Cloning configuration with audio URLs and settings

        Returns:
            Cloning result with voice ID
        """
        pass

    @abstractmethod
    async def get_voice(
        self,
        voice_id: str,
    ) -> VoiceInfo:
        """
        Get information about a voice.

        Args:
            voice_id: The voice ID to look up

        Returns:
            Voice information
        """
        pass

    @abstractmethod
    async def list_voices(
        self,
    ) -> list[VoiceInfo]:
        """
        List all available voices (cloned and preset).

        Returns:
            List of voice information
        """
        pass

    @abstractmethod
    async def delete_voice(
        self,
        voice_id: str,
    ) -> bool:
        """
        Delete a cloned voice.

        Args:
            voice_id: The voice ID to delete

        Returns:
            True if successfully deleted
        """
        pass

    @abstractmethod
    async def synthesize_speech(
        self,
        config: VoiceSynthesisConfig,
    ) -> VoiceSynthesisResult:
        """
        Generate speech from text.

        Args:
            config: Synthesis configuration with text and voice settings

        Returns:
            Synthesis result with audio URL or data
        """
        pass

    async def synthesize_speech_stream(
        self,
        config: VoiceSynthesisConfig,
    ) -> AsyncIterator[bytes]:
        """
        Stream speech generation in chunks.

        Only available if supports_streaming is True.

        Args:
            config: Synthesis configuration

        Yields:
            Audio data chunks
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support streaming synthesis"
        )

    async def validate_audio_samples(
        self,
        audio_urls: list[str],
    ) -> dict:
        """
        Validate audio samples for voice cloning.

        Args:
            audio_urls: URLs of audio files to validate

        Returns:
            Validation results with quality scores and issues
        """
        # Default implementation - providers can override
        return {
            "valid": True,
            "issues": [],
            "quality_scores": [0.8] * len(audio_urls),
            "total_duration_seconds": 0,
            "minimum_duration_met": True,
        }

    async def estimate_cost(
        self,
        text: str,
        voice_id: str,
    ) -> dict:
        """
        Estimate the cost of synthesizing text.

        Args:
            text: Text to synthesize
            voice_id: Voice to use

        Returns:
            Cost estimate with character count and pricing
        """
        char_count = len(text)
        return {
            "character_count": char_count,
            "estimated_cost": None,  # Provider-specific
            "estimated_duration_seconds": char_count / 15,  # ~15 chars/sec avg
        }

    async def get_usage(self) -> dict:
        """
        Get current usage statistics.

        Returns:
            Usage info (characters used, limit, reset date)
        """
        return {
            "characters_used": 0,
            "character_limit": None,
            "reset_date": None,
        }
