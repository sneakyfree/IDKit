"""
AI Twin API Endpoints

Digital clone creation, training, and content generation.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, desc

from app.dependencies import DB, CurrentUser
from app.models.ai_twin import (
    AiTwin,
    TwinMediaUpload,
    AvatarConfig,
    VoiceConfig,
    TwinTrainingJob,
    TwinGeneratedAsset,
    TwinStatus,
    TrainingJobStatus,
)
from app.services.twin import AiTwinService

router = APIRouter()


# ==================== Schemas ====================


class CreateTwinRequest(BaseModel):
    """Request to create a new AI Twin."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    personality_prompt: Optional[str] = None
    communication_style: str = Field(default="conversational")
    default_language: str = Field(default="en")


class TwinResponse(BaseModel):
    """AI Twin response."""

    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    avatar_status: str
    voice_status: str
    avatar_preview_url: Optional[str]
    voice_preview_url: Optional[str]
    avatar_provider: Optional[str]
    voice_provider: Optional[str]
    personality_prompt: Optional[str]
    communication_style: str
    default_language: str
    video_count: int
    audio_count: int
    total_minutes_generated: float
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AddMediaRequest(BaseModel):
    """Request to add media for training."""

    media_type: str = Field(description="'photo', 'video', or 'audio'")
    purpose: str = Field(description="'avatar_training', 'avatar_video_training', or 'voice_training'")
    file_url: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float] = None


class MediaResponse(BaseModel):
    """Media upload response."""

    id: uuid.UUID
    ai_twin_id: uuid.UUID
    media_type: str
    purpose: str
    file_url: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float]
    quality_score: Optional[float]
    is_approved: bool
    created_at: str

    class Config:
        from_attributes = True


class TrainingJobResponse(BaseModel):
    """Training job response."""

    id: uuid.UUID
    ai_twin_id: uuid.UUID
    job_type: str
    status: str
    progress: int
    provider: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_completion: Optional[str]
    result_url: Optional[str]
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class GenerateVideoRequest(BaseModel):
    """Request to generate video with AI Twin."""

    text: Optional[str] = Field(default=None, max_length=5000)
    audio_url: Optional[str] = None
    resolution: str = Field(default="1080p")
    aspect_ratio: str = Field(default="16:9")
    background_color: str = Field(default="#ffffff")


class SynthesizeSpeechRequest(BaseModel):
    """Request to synthesize speech."""

    text: str = Field(min_length=1, max_length=5000)
    stability: float = Field(default=0.5, ge=0, le=1)
    similarity_boost: float = Field(default=0.75, ge=0, le=1)


class GeneratedAssetResponse(BaseModel):
    """Generated asset response."""

    id: uuid.UUID
    ai_twin_id: uuid.UUID
    asset_type: str
    input_text: Optional[str]
    output_url: str
    thumbnail_url: Optional[str]
    duration_seconds: float
    status: str
    provider: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AvatarConfigRequest(BaseModel):
    """Request to update avatar configuration."""

    background_type: Optional[str] = None
    background_color: Optional[str] = None
    background_url: Optional[str] = None
    camera_angle: Optional[str] = None
    zoom_level: Optional[str] = None
    emotion_default: Optional[str] = None
    gesture_intensity: Optional[str] = None
    eye_contact: Optional[bool] = None
    head_movement: Optional[bool] = None
    default_resolution: Optional[str] = None
    default_aspect_ratio: Optional[str] = None


class VoiceConfigRequest(BaseModel):
    """Request to update voice configuration."""

    stability: Optional[float] = Field(default=None, ge=0, le=1)
    similarity_boost: Optional[float] = Field(default=None, ge=0, le=1)
    style: Optional[float] = Field(default=None, ge=0, le=1)
    speaking_rate: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(default=None, ge=-20, le=20)
    primary_language: Optional[str] = None


# ==================== Twin Endpoints ====================


@router.post("", response_model=TwinResponse, status_code=status.HTTP_201_CREATED)
async def create_twin(
    request: CreateTwinRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new AI Twin."""
    service = AiTwinService(db)

    twin = await service.create_twin(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        personality_prompt=request.personality_prompt,
        communication_style=request.communication_style,
        default_language=request.default_language,
    )

    return TwinResponse(
        id=twin.id,
        name=twin.name,
        description=twin.description,
        status=twin.status,
        avatar_status=twin.avatar_status,
        voice_status=twin.voice_status,
        avatar_preview_url=twin.avatar_preview_url,
        voice_preview_url=twin.voice_preview_url,
        avatar_provider=twin.avatar_provider,
        voice_provider=twin.voice_provider,
        personality_prompt=twin.personality_prompt,
        communication_style=twin.communication_style,
        default_language=twin.default_language,
        video_count=twin.video_count,
        audio_count=twin.audio_count,
        total_minutes_generated=twin.total_minutes_generated,
        is_active=twin.is_active,
        created_at=twin.created_at.isoformat(),
        updated_at=twin.updated_at.isoformat(),
    )


@router.get("", response_model=List[TwinResponse])
async def list_twins(
    db: DB,
    current_user: CurrentUser,
):
    """List user's AI Twins."""
    service = AiTwinService(db)
    twins = await service.list_twins(current_user.id)

    return [
        TwinResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            status=t.status,
            avatar_status=t.avatar_status,
            voice_status=t.voice_status,
            avatar_preview_url=t.avatar_preview_url,
            voice_preview_url=t.voice_preview_url,
            avatar_provider=t.avatar_provider,
            voice_provider=t.voice_provider,
            personality_prompt=t.personality_prompt,
            communication_style=t.communication_style,
            default_language=t.default_language,
            video_count=t.video_count,
            audio_count=t.audio_count,
            total_minutes_generated=t.total_minutes_generated,
            is_active=t.is_active,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
        )
        for t in twins
    ]


@router.get("/{twin_id}", response_model=TwinResponse)
async def get_twin(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get AI Twin details."""
    service = AiTwinService(db)
    twin = await service.get_twin(twin_id, current_user.id)

    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Twin not found",
        )

    return TwinResponse(
        id=twin.id,
        name=twin.name,
        description=twin.description,
        status=twin.status,
        avatar_status=twin.avatar_status,
        voice_status=twin.voice_status,
        avatar_preview_url=twin.avatar_preview_url,
        voice_preview_url=twin.voice_preview_url,
        avatar_provider=twin.avatar_provider,
        voice_provider=twin.voice_provider,
        personality_prompt=twin.personality_prompt,
        communication_style=twin.communication_style,
        default_language=twin.default_language,
        video_count=twin.video_count,
        audio_count=twin.audio_count,
        total_minutes_generated=twin.total_minutes_generated,
        is_active=twin.is_active,
        created_at=twin.created_at.isoformat(),
        updated_at=twin.updated_at.isoformat(),
    )


@router.delete("/{twin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_twin(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete an AI Twin."""
    service = AiTwinService(db)
    deleted = await service.delete_twin(twin_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Twin not found",
        )


# ==================== Media Endpoints ====================


@router.post("/{twin_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def add_media(
    twin_id: uuid.UUID,
    request: AddMediaRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Add media for AI Twin training."""
    service = AiTwinService(db)

    try:
        media = await service.add_media(
            twin_id=twin_id,
            user_id=current_user.id,
            media_type=request.media_type,
            purpose=request.purpose,
            file_url=request.file_url,
            file_name=request.file_name,
            file_size_bytes=request.file_size_bytes,
            mime_type=request.mime_type,
            duration_seconds=request.duration_seconds,
        )

        return MediaResponse(
            id=media.id,
            ai_twin_id=media.ai_twin_id,
            media_type=media.media_type,
            purpose=media.purpose,
            file_url=media.file_url,
            file_name=media.file_name,
            file_size_bytes=media.file_size_bytes,
            mime_type=media.mime_type,
            duration_seconds=media.duration_seconds,
            quality_score=media.quality_score,
            is_approved=media.is_approved,
            created_at=media.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{twin_id}/media", response_model=List[MediaResponse])
async def list_media(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    purpose: Optional[str] = Query(default=None),
):
    """List media uploads for an AI Twin."""
    # Verify ownership
    result = await db.execute(
        select(AiTwin).where(
            AiTwin.id == twin_id,
            AiTwin.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Twin not found",
        )

    query = select(TwinMediaUpload).where(
        TwinMediaUpload.ai_twin_id == twin_id
    )
    if purpose:
        query = query.where(TwinMediaUpload.purpose == purpose)

    result = await db.execute(query.order_by(desc(TwinMediaUpload.created_at)))
    media_list = result.scalars().all()

    return [
        MediaResponse(
            id=m.id,
            ai_twin_id=m.ai_twin_id,
            media_type=m.media_type,
            purpose=m.purpose,
            file_url=m.file_url,
            file_name=m.file_name,
            file_size_bytes=m.file_size_bytes,
            mime_type=m.mime_type,
            duration_seconds=m.duration_seconds,
            quality_score=m.quality_score,
            is_approved=m.is_approved,
            created_at=m.created_at.isoformat(),
        )
        for m in media_list
    ]


@router.post("/{twin_id}/media/{media_id}/approve", response_model=dict)
async def approve_media(
    twin_id: uuid.UUID,
    media_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    quality_score: Optional[float] = Query(default=None, ge=0, le=1),
):
    """Approve media for training."""
    service = AiTwinService(db)
    approved = await service.approve_media(media_id, current_user.id, quality_score)

    if not approved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )

    return {"status": "approved"}


# ==================== Training Endpoints ====================


@router.post("/{twin_id}/avatar/train", response_model=TrainingJobResponse)
async def train_avatar(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Start avatar training for AI Twin."""
    service = AiTwinService(db)

    try:
        job = await service.train_avatar(twin_id, current_user.id)

        return TrainingJobResponse(
            id=job.id,
            ai_twin_id=job.ai_twin_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            provider=job.provider,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            estimated_completion=job.estimated_completion.isoformat() if job.estimated_completion else None,
            result_url=job.result_url,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{twin_id}/voice/train", response_model=TrainingJobResponse)
async def train_voice(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Start voice cloning for AI Twin."""
    service = AiTwinService(db)

    try:
        job = await service.train_voice(twin_id, current_user.id)

        return TrainingJobResponse(
            id=job.id,
            ai_twin_id=job.ai_twin_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            provider=job.provider,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            estimated_completion=job.estimated_completion.isoformat() if job.estimated_completion else None,
            result_url=job.result_url,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{twin_id}/jobs", response_model=List[TrainingJobResponse])
async def list_training_jobs(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """List training jobs for an AI Twin."""
    # Verify ownership
    result = await db.execute(
        select(AiTwin).where(
            AiTwin.id == twin_id,
            AiTwin.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Twin not found",
        )

    result = await db.execute(
        select(TwinTrainingJob)
        .where(TwinTrainingJob.ai_twin_id == twin_id)
        .order_by(desc(TwinTrainingJob.created_at))
    )
    jobs = result.scalars().all()

    return [
        TrainingJobResponse(
            id=j.id,
            ai_twin_id=j.ai_twin_id,
            job_type=j.job_type,
            status=j.status,
            progress=j.progress,
            provider=j.provider,
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
            estimated_completion=j.estimated_completion.isoformat() if j.estimated_completion else None,
            result_url=j.result_url,
            error_message=j.error_message,
            created_at=j.created_at.isoformat(),
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get training job status and check for updates."""
    service = AiTwinService(db)

    try:
        job = await service.check_avatar_training(job_id, current_user.id)

        return TrainingJobResponse(
            id=job.id,
            ai_twin_id=job.ai_twin_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            provider=job.provider,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            estimated_completion=job.estimated_completion.isoformat() if job.estimated_completion else None,
            result_url=job.result_url,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Generation Endpoints ====================


@router.post("/{twin_id}/generate/video", response_model=GeneratedAssetResponse)
async def generate_video(
    twin_id: uuid.UUID,
    request: GenerateVideoRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Generate a video with the AI Twin speaking."""
    if not request.text and not request.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or audio_url is required",
        )

    service = AiTwinService(db)

    try:
        asset = await service.generate_video(
            twin_id=twin_id,
            user_id=current_user.id,
            text=request.text,
            audio_url=request.audio_url,
            resolution=request.resolution,
            aspect_ratio=request.aspect_ratio,
            background_color=request.background_color,
        )

        return GeneratedAssetResponse(
            id=asset.id,
            ai_twin_id=asset.ai_twin_id,
            asset_type=asset.asset_type,
            input_text=asset.input_text,
            output_url=asset.output_url,
            thumbnail_url=asset.thumbnail_url,
            duration_seconds=asset.duration_seconds,
            status=asset.status,
            provider=asset.provider,
            created_at=asset.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{twin_id}/generate/speech", response_model=GeneratedAssetResponse)
async def synthesize_speech(
    twin_id: uuid.UUID,
    request: SynthesizeSpeechRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Generate speech audio using the AI Twin's voice."""
    service = AiTwinService(db)

    try:
        asset = await service.synthesize_speech(
            twin_id=twin_id,
            user_id=current_user.id,
            text=request.text,
            stability=request.stability,
            similarity_boost=request.similarity_boost,
        )

        return GeneratedAssetResponse(
            id=asset.id,
            ai_twin_id=asset.ai_twin_id,
            asset_type=asset.asset_type,
            input_text=asset.input_text,
            output_url=asset.output_url,
            thumbnail_url=asset.thumbnail_url,
            duration_seconds=asset.duration_seconds,
            status=asset.status,
            provider=asset.provider,
            created_at=asset.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{twin_id}/assets", response_model=List[GeneratedAssetResponse])
async def list_generated_assets(
    twin_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    asset_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """List generated assets for an AI Twin."""
    # Verify ownership
    result = await db.execute(
        select(AiTwin).where(
            AiTwin.id == twin_id,
            AiTwin.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Twin not found",
        )

    query = select(TwinGeneratedAsset).where(
        TwinGeneratedAsset.ai_twin_id == twin_id
    )

    if asset_type:
        query = query.where(TwinGeneratedAsset.asset_type == asset_type)

    query = query.order_by(desc(TwinGeneratedAsset.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    assets = result.scalars().all()

    return [
        GeneratedAssetResponse(
            id=a.id,
            ai_twin_id=a.ai_twin_id,
            asset_type=a.asset_type,
            input_text=a.input_text,
            output_url=a.output_url,
            thumbnail_url=a.thumbnail_url,
            duration_seconds=a.duration_seconds,
            status=a.status,
            provider=a.provider,
            created_at=a.created_at.isoformat(),
        )
        for a in assets
    ]


@router.get("/assets/{asset_id}", response_model=GeneratedAssetResponse)
async def get_generated_asset(
    asset_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get asset details and check generation status."""
    service = AiTwinService(db)

    try:
        asset = await service.check_video_generation(asset_id, current_user.id)

        return GeneratedAssetResponse(
            id=asset.id,
            ai_twin_id=asset.ai_twin_id,
            asset_type=asset.asset_type,
            input_text=asset.input_text,
            output_url=asset.output_url,
            thumbnail_url=asset.thumbnail_url,
            duration_seconds=asset.duration_seconds,
            status=asset.status,
            provider=asset.provider,
            created_at=asset.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
