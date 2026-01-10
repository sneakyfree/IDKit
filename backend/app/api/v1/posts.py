"""
Posts API Endpoints

CRUD operations for feed posts, likes, comments, and saves.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser, OptionalUser
from app.services.feed import FeedService

router = APIRouter()


# ==================== Schemas ====================


class CreatePostRequest(BaseModel):
    """Request to create a new post."""

    post_type: str = Field(
        description="Post type: video, image, text, carousel, podcast_clip"
    )
    content_text: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    visibility: str = Field(default="public", description="public, followers, private")
    ai_generated: bool = False


class PostResponse(BaseModel):
    """Post response."""

    id: uuid.UUID
    user_id: uuid.UUID
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
    visibility: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CommentRequest(BaseModel):
    """Request to add a comment."""

    content: str = Field(min_length=1, max_length=2000)
    parent_comment_id: Optional[uuid.UUID] = None


class CommentResponse(BaseModel):
    """Comment response."""

    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    like_count: int
    parent_comment_id: Optional[uuid.UUID]
    created_at: str

    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    """Like action response."""

    success: bool
    like_count: int


class SaveResponse(BaseModel):
    """Save action response."""

    success: bool
    save_count: int


# ==================== Endpoints ====================


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    request: CreatePostRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new post."""
    service = FeedService(db)

    post = await service.create_post(
        user_id=current_user.id,
        post_type=request.post_type,
        content_text=request.content_text,
        media_urls=request.media_urls,
        thumbnail_url=request.thumbnail_url,
        hashtags=request.hashtags,
        mentions=request.mentions,
        visibility=request.visibility,
        ai_generated=request.ai_generated,
    )

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
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
        visibility=post.visibility,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: OptionalUser,
):
    """Get a single post by ID."""
    service = FeedService(db)

    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # Check visibility permissions
    if post.visibility == "private" and (
        not current_user or post.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This post is private",
        )

    if post.visibility == "followers":
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This post is only visible to followers",
            )
        # Check if current_user follows the post author (or is the author)
        if current_user.id != post.user_id:
            is_follower = await service.is_following(
                follower_id=current_user.id,
                following_id=post.user_id,
            )
            if not is_follower:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This post is only visible to followers",
                )

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
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
        visibility=post.visibility,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete a post (only by owner)."""
    service = FeedService(db)

    success = await service.delete_post(post_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or you don't have permission to delete it",
        )


# ==================== Likes ====================


@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Like a post."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    success = await service.like_post(post_id, current_user.id)

    # Get updated like count
    post = await service.get_post(post_id)

    return LikeResponse(success=success, like_count=post.like_count)


@router.delete("/{post_id}/like", response_model=LikeResponse)
async def unlike_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Unlike a post."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    success = await service.unlike_post(post_id, current_user.id)

    # Get updated like count
    post = await service.get_post(post_id)

    return LikeResponse(success=success, like_count=post.like_count)


# ==================== Comments ====================


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: uuid.UUID,
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get comments for a post."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    comments = await service.get_comments(post_id, page, page_size)

    return [
        CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            content=comment.content,
            like_count=comment.like_count,
            parent_comment_id=comment.parent_comment_id,
            created_at=comment.created_at.isoformat(),
        )
        for comment in comments
    ]


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    post_id: uuid.UUID,
    request: CommentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Add a comment to a post."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    comment = await service.add_comment(
        post_id=post_id,
        user_id=current_user.id,
        content=request.content,
        parent_comment_id=request.parent_comment_id,
    )

    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        content=comment.content,
        like_count=comment.like_count,
        parent_comment_id=comment.parent_comment_id,
        created_at=comment.created_at.isoformat(),
    )


# ==================== Saves ====================


@router.post("/{post_id}/save", response_model=SaveResponse)
async def save_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    collection: str = Query(default="Saved"),
):
    """Save a post to a collection."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    success = await service.save_post(post_id, current_user.id, collection)

    # Get updated save count
    post = await service.get_post(post_id)

    return SaveResponse(success=success, save_count=post.save_count)


@router.delete("/{post_id}/save", response_model=SaveResponse)
async def unsave_post(
    post_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    collection: str = Query(default="Saved"),
):
    """Remove a post from saves."""
    service = FeedService(db)

    # Verify post exists
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    success = await service.unsave_post(post_id, current_user.id, collection)

    # Get updated save count
    post = await service.get_post(post_id)

    return SaveResponse(success=success, save_count=post.save_count)
