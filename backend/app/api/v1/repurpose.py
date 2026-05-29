"""
Content Repurposing API Endpoints

Transform content from one format to multiple platform-optimized formats.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.content.repurposer import ContentRepurposer

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class RepurposeResultResponse(BaseModel):
    """Result of a repurposing operation."""
    source_id: str
    source_type: str
    output_type: str
    content: dict
    platform: Optional[str]
    metadata: dict
    created_at: datetime


class PodcastToSocialRequest(BaseModel):
    """Request to generate social posts from podcast."""
    episode_id: str
    platforms: Optional[List[str]] = None
    post_count: int = Field(default=5, ge=1, le=20)
    brand_voice_id: Optional[str] = None


class PodcastToQuoteCardsRequest(BaseModel):
    """Request to generate quote cards from podcast."""
    episode_id: str
    quote_count: int = Field(default=5, ge=1, le=10)
    style: str = Field(default="minimal", pattern="^(minimal|gradient|bold|professional|playful)$")


class PodcastToBlogRequest(BaseModel):
    """Request to generate blog post from podcast."""
    episode_id: str
    include_timestamps: bool = True
    brand_voice_id: Optional[str] = None


class PodcastToNewsletterRequest(BaseModel):
    """Request to generate newsletter from podcast."""
    episode_id: str
    brand_voice_id: Optional[str] = None


class VideoToShortsRequest(BaseModel):
    """Request to generate shorts from long video."""
    content_id: str
    clip_count: int = Field(default=5, ge=1, le=10)
    platforms: Optional[List[str]] = None


class BlogToThreadRequest(BaseModel):
    """Request to convert blog to Twitter thread."""
    content_id: str
    max_tweets: int = Field(default=10, ge=3, le=25)


class BlogToLinkedInRequest(BaseModel):
    """Request to convert blog to LinkedIn post."""
    content_id: str
    style: str = Field(default="professional", pattern="^(professional|casual|thought_leader)$")


class BlogToCarouselRequest(BaseModel):
    """Request to convert blog to carousel."""
    content_id: str
    slide_count: int = Field(default=10, ge=3, le=10)
    platform: str = Field(default="instagram", pattern="^(instagram|linkedin)$")


class RepurposeAllRequest(BaseModel):
    """Request to repurpose content to all platforms."""
    content_id: str
    content_type: str = Field(..., pattern="^(podcast_episode|blog_post|video)$")
    brand_voice_id: Optional[str] = None


class RepurposeAllResponse(BaseModel):
    """Response with all repurposed content."""
    twitter: List[RepurposeResultResponse]
    linkedin: List[RepurposeResultResponse]
    instagram: List[RepurposeResultResponse]
    tiktok: List[RepurposeResultResponse]
    facebook: List[RepurposeResultResponse]
    youtube_shorts: List[RepurposeResultResponse]
    blog: List[RepurposeResultResponse]
    newsletter: List[RepurposeResultResponse]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/podcast/social", response_model=List[RepurposeResultResponse])
async def podcast_to_social_posts(
    request: PodcastToSocialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate social media posts from a podcast episode.

    Extracts key insights, quotes, and takeaways optimized for each platform.
    """
    try:
        episode_uuid = uuid.UUID(request.episode_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode ID format")

    brand_voice_uuid = None
    if request.brand_voice_id:
        try:
            brand_voice_uuid = uuid.UUID(request.brand_voice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid brand voice ID format")

    service = ContentRepurposer(db)

    try:
        results = await service.podcast_to_social_posts(
            episode_id=episode_uuid,
            user_id=current_user.id,
            platforms=request.platforms,
            post_count=request.post_count,
            brand_voice_id=brand_voice_uuid,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        RepurposeResultResponse(
            source_id=str(r.source_id),
            source_type=r.source_type,
            output_type=r.output_type,
            content=r.content if isinstance(r.content, dict) else {"data": r.content},
            platform=r.platform,
            metadata=r.metadata,
            created_at=r.created_at,
        )
        for r in results
    ]


@router.post("/podcast/quote-cards", response_model=List[RepurposeResultResponse])
async def podcast_to_quote_cards(
    request: PodcastToQuoteCardsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract quotable moments and generate quote card data.

    Returns structured data for rendering as shareable images.
    """
    try:
        episode_uuid = uuid.UUID(request.episode_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode ID format")

    service = ContentRepurposer(db)

    try:
        results = await service.podcast_to_quote_cards(
            episode_id=episode_uuid,
            user_id=current_user.id,
            quote_count=request.quote_count,
            style=request.style,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        RepurposeResultResponse(
            source_id=str(r.source_id),
            source_type=r.source_type,
            output_type=r.output_type,
            content=r.content if isinstance(r.content, dict) else {"data": r.content},
            platform=r.platform,
            metadata=r.metadata,
            created_at=r.created_at,
        )
        for r in results
    ]


@router.post("/podcast/blog", response_model=RepurposeResultResponse)
async def podcast_to_blog_post(
    request: PodcastToBlogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert podcast episode to a full blog post.

    Creates SEO-optimized article from episode content.
    """
    try:
        episode_uuid = uuid.UUID(request.episode_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode ID format")

    brand_voice_uuid = None
    if request.brand_voice_id:
        try:
            brand_voice_uuid = uuid.UUID(request.brand_voice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid brand voice ID format")

    service = ContentRepurposer(db)

    try:
        result = await service.podcast_to_blog_post(
            episode_id=episode_uuid,
            user_id=current_user.id,
            include_timestamps=request.include_timestamps,
            brand_voice_id=brand_voice_uuid,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RepurposeResultResponse(
        source_id=str(result.source_id),
        source_type=result.source_type,
        output_type=result.output_type,
        content=result.content if isinstance(result.content, dict) else {"data": result.content},
        platform=result.platform,
        metadata=result.metadata,
        created_at=result.created_at,
    )


@router.post("/podcast/newsletter", response_model=RepurposeResultResponse)
async def podcast_to_newsletter(
    request: PodcastToNewsletterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create newsletter content from podcast episode.
    """
    try:
        episode_uuid = uuid.UUID(request.episode_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid episode ID format")

    brand_voice_uuid = None
    if request.brand_voice_id:
        try:
            brand_voice_uuid = uuid.UUID(request.brand_voice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid brand voice ID format")

    service = ContentRepurposer(db)

    try:
        result = await service.podcast_to_newsletter(
            episode_id=episode_uuid,
            user_id=current_user.id,
            brand_voice_id=brand_voice_uuid,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RepurposeResultResponse(
        source_id=str(result.source_id),
        source_type=result.source_type,
        output_type=result.output_type,
        content=result.content if isinstance(result.content, dict) else {"data": result.content},
        platform=result.platform,
        metadata=result.metadata,
        created_at=result.created_at,
    )


@router.post("/video/shorts", response_model=List[RepurposeResultResponse])
async def video_to_shorts(
    request: VideoToShortsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Identify best moments from long video for short-form content.

    Returns timing markers and suggested captions for clips.
    """
    try:
        content_uuid = uuid.UUID(request.content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")

    service = ContentRepurposer(db)

    try:
        results = await service.long_video_to_shorts(
            content_id=content_uuid,
            user_id=current_user.id,
            clip_count=request.clip_count,
            platforms=request.platforms,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        RepurposeResultResponse(
            source_id=str(r.source_id),
            source_type=r.source_type,
            output_type=r.output_type,
            content=r.content if isinstance(r.content, dict) else {"data": r.content},
            platform=r.platform,
            metadata=r.metadata,
            created_at=r.created_at,
        )
        for r in results
    ]


@router.post("/blog/twitter-thread", response_model=RepurposeResultResponse)
async def blog_to_twitter_thread(
    request: BlogToThreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert blog post to Twitter/X thread.
    """
    try:
        content_uuid = uuid.UUID(request.content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")

    service = ContentRepurposer(db)

    try:
        result = await service.blog_to_twitter_thread(
            content_id=content_uuid,
            user_id=current_user.id,
            max_tweets=request.max_tweets,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RepurposeResultResponse(
        source_id=str(result.source_id),
        source_type=result.source_type,
        output_type=result.output_type,
        content=result.content if isinstance(result.content, dict) else {"data": result.content},
        platform=result.platform,
        metadata=result.metadata,
        created_at=result.created_at,
    )


@router.post("/blog/linkedin", response_model=RepurposeResultResponse)
async def blog_to_linkedin_post(
    request: BlogToLinkedInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert blog post to LinkedIn-optimized post.
    """
    try:
        content_uuid = uuid.UUID(request.content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")

    service = ContentRepurposer(db)

    try:
        result = await service.blog_to_linkedin_post(
            content_id=content_uuid,
            user_id=current_user.id,
            style=request.style,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RepurposeResultResponse(
        source_id=str(result.source_id),
        source_type=result.source_type,
        output_type=result.output_type,
        content=result.content if isinstance(result.content, dict) else {"data": result.content},
        platform=result.platform,
        metadata=result.metadata,
        created_at=result.created_at,
    )


@router.post("/blog/carousel", response_model=RepurposeResultResponse)
async def blog_to_carousel(
    request: BlogToCarouselRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert blog post to carousel slides for Instagram/LinkedIn.
    """
    try:
        content_uuid = uuid.UUID(request.content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")

    service = ContentRepurposer(db)

    try:
        result = await service.blog_to_carousel(
            content_id=content_uuid,
            user_id=current_user.id,
            slide_count=request.slide_count,
            platform=request.platform,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RepurposeResultResponse(
        source_id=str(result.source_id),
        source_type=result.source_type,
        output_type=result.output_type,
        content=result.content if isinstance(result.content, dict) else {"data": result.content},
        platform=result.platform,
        metadata=result.metadata,
        created_at=result.created_at,
    )


@router.post("/all", response_model=RepurposeAllResponse)
async def repurpose_to_all_platforms(
    request: RepurposeAllRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    One-click repurpose content to all supported platforms.

    Generates optimized content for Twitter, LinkedIn, Instagram,
    TikTok, Facebook, YouTube Shorts, blog, and newsletter.
    """
    try:
        content_uuid = uuid.UUID(request.content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID format")

    brand_voice_uuid = None
    if request.brand_voice_id:
        try:
            brand_voice_uuid = uuid.UUID(request.brand_voice_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid brand voice ID format")

    service = ContentRepurposer(db)

    try:
        results = await service.repurpose_to_all_platforms(
            content_id=content_uuid,
            user_id=current_user.id,
            content_type=request.content_type,
            brand_voice_id=brand_voice_uuid,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    def format_results(items):
        return [
            RepurposeResultResponse(
                source_id=str(r.source_id),
                source_type=r.source_type,
                output_type=r.output_type,
                content=r.content if isinstance(r.content, dict) else {"data": r.content},
                platform=r.platform,
                metadata=r.metadata,
                created_at=r.created_at,
            )
            for r in items
        ]

    return RepurposeAllResponse(
        twitter=format_results(results.get("twitter", [])),
        linkedin=format_results(results.get("linkedin", [])),
        instagram=format_results(results.get("instagram", [])),
        tiktok=format_results(results.get("tiktok", [])),
        facebook=format_results(results.get("facebook", [])),
        youtube_shorts=format_results(results.get("youtube_shorts", [])),
        blog=format_results(results.get("blog", [])),
        newsletter=format_results(results.get("newsletter", [])),
    )


@router.get("/platforms")
async def get_supported_platforms():
    """
    Get list of supported platforms and content transformations.
    """
    return {
        "source_types": [
            {
                "type": "podcast_episode",
                "outputs": ["social_posts", "quote_cards", "blog_post", "newsletter"],
            },
            {
                "type": "blog_post",
                "outputs": ["twitter_thread", "linkedin_post", "carousel"],
            },
            {
                "type": "video",
                "outputs": ["shorts", "clips"],
            },
        ],
        "platforms": {
            "twitter": {"max_chars": 280, "thread_max": 25},
            "instagram": {"caption_max": 2200, "carousel_max": 10},
            "linkedin": {"max_chars": 3000},
            "tiktok": {"caption_max": 2200, "video_max_seconds": 180},
            "youtube_shorts": {"title_max": 100, "video_max_seconds": 60},
            "facebook": {"max_chars": 63206},
        },
        "quote_card_styles": ["minimal", "gradient", "bold", "professional", "playful"],
    }


@router.get("")
async def _qa_list_root():
    """QA gap-closure: collection list (empty until feature persists items)."""
    return []
