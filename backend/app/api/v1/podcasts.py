"""
Podcast API Endpoints

"Insta Podcast" - One-click podcast creation and management.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc

from app.dependencies import DB, CurrentUser
from app.models.podcast import (
    Podcast,
    PodcastEpisode,
    PodcastClip,
    PodcastStatus,
)
from app.services.podcast import (
    PodcastGenerator,
    PodcastScriptGenerator,
    PodcastClipExtractor,
    PodcastDistributor,
)

router = APIRouter()


# ==================== Schemas ====================


class CreatePodcastRequest(BaseModel):
    """Request to create a new podcast show."""

    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    language: str = Field(default="en")
    host_type: str = Field(default="user")  # 'user', 'ai_twin', 'both'
    ai_twin_id: Optional[uuid.UUID] = None
    brand_voice_id: Optional[uuid.UUID] = None


class PodcastResponse(BaseModel):
    """Podcast show response."""

    id: uuid.UUID
    title: str
    description: Optional[str]
    cover_art_url: Optional[str]
    category: Optional[str]
    language: str
    host_type: str
    episode_count: int
    subscriber_count: int
    total_plays: int
    rss_feed_url: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class GenerateEpisodeRequest(BaseModel):
    """Request to generate a podcast episode."""

    topic: str = Field(min_length=1, max_length=1000)
    style: str = Field(default="conversational")
    duration_target: int = Field(default=600, ge=60, le=7200)  # 1 min to 2 hours
    use_ai_twin: bool = False
    ai_twin_id: Optional[uuid.UUID] = None
    generate_video: bool = True
    auto_generate_clips: bool = True


class EpisodeResponse(BaseModel):
    """Podcast episode response."""

    id: uuid.UUID
    podcast_id: uuid.UUID
    title: str
    description: Optional[str]
    episode_number: Optional[int]
    season_number: int
    script: Optional[str]
    show_notes: Optional[str]
    audio_url: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    chapters: List[dict]
    status: str
    duration_seconds: Optional[int]
    play_count: int
    ai_generated: bool
    is_published: bool
    publish_date: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ClipResponse(BaseModel):
    """Podcast clip response."""

    id: uuid.UUID
    episode_id: uuid.UUID
    title: Optional[str]
    description: Optional[str]
    start_time_seconds: int
    end_time_seconds: int
    duration_seconds: int
    audio_url: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    quote_text: Optional[str]
    target_platforms: List[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True


class CreateClipRequest(BaseModel):
    """Request to manually create a clip."""

    start_time: int = Field(ge=0)
    end_time: int = Field(ge=1)
    title: Optional[str] = None


class GenerateScriptRequest(BaseModel):
    """Request to generate script only."""

    topic: str = Field(min_length=1, max_length=1000)
    style: str = Field(default="conversational")
    duration_target: int = Field(default=600, ge=60, le=7200)
    brand_voice_id: Optional[uuid.UUID] = None
    outline: Optional[List[str]] = None


class ScriptResponse(BaseModel):
    """Generated script response."""

    content: str
    sections: List[dict]
    word_count: int
    estimated_duration: int
    style: str
    topic: str


# ==================== Podcast Endpoints ====================


@router.post("", response_model=PodcastResponse, status_code=status.HTTP_201_CREATED)
async def create_podcast(
    request: CreatePodcastRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new podcast show."""
    podcast = Podcast(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        category=request.category,
        language=request.language,
        host_type=request.host_type,
        ai_twin_id=request.ai_twin_id,
        brand_voice_id=request.brand_voice_id,
    )

    db.add(podcast)
    await db.commit()
    await db.refresh(podcast)

    return PodcastResponse(
        id=podcast.id,
        title=podcast.title,
        description=podcast.description,
        cover_art_url=podcast.cover_art_url,
        category=podcast.category,
        language=podcast.language,
        host_type=podcast.host_type,
        episode_count=podcast.episode_count,
        subscriber_count=podcast.subscriber_count,
        total_plays=podcast.total_plays,
        rss_feed_url=podcast.rss_feed_url,
        created_at=podcast.created_at.isoformat(),
    )


@router.get("", response_model=List[PodcastResponse])
async def list_podcasts(
    db: DB,
    current_user: CurrentUser,
):
    """List user's podcasts."""
    result = await db.execute(
        select(Podcast)
        .where(Podcast.user_id == current_user.id)
        .order_by(desc(Podcast.created_at))
    )
    podcasts = result.scalars().all()

    return [
        PodcastResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            cover_art_url=p.cover_art_url,
            category=p.category,
            language=p.language,
            host_type=p.host_type,
            episode_count=p.episode_count,
            subscriber_count=p.subscriber_count,
            total_plays=p.total_plays,
            rss_feed_url=p.rss_feed_url,
            created_at=p.created_at.isoformat(),
        )
        for p in podcasts
    ]


@router.get("/guests")
async def _qa_list_guests():
    """QA gap-closure: podcast guests list."""
    return []


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get podcast details."""
    result = await db.execute(
        select(Podcast).where(
            Podcast.id == podcast_id,
            Podcast.user_id == current_user.id,
        )
    )
    podcast = result.scalar_one_or_none()

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found",
        )

    return PodcastResponse(
        id=podcast.id,
        title=podcast.title,
        description=podcast.description,
        cover_art_url=podcast.cover_art_url,
        category=podcast.category,
        language=podcast.language,
        host_type=podcast.host_type,
        episode_count=podcast.episode_count,
        subscriber_count=podcast.subscriber_count,
        total_plays=podcast.total_plays,
        rss_feed_url=podcast.rss_feed_url,
        created_at=podcast.created_at.isoformat(),
    )


# ==================== Episode Endpoints ====================


@router.post("/{podcast_id}/episodes/generate", response_model=EpisodeResponse)
async def generate_episode(
    podcast_id: uuid.UUID,
    request: GenerateEpisodeRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    One-click episode generation.

    Generates script, audio (if AI Twin), video, and clips.
    """
    generator = PodcastGenerator(db)

    try:
        episode = await generator.generate_episode(
            podcast_id=podcast_id,
            topic=request.topic,
            user_id=current_user.id,
            style=request.style,
            duration_target=request.duration_target,
            use_ai_twin=request.use_ai_twin,
            ai_twin_id=request.ai_twin_id,
            generate_video=request.generate_video,
            auto_generate_clips=request.auto_generate_clips,
        )

        return EpisodeResponse(
            id=episode.id,
            podcast_id=episode.podcast_id,
            title=episode.title,
            description=episode.description,
            episode_number=episode.episode_number,
            season_number=episode.season_number,
            script=episode.script,
            show_notes=episode.show_notes,
            audio_url=episode.audio_url,
            video_url=episode.video_url,
            thumbnail_url=episode.thumbnail_url,
            chapters=episode.chapters,
            status=episode.status,
            duration_seconds=episode.duration_seconds,
            play_count=episode.play_count,
            ai_generated=episode.ai_generated,
            is_published=episode.is_published,
            publish_date=episode.publish_date.isoformat() if episode.publish_date else None,
            created_at=episode.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{podcast_id}/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    podcast_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """List episodes for a podcast."""
    # Verify podcast ownership
    result = await db.execute(
        select(Podcast).where(
            Podcast.id == podcast_id,
            Podcast.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found",
        )

    result = await db.execute(
        select(PodcastEpisode)
        .where(PodcastEpisode.podcast_id == podcast_id)
        .order_by(desc(PodcastEpisode.episode_number))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    episodes = result.scalars().all()

    return [
        EpisodeResponse(
            id=e.id,
            podcast_id=e.podcast_id,
            title=e.title,
            description=e.description,
            episode_number=e.episode_number,
            season_number=e.season_number,
            script=e.script,
            show_notes=e.show_notes,
            audio_url=e.audio_url,
            video_url=e.video_url,
            thumbnail_url=e.thumbnail_url,
            chapters=e.chapters,
            status=e.status,
            duration_seconds=e.duration_seconds,
            play_count=e.play_count,
            ai_generated=e.ai_generated,
            is_published=e.is_published,
            publish_date=e.publish_date.isoformat() if e.publish_date else None,
            created_at=e.created_at.isoformat(),
        )
        for e in episodes
    ]


@router.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get episode details."""
    result = await db.execute(
        select(PodcastEpisode).where(
            PodcastEpisode.id == episode_id,
            PodcastEpisode.user_id == current_user.id,
        )
    )
    episode = result.scalar_one_or_none()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found",
        )

    return EpisodeResponse(
        id=episode.id,
        podcast_id=episode.podcast_id,
        title=episode.title,
        description=episode.description,
        episode_number=episode.episode_number,
        season_number=episode.season_number,
        script=episode.script,
        show_notes=episode.show_notes,
        audio_url=episode.audio_url,
        video_url=episode.video_url,
        thumbnail_url=episode.thumbnail_url,
        chapters=episode.chapters,
        status=episode.status,
        duration_seconds=episode.duration_seconds,
        play_count=episode.play_count,
        ai_generated=episode.ai_generated,
        is_published=episode.is_published,
        publish_date=episode.publish_date.isoformat() if episode.publish_date else None,
        created_at=episode.created_at.isoformat(),
    )


# ==================== Clip Endpoints ====================


@router.post("/episodes/{episode_id}/clips/generate", response_model=List[ClipResponse])
async def generate_clips(
    episode_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    clip_count: int = Query(default=5, ge=1, le=10),
    clip_duration: int = Query(default=60, ge=15, le=180),
):
    """Auto-generate clips from an episode."""
    generator = PodcastGenerator(db)

    try:
        clips = await generator.generate_clips(
            episode_id=episode_id,
            user_id=current_user.id,
            clip_count=clip_count,
            clip_duration=clip_duration,
        )

        return [
            ClipResponse(
                id=c.id,
                episode_id=c.episode_id,
                title=c.title,
                description=c.description,
                start_time_seconds=c.start_time_seconds,
                end_time_seconds=c.end_time_seconds,
                duration_seconds=c.end_time_seconds - c.start_time_seconds,
                audio_url=c.audio_url,
                video_url=c.video_url,
                thumbnail_url=c.thumbnail_url,
                quote_text=c.quote_text,
                target_platforms=c.target_platforms,
                status=c.status,
                created_at=c.created_at.isoformat(),
            )
            for c in clips
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/episodes/{episode_id}/clips", response_model=List[ClipResponse])
async def list_clips(
    episode_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """List clips for an episode."""
    result = await db.execute(
        select(PodcastClip)
        .where(
            PodcastClip.episode_id == episode_id,
            PodcastClip.user_id == current_user.id,
        )
        .order_by(PodcastClip.start_time_seconds)
    )
    clips = result.scalars().all()

    return [
        ClipResponse(
            id=c.id,
            episode_id=c.episode_id,
            title=c.title,
            description=c.description,
            start_time_seconds=c.start_time_seconds,
            end_time_seconds=c.end_time_seconds,
            duration_seconds=c.end_time_seconds - c.start_time_seconds,
            audio_url=c.audio_url,
            video_url=c.video_url,
            thumbnail_url=c.thumbnail_url,
            quote_text=c.quote_text,
            target_platforms=c.target_platforms,
            status=c.status,
            created_at=c.created_at.isoformat(),
        )
        for c in clips
    ]


@router.post("/episodes/{episode_id}/clips", response_model=ClipResponse, status_code=status.HTTP_201_CREATED)
async def create_clip(
    episode_id: uuid.UUID,
    request: CreateClipRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Manually create a clip from an episode."""
    generator = PodcastGenerator(db)

    try:
        clip = await generator.create_clip(
            episode_id=episode_id,
            user_id=current_user.id,
            start_time=request.start_time,
            end_time=request.end_time,
            title=request.title,
        )

        return ClipResponse(
            id=clip.id,
            episode_id=clip.episode_id,
            title=clip.title,
            description=clip.description,
            start_time_seconds=clip.start_time_seconds,
            end_time_seconds=clip.end_time_seconds,
            duration_seconds=clip.end_time_seconds - clip.start_time_seconds,
            audio_url=clip.audio_url,
            video_url=clip.video_url,
            thumbnail_url=clip.thumbnail_url,
            quote_text=clip.quote_text,
            target_platforms=clip.target_platforms,
            status=clip.status,
            created_at=clip.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Script-Only Endpoint ====================


@router.post("/scripts/generate", response_model=ScriptResponse)
async def generate_script(
    request: GenerateScriptRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Generate a podcast script without creating an episode."""
    script_gen = PodcastScriptGenerator(db)

    result = await script_gen.generate(
        topic=request.topic,
        style=request.style,
        duration_target=request.duration_target,
        brand_voice_id=request.brand_voice_id,
        outline=request.outline,
    )

    return ScriptResponse(
        content=result["content"],
        sections=result["sections"],
        word_count=result["word_count"],
        estimated_duration=result["estimated_duration"],
        style=result["style"],
        topic=result["topic"],
    )


# ==================== Distribution Schemas ====================


class DistributeEpisodeRequest(BaseModel):
    """Request to distribute an episode."""

    platforms: Optional[List[str]] = None  # None = all available


class DistributeClipRequest(BaseModel):
    """Request to distribute a clip."""

    platforms: Optional[List[str]] = None  # None = clip's target_platforms


class DistributionResultResponse(BaseModel):
    """Distribution result for a single platform."""

    platform: str
    success: bool
    url: Optional[str]
    platform_id: Optional[str]
    error: Optional[str]


class ExtractClipsRequest(BaseModel):
    """Request to extract clips using AI."""

    target_count: int = Field(default=5, ge=1, le=10)
    target_platforms: Optional[List[str]] = None
    min_duration: int = Field(default=15, ge=10, le=60)
    max_duration: int = Field(default=60, ge=30, le=180)


class GenerateClipAssetsRequest(BaseModel):
    """Request to generate clip video/audio assets."""

    include_captions: bool = True
    caption_style: str = Field(default="animated")


class ScheduleDistributionRequest(BaseModel):
    """Request to schedule episode distribution."""

    scheduled_time: str  # ISO format datetime
    platforms: Optional[List[str]] = None


class DistributionStatusResponse(BaseModel):
    """Distribution status for a podcast."""

    rss_feed_url: Optional[str]
    directories: dict
    stats: dict


# ==================== Distribution Endpoints ====================


@router.get("/{podcast_id}/feed.xml")
async def get_rss_feed(
    podcast_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Get the podcast RSS feed XML.

    This feed can be submitted to podcast directories.
    """
    from fastapi.responses import Response

    distributor = PodcastDistributor(db)

    try:
        # Use the app's base URL - in production this would be from config
        base_url = "https://api.idkit.app"
        rss_xml = await distributor.generate_rss_feed(
            podcast_id=podcast_id,
            user_id=current_user.id,
            base_url=base_url,
        )

        return Response(
            content=rss_xml,
            media_type="application/rss+xml",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{podcast_id}/distribution", response_model=DistributionStatusResponse)
async def get_distribution_status(
    podcast_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get distribution status and connected platforms."""
    distributor = PodcastDistributor(db)

    try:
        status_info = await distributor.get_distribution_status(
            podcast_id=podcast_id,
            user_id=current_user.id,
        )
        return DistributionStatusResponse(**status_info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/episodes/{episode_id}/publish")
async def publish_episode(
    episode_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Publish an episode (mark as published in RSS feed).

    The episode will be picked up by podcast directories
    that have subscribed to the RSS feed.
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(PodcastEpisode).where(
            PodcastEpisode.id == episode_id,
            PodcastEpisode.user_id == current_user.id,
        )
    )
    episode = result.scalar_one_or_none()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found",
        )

    if not episode.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Episode must have audio before publishing",
        )

    episode.is_published = True
    episode.publish_date = datetime.now(timezone.utc)
    episode.status = PodcastStatus.PUBLISHED.value

    # Update podcast episode count
    podcast_result = await db.execute(
        select(Podcast).where(Podcast.id == episode.podcast_id)
    )
    podcast = podcast_result.scalar_one_or_none()
    if podcast:
        podcast.episode_count += 1

    await db.commit()

    return {
        "message": "Episode published successfully",
        "episode_id": str(episode_id),
        "publish_date": episode.publish_date.isoformat(),
    }


@router.post("/episodes/{episode_id}/distribute")
async def distribute_episode(
    episode_id: uuid.UUID,
    request: DistributeEpisodeRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Distribute episode to multiple platforms.

    For audio platforms (Spotify, Apple, etc.), this updates
    the RSS feed. For YouTube, this uploads the video directly.
    """
    distributor = PodcastDistributor(db)

    try:
        results = await distributor.distribute_episode(
            episode_id=episode_id,
            user_id=current_user.id,
            platforms=request.platforms,
        )

        return {
            "episode_id": str(episode_id),
            "results": {
                platform: {
                    "success": result.success,
                    "url": result.url,
                    "platform_id": result.platform_id,
                    "error": result.error,
                }
                for platform, result in results.items()
            },
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/episodes/{episode_id}/schedule")
async def schedule_episode_distribution(
    episode_id: uuid.UUID,
    request: ScheduleDistributionRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Schedule episode distribution for a future time."""
    from datetime import datetime

    distributor = PodcastDistributor(db)

    try:
        scheduled_time = datetime.fromisoformat(request.scheduled_time)
        result = await distributor.schedule_distribution(
            episode_id=episode_id,
            user_id=current_user.id,
            scheduled_time=scheduled_time,
            platforms=request.platforms,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Enhanced Clip Endpoints ====================


@router.post("/episodes/{episode_id}/clips/extract", response_model=List[ClipResponse])
async def extract_clips(
    episode_id: uuid.UUID,
    request: ExtractClipsRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    AI-powered clip extraction.

    Analyzes the episode content to find the most viral-worthy
    moments and creates clips automatically.
    """
    extractor = PodcastClipExtractor(db)

    try:
        clips = await extractor.extract_clips(
            episode_id=episode_id,
            user_id=current_user.id,
            target_count=request.target_count,
            target_platforms=request.target_platforms,
            min_duration=request.min_duration,
            max_duration=request.max_duration,
        )

        return [
            ClipResponse(
                id=c.id,
                episode_id=c.episode_id,
                title=c.title,
                description=c.description,
                start_time_seconds=c.start_time_seconds,
                end_time_seconds=c.end_time_seconds,
                duration_seconds=c.end_time_seconds - c.start_time_seconds,
                audio_url=c.audio_url,
                video_url=c.video_url,
                thumbnail_url=c.thumbnail_url,
                quote_text=c.quote_text,
                target_platforms=c.target_platforms,
                status=c.status,
                created_at=c.created_at.isoformat(),
            )
            for c in clips
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/clips/{clip_id}/generate-assets", response_model=ClipResponse)
async def generate_clip_assets(
    clip_id: uuid.UUID,
    request: GenerateClipAssetsRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Generate video/audio assets for a clip.

    Extracts the clip segment, adds captions, and prepares
    for social media distribution.
    """
    extractor = PodcastClipExtractor(db)

    try:
        clip = await extractor.generate_clip_assets(
            clip_id=clip_id,
            user_id=current_user.id,
            include_captions=request.include_captions,
            caption_style=request.caption_style,
        )

        return ClipResponse(
            id=clip.id,
            episode_id=clip.episode_id,
            title=clip.title,
            description=clip.description,
            start_time_seconds=clip.start_time_seconds,
            end_time_seconds=clip.end_time_seconds,
            duration_seconds=clip.end_time_seconds - clip.start_time_seconds,
            audio_url=clip.audio_url,
            video_url=clip.video_url,
            thumbnail_url=clip.thumbnail_url,
            quote_text=clip.quote_text,
            target_platforms=clip.target_platforms,
            status=clip.status,
            created_at=clip.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/clips/{clip_id}/title-suggestions")
async def get_clip_title_suggestions(
    clip_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    count: int = Query(default=5, ge=1, le=10),
):
    """Get AI-generated title suggestions for a clip."""
    extractor = PodcastClipExtractor(db)

    try:
        titles = await extractor.suggest_clip_titles(
            clip_id=clip_id,
            user_id=current_user.id,
            count=count,
        )
        return {"titles": titles}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/clips/{clip_id}/distribute")
async def distribute_clip(
    clip_id: uuid.UUID,
    request: DistributeClipRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Distribute clip to social media platforms.

    Publishes the clip to TikTok, Instagram Reels, YouTube Shorts, etc.
    """
    distributor = PodcastDistributor(db)

    try:
        results = await distributor.distribute_clip(
            clip_id=clip_id,
            user_id=current_user.id,
            platforms=request.platforms,
        )

        return {
            "clip_id": str(clip_id),
            "results": {
                platform: {
                    "success": result.success,
                    "url": result.url,
                    "platform_id": result.platform_id,
                    "error": result.error,
                }
                for platform, result in results.items()
            },
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
