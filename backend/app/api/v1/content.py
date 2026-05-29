"""
Content API Endpoints

Content generation, management, and publishing.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc

from app.dependencies import DB, CurrentUser
from app.models.content import (
    BrandVoice,
    ContentItem,
    ContentStatus,
    ContentTemplate,
    ContentType,
    GenerationJob,
)
from app.services.content import ContentGenerator

router = APIRouter()


# ==================== Schemas ====================


class GenerateContentRequest(BaseModel):
    """Request to generate content."""

    content_type: str = Field(
        description="Type: video_script, short_script, blog_post, social_post, email, podcast_script, carousel, thread"
    )
    topic: str = Field(min_length=1, max_length=1000)
    brand_voice_id: Optional[uuid.UUID] = None
    template_id: Optional[uuid.UUID] = None
    additional_context: Optional[str] = None
    target_platforms: Optional[List[str]] = None


class ContentResponse(BaseModel):
    """Content item response."""

    id: uuid.UUID
    content_type: str
    status: str
    title: str
    body: str
    media_urls: List[str]
    thumbnail_url: Optional[str]
    ai_generated: bool
    hashtags: List[str]
    target_platforms: List[str]
    scheduled_at: Optional[str]
    published_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BrandVoiceResponse(BaseModel):
    """Brand voice response."""

    id: uuid.UUID
    name: str
    description: Optional[str]
    tone: str
    personality_traits: List[str]
    sentence_style: str
    vocabulary_level: str
    use_emojis: bool
    emoji_frequency: str
    is_default: bool
    created_at: str

    class Config:
        from_attributes = True


class CreateBrandVoiceRequest(BaseModel):
    """Request to create a brand voice."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    tone: str = Field(default="professional")
    personality_traits: List[str] = Field(default_factory=list)
    sentence_style: str = Field(default="mixed")
    vocabulary_level: str = Field(default="general")
    use_emojis: bool = True
    emoji_frequency: str = Field(default="moderate")
    preferred_cta: List[str] = Field(default_factory=list)
    avoid_words: List[str] = Field(default_factory=list)
    sample_content: List[str] = Field(default_factory=list)
    is_default: bool = False


class TemplateResponse(BaseModel):
    """Content template response."""

    id: uuid.UUID
    name: str
    description: Optional[str]
    content_type: str
    template_body: str
    variables: List[dict]
    target_platforms: List[str]
    category: Optional[str]
    tags: List[str]
    use_count: int
    is_system: bool
    is_public: bool

    class Config:
        from_attributes = True


class RepurposeRequest(BaseModel):
    """Request to repurpose content."""

    content_id: uuid.UUID
    target_types: List[str]


class JobStatusResponse(BaseModel):
    """Generation job status response."""

    id: uuid.UUID
    job_type: str
    status: str
    progress: int
    error_message: Optional[str]
    content_id: Optional[uuid.UUID]
    created_at: str

    class Config:
        from_attributes = True


# ==================== Content Generation ====================


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Generate AI content based on topic and parameters.

    Supports various content types with optional brand voice
    and template customization.
    """
    try:
        content_type = ContentType(request.content_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {request.content_type}",
        )

    generator = ContentGenerator(db)

    try:
        content = await generator.generate_content(
            user_id=current_user.id,
            content_type=content_type,
            topic=request.topic,
            brand_voice_id=request.brand_voice_id,
            template_id=request.template_id,
            additional_context=request.additional_context,
            target_platforms=request.target_platforms,
        )

        return ContentResponse(
            id=content.id,
            content_type=content.content_type,
            status=content.status,
            title=content.title,
            body=content.body,
            media_urls=content.media_urls,
            thumbnail_url=content.thumbnail_url,
            ai_generated=content.ai_generated,
            hashtags=content.hashtags,
            target_platforms=content.target_platforms,
            scheduled_at=content.scheduled_at.isoformat() if content.scheduled_at else None,
            published_at=content.published_at.isoformat() if content.published_at else None,
            created_at=content.created_at.isoformat(),
            updated_at=content.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.post("/generate/stream")
async def generate_content_stream(
    request: GenerateContentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Stream content generation for real-time display.

    Returns server-sent events with content chunks.
    """
    try:
        content_type = ContentType(request.content_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {request.content_type}",
        )

    generator = ContentGenerator(db)

    async def stream_generator():
        async for chunk in generator.generate_content_stream(
            user_id=current_user.id,
            content_type=content_type,
            topic=request.topic,
            brand_voice_id=request.brand_voice_id,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )


@router.post("/repurpose", response_model=List[ContentResponse])
async def repurpose_content(
    request: RepurposeRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Repurpose existing content into other formats.

    E.g., Blog post -> Social posts, threads, etc.
    """
    target_types = []
    for t in request.target_types:
        try:
            target_types.append(ContentType(t))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type: {t}",
            )

    generator = ContentGenerator(db)

    try:
        contents = await generator.repurpose_content(
            content_id=request.content_id,
            target_types=target_types,
            user_id=current_user.id,
        )

        return [
            ContentResponse(
                id=c.id,
                content_type=c.content_type,
                status=c.status,
                title=c.title,
                body=c.body,
                media_urls=c.media_urls,
                thumbnail_url=c.thumbnail_url,
                ai_generated=c.ai_generated,
                hashtags=c.hashtags,
                target_platforms=c.target_platforms,
                scheduled_at=c.scheduled_at.isoformat() if c.scheduled_at else None,
                published_at=c.published_at.isoformat() if c.published_at else None,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in contents
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Content Management ====================


@router.get("", response_model=List[ContentResponse])
async def list_content(
    db: DB,
    current_user: CurrentUser,
    content_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """List user's content items."""
    query = select(ContentItem).where(ContentItem.user_id == current_user.id)

    if content_type:
        query = query.where(ContentItem.content_type == content_type)

    if status_filter:
        query = query.where(ContentItem.status == status_filter)

    query = (
        query.order_by(desc(ContentItem.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    contents = result.scalars().all()

    return [
        ContentResponse(
            id=c.id,
            content_type=c.content_type,
            status=c.status,
            title=c.title,
            body=c.body,
            media_urls=c.media_urls,
            thumbnail_url=c.thumbnail_url,
            ai_generated=c.ai_generated,
            hashtags=c.hashtags,
            target_platforms=c.target_platforms,
            scheduled_at=c.scheduled_at.isoformat() if c.scheduled_at else None,
            published_at=c.published_at.isoformat() if c.published_at else None,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in contents
    ]


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    db: DB,
    current_user: CurrentUser,
    content_type: Optional[str] = None,
    include_system: bool = Query(default=True),
    include_public: bool = Query(default=True),
):
    """List available templates."""
    from sqlalchemy import or_

    conditions = [ContentTemplate.user_id == current_user.id]

    if include_system:
        conditions.append(ContentTemplate.is_system == True)

    if include_public:
        conditions.append(ContentTemplate.is_public == True)

    query = select(ContentTemplate).where(or_(*conditions))

    if content_type:
        query = query.where(ContentTemplate.content_type == content_type)

    query = query.order_by(desc(ContentTemplate.use_count))

    result = await db.execute(query)
    templates = result.scalars().all()

    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            content_type=t.content_type,
            template_body=t.template_body,
            variables=t.variables,
            target_platforms=t.target_platforms,
            category=t.category,
            tags=t.tags,
            use_count=t.use_count,
            is_system=t.is_system,
            is_public=t.is_public,
        )
        for t in templates
    ]


# ==================== Jobs ====================


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get a specific content item."""
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return ContentResponse(
        id=content.id,
        content_type=content.content_type,
        status=content.status,
        title=content.title,
        body=content.body,
        media_urls=content.media_urls,
        thumbnail_url=content.thumbnail_url,
        ai_generated=content.ai_generated,
        hashtags=content.hashtags,
        target_platforms=content.target_platforms,
        scheduled_at=content.scheduled_at.isoformat() if content.scheduled_at else None,
        published_at=content.published_at.isoformat() if content.published_at else None,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
    )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete a content item."""
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    await db.delete(content)
    await db.commit()


# ==================== Brand Voices ====================


@router.get("/brand-voices", response_model=List[BrandVoiceResponse])
async def list_brand_voices(
    db: DB,
    current_user: CurrentUser,
):
    """List user's brand voices."""
    result = await db.execute(
        select(BrandVoice)
        .where(BrandVoice.user_id == current_user.id)
        .order_by(desc(BrandVoice.is_default), BrandVoice.name)
    )
    voices = result.scalars().all()

    return [
        BrandVoiceResponse(
            id=v.id,
            name=v.name,
            description=v.description,
            tone=v.tone,
            personality_traits=v.personality_traits,
            sentence_style=v.sentence_style,
            vocabulary_level=v.vocabulary_level,
            use_emojis=v.use_emojis,
            emoji_frequency=v.emoji_frequency,
            is_default=v.is_default,
            created_at=v.created_at.isoformat(),
        )
        for v in voices
    ]


@router.post("/brand-voices", response_model=BrandVoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_brand_voice(
    request: CreateBrandVoiceRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new brand voice."""
    # If setting as default, unset other defaults
    if request.is_default:
        from sqlalchemy import update

        await db.execute(
            update(BrandVoice)
            .where(BrandVoice.user_id == current_user.id)
            .values(is_default=False)
        )

    voice = BrandVoice(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        tone=request.tone,
        personality_traits=request.personality_traits,
        sentence_style=request.sentence_style,
        vocabulary_level=request.vocabulary_level,
        use_emojis=request.use_emojis,
        emoji_frequency=request.emoji_frequency,
        preferred_cta=request.preferred_cta,
        avoid_words=request.avoid_words,
        sample_content=request.sample_content,
        is_default=request.is_default,
    )

    db.add(voice)
    await db.commit()
    await db.refresh(voice)

    return BrandVoiceResponse(
        id=voice.id,
        name=voice.name,
        description=voice.description,
        tone=voice.tone,
        personality_traits=voice.personality_traits,
        sentence_style=voice.sentence_style,
        vocabulary_level=voice.vocabulary_level,
        use_emojis=voice.use_emojis,
        emoji_frequency=voice.emoji_frequency,
        is_default=voice.is_default,
        created_at=voice.created_at.isoformat(),
    )


# ==================== Templates ====================


@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_generation_jobs(
    db: DB,
    current_user: CurrentUser,
    status_filter: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    """List user's generation jobs."""
    query = select(GenerationJob).where(GenerationJob.user_id == current_user.id)

    if status_filter:
        query = query.where(GenerationJob.status == status_filter)

    query = query.order_by(desc(GenerationJob.created_at)).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [
        JobStatusResponse(
            id=j.id,
            job_type=j.job_type,
            status=j.status,
            progress=j.progress,
            error_message=j.error_message,
            content_id=j.content_id,
            created_at=j.created_at.isoformat(),
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get status of a specific generation job."""
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobStatusResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        content_id=job.content_id,
        created_at=job.created_at.isoformat(),
    )
