"""
Feed API Endpoints

TikTok-style personalized feed for IDKit community.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, OptionalUser, CurrentUser
from app.models.feed import FeedPost
from app.services.feed import FeedService

router = APIRouter()


# ==================== Schemas ====================


class PostAuthor(BaseModel):
    """Post author info."""

    user_id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str]
    is_verified: bool


class PostResponse(BaseModel):
    """Feed post response."""

    id: uuid.UUID
    post_type: str
    content_text: Optional[str]
    media_urls: List[str]
    thumbnail_url: Optional[str]
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    save_count: int
    hashtags: List[str]
    ai_generated: bool
    created_at: str

    # Viewer-specific
    is_liked: bool = False
    is_saved: bool = False

    class Config:
        from_attributes = True


class FeedResponse(BaseModel):
    """Feed response with pagination."""

    posts: List[PostResponse]
    page: int
    page_size: int
    has_more: bool


# ==================== Endpoints ====================


@router.get("", response_model=FeedResponse)
async def get_feed(
    db: DB,
    current_user: OptionalUser,
    feed_type: str = Query(
        default="for_you",
        description="Feed type: for_you, following, trending, discover",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """
    Get personalized feed.

    Feed types:
    - `for_you`: Personalized mix based on engagement and preferences
    - `following`: Posts only from users you follow
    - `trending`: Top trending posts
    - `discover`: New content discovery
    """
    service = FeedService(db)

    user_id = current_user.id if current_user else None

    posts = await service.get_feed(
        user_id=user_id,
        feed_type=feed_type,
        page=page,
        page_size=page_size + 1,  # Get one extra to check has_more
    )

    has_more = len(posts) > page_size
    posts = posts[:page_size]

    # Convert to response with viewer context
    post_responses = []
    for post in posts:
        response = PostResponse(
            id=post.id,
            post_type=post.post_type,
            content_text=post.content_text,
            media_urls=post.media_urls,
            thumbnail_url=post.thumbnail_url,
            view_count=post.view_count,
            like_count=post.like_count,
            comment_count=post.comment_count,
            share_count=post.share_count,
            save_count=post.save_count,
            hashtags=post.hashtags,
            ai_generated=post.ai_generated,
            created_at=post.created_at.isoformat(),
        )

        # Add viewer context if authenticated
        if user_id:
            response.is_liked = await service.is_post_liked(post.id, user_id)
            # response.is_saved = await service.is_post_saved(post.id, user_id)

        post_responses.append(response)

    return FeedResponse(
        posts=post_responses,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/following", response_model=FeedResponse)
async def get_following_feed(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get feed from followed users only (requires authentication)."""
    service = FeedService(db)

    posts = await service.get_feed(
        user_id=current_user.id,
        feed_type="following",
        page=page,
        page_size=page_size + 1,
    )

    has_more = len(posts) > page_size
    posts = posts[:page_size]

    post_responses = []
    for post in posts:
        response = PostResponse(
            id=post.id,
            post_type=post.post_type,
            content_text=post.content_text,
            media_urls=post.media_urls,
            thumbnail_url=post.thumbnail_url,
            view_count=post.view_count,
            like_count=post.like_count,
            comment_count=post.comment_count,
            share_count=post.share_count,
            save_count=post.save_count,
            hashtags=post.hashtags,
            ai_generated=post.ai_generated,
            created_at=post.created_at.isoformat(),
            is_liked=await service.is_post_liked(post.id, current_user.id),
        )
        post_responses.append(response)

    return FeedResponse(
        posts=post_responses,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/trending", response_model=FeedResponse)
async def get_trending_feed(
    db: DB,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get trending posts."""
    service = FeedService(db)

    user_id = current_user.id if current_user else None

    posts = await service.get_feed(
        user_id=user_id,
        feed_type="trending",
        page=page,
        page_size=page_size + 1,
    )

    has_more = len(posts) > page_size
    posts = posts[:page_size]

    post_responses = []
    for post in posts:
        response = PostResponse(
            id=post.id,
            post_type=post.post_type,
            content_text=post.content_text,
            media_urls=post.media_urls,
            thumbnail_url=post.thumbnail_url,
            view_count=post.view_count,
            like_count=post.like_count,
            comment_count=post.comment_count,
            share_count=post.share_count,
            save_count=post.save_count,
            hashtags=post.hashtags,
            ai_generated=post.ai_generated,
            created_at=post.created_at.isoformat(),
        )

        if user_id:
            response.is_liked = await service.is_post_liked(post.id, user_id)

        post_responses.append(response)

    return FeedResponse(
        posts=post_responses,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


# ==================== Create Post (for frontend compatibility) ====================


class CreatePostRequest(BaseModel):
    """Request to create a new post (feed/posts endpoint)."""
    post_type: str = "text"
    content_text: Optional[str] = None
    media_urls: List[str] = []
    thumbnail_url: Optional[str] = None
    hashtags: List[str] = []
    mentions: List[str] = []
    visibility: str = "public"
    ai_generated: bool = False


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post_via_feed(
    request: CreatePostRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a new post via /feed/posts endpoint.
    This is for frontend compatibility - redirects to main posts logic.
    """
    service = FeedService(db)

    post = await service.create_post(
        user_id=current_user.id,
        post_type=request.post_type,
        content_text=request.content_text,
        media_urls=request.media_urls or [],
        thumbnail_url=request.thumbnail_url,
        hashtags=request.hashtags or [],
        mentions=request.mentions or [],
        visibility=request.visibility,
        ai_generated=request.ai_generated,
    )

    return PostResponse(
        id=post.id,
        post_type=post.post_type,
        content_text=post.content_text,
        media_urls=post.media_urls,
        thumbnail_url=post.thumbnail_url,
        view_count=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        share_count=post.share_count,
        save_count=post.save_count,
        hashtags=post.hashtags,
        ai_generated=post.ai_generated,
        created_at=post.created_at.isoformat(),
    )
