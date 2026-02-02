"""
AI Twin Schemas

Schema definitions for the AI Twin Lab.
Digital avatar creation and voice cloning.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class TwinStatus(str, Enum):
    """Status of AI Twin creation."""
    PENDING = "pending"           # Waiting for assets
    PROCESSING_VOICE = "processing_voice"  # Creating voice clone
    PROCESSING_AVATAR = "processing_avatar"  # Creating avatar
    READY = "ready"               # Twin is ready to use
    FAILED = "failed"             # Creation failed
    DISABLED = "disabled"         # Temporarily disabled


class AssetType(str, Enum):
    """Types of Twin assets."""
    VIDEO_SAMPLE = "video_sample"
    AUDIO_SAMPLE = "audio_sample"
    AVATAR = "avatar"
    VOICE_CLONE = "voice_clone"


class TwinAsset(BaseModel):
    """An asset used by or generated for a Twin."""
    asset_id: UUID
    asset_type: AssetType
    
    # Storage
    url: Optional[str] = None
    storage_key: Optional[str] = None
    
    # External references
    external_id: Optional[str] = None  # HeyGen/ElevenLabs ID
    external_provider: Optional[str] = None  # heygen, elevenlabs
    
    # Metadata
    filename: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[float] = None
    format: Optional[str] = None
    
    # Status
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceSettings(BaseModel):
    """Voice synthesis settings for ElevenLabs."""
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    use_speaker_boost: bool = True


class AvatarSettings(BaseModel):
    """Avatar settings for HeyGen."""
    talking_style: str = "expressive"  # stable, expressive
    background_type: str = "transparent"  # transparent, solid, custom
    background_color: Optional[str] = None
    aspect_ratio: str = "16:9"  # 16:9, 9:16, 1:1


class AITwin(BaseModel):
    """
    AI Twin - Digital avatar with cloned voice.
    
    Represents a creator's digital clone that can generate
    video content automatically.
    """
    twin_id: UUID
    user_id: UUID
    
    # Profile
    name: str
    description: Optional[str] = None
    
    # Status
    status: TwinStatus = TwinStatus.PENDING
    status_message: Optional[str] = None
    
    # Assets
    assets: List[TwinAsset] = Field(default_factory=list)
    
    # External IDs
    heygen_avatar_id: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    
    # Settings
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    avatar_settings: AvatarSettings = Field(default_factory=AvatarSettings)
    
    # Quality metrics
    voice_similarity_score: Optional[float] = None  # 0.0-1.0
    avatar_quality_score: Optional[float] = None  # 0.0-1.0
    
    # Usage
    total_videos_generated: int = 0
    total_audio_generated: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ready_at: Optional[datetime] = None


class TwinContent(BaseModel):
    """Content generated using an AI Twin."""
    content_id: UUID
    twin_id: UUID
    user_id: UUID
    
    # Content type
    content_type: str  # video, audio, image
    
    # Script/input
    script: str
    language: str = "en"
    
    # Generated outputs
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Metadata
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    file_size: Optional[int] = None
    
    # Pipeline status
    status: str = "pending"  # pending, processing, completed, failed
    current_step: Optional[str] = None
    progress_percent: float = 0.0
    error: Optional[str] = None
    
    # External references
    heygen_video_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# ============== Request/Response Schemas ==============

class TwinCreateRequest(BaseModel):
    """Request to create a new AI Twin."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    voice_settings: Optional[VoiceSettings] = None
    avatar_settings: Optional[AvatarSettings] = None


class TwinCreateResponse(BaseModel):
    """Response after starting twin creation."""
    twin: AITwin
    upload_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="Pre-signed URLs for uploading video/audio samples"
    )


class TwinResponse(BaseModel):
    """Single twin response."""
    twin: AITwin


class TwinListResponse(BaseModel):
    """List of twins response."""
    twins: List[AITwin]
    total_count: int


class SampleUploadRequest(BaseModel):
    """Request to upload voice/video sample."""
    sample_type: AssetType
    filename: str
    content_type: str
    file_size: int


class SampleUploadResponse(BaseModel):
    """Response with upload URL."""
    upload_url: str
    asset_id: UUID
    expires_at: datetime


class GenerateContentRequest(BaseModel):
    """Request to generate content using AI Twin."""
    script: str = Field(..., min_length=1, max_length=5000)
    content_type: str = "video"  # video, audio
    language: str = "en"
    
    # Output settings
    resolution: str = "1080p"  # 720p, 1080p, 4k
    aspect_ratio: str = "16:9"
    
    # Voice override (optional)
    voice_settings: Optional[VoiceSettings] = None


class GenerateContentResponse(BaseModel):
    """Response after starting content generation."""
    content: TwinContent
    estimated_duration_seconds: int


class ContentListResponse(BaseModel):
    """List of generated content."""
    content: List[TwinContent]
    total_count: int


class PipelineStatusResponse(BaseModel):
    """Status of content generation pipeline."""
    content_id: UUID
    status: str
    current_step: Optional[str]
    progress_percent: float
    estimated_remaining_seconds: Optional[int]
    output_url: Optional[str] = None
