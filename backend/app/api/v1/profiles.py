"""
Profiles API Endpoints

User profile management, follow/unfollow, and profile discovery.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser, OptionalUser
from app.models.feed import UserProfile, FeedPost, Follow
from app.services.feed import FeedService

router = APIRouter()


# ==================== Schemas ====================


class ProfileResponse(BaseModel):
    """Public profile response."""

    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    cover_image_url: Optional[str]
    website_url: Optional[str]
    follower_count: int
    following_count: int
    post_count: int
    is_verified: bool
    niche_tags: List[str]
    is_following: bool = False  # Whether current user follows this profile

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Request to update profile."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=500)
    niche_tags: Optional[List[str]] = None


class FollowResponse(BaseModel):
    """Follow action response."""

    success: bool
    follower_count: int
    is_following: bool


class ProfileListResponse(BaseModel):
    """Paginated profile list."""

    profiles: List[ProfileResponse]
    total: int
    page: int
    page_size: int


class PostPreviewResponse(BaseModel):
    """Post preview for profile grid."""

    id: uuid.UUID
    post_type: str
    thumbnail_url: Optional[str]
    media_urls: List[str]
    like_count: int
    comment_count: int
    created_at: str

    class Config:
        from_attributes = True


# ==================== Endpoints ====================


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    db: DB,
    current_user: CurrentUser,
):
    """Get current user's profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete onboarding.",
        )

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=profile.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        website_url=profile.website_url,
        follower_count=profile.follower_count,
        following_count=profile.following_count,
        post_count=profile.post_count,
        is_verified=profile.is_verified,
        niche_tags=profile.niche_tags or [],
        is_following=False,  # Can't follow yourself
    )


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    request: ProfileUpdateRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Update current user's profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Update fields if provided
    if request.display_name is not None:
        profile.display_name = request.display_name
    if request.bio is not None:
        profile.bio = request.bio
    if request.avatar_url is not None:
        profile.avatar_url = request.avatar_url
    if request.cover_image_url is not None:
        profile.cover_image_url = request.cover_image_url
    if request.website_url is not None:
        profile.website_url = request.website_url
    if request.niche_tags is not None:
        profile.niche_tags = request.niche_tags

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=profile.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        website_url=profile.website_url,
        follower_count=profile.follower_count,
        following_count=profile.following_count,
        post_count=profile.post_count,
        is_verified=profile.is_verified,
        niche_tags=profile.niche_tags or [],
        is_following=False,
    )


@router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    db: DB,
    current_user: OptionalUser,
):
    """Get a user's public profile by username."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Check if current user follows this profile
    is_following = False
    if current_user:
        follow_result = await db.execute(
            select(Follow).where(
                Follow.follower_id == current_user.id,
                Follow.following_id == profile.user_id,
            )
        )
        is_following = follow_result.scalar_one_or_none() is not None

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=profile.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        website_url=profile.website_url,
        follower_count=profile.follower_count,
        following_count=profile.following_count,
        post_count=profile.post_count,
        is_verified=profile.is_verified,
        niche_tags=profile.niche_tags or [],
        is_following=is_following,
    )


@router.get("/{username}/posts", response_model=List[PostPreviewResponse])
async def get_user_posts(
    username: str,
    db: DB,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get posts from a user's profile (grid view)."""
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Build query based on visibility
    query = select(FeedPost).where(FeedPost.user_id == profile.user_id)

    if not current_user or current_user.id != profile.user_id:
        # Non-owner can only see public posts
        query = query.where(FeedPost.visibility == "public")

    # Order by pinned first, then by date
    query = (
        query.order_by(FeedPost.is_pinned.desc(), FeedPost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    posts = result.scalars().all()

    return [
        PostPreviewResponse(
            id=post.id,
            post_type=post.post_type,
            thumbnail_url=post.thumbnail_url,
            media_urls=post.media_urls or [],
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at.isoformat(),
        )
        for post in posts
    ]


@router.post("/{username}/follow", response_model=FollowResponse)
async def follow_user(
    username: str,
    db: DB,
    current_user: CurrentUser,
):
    """Follow a user."""
    service = FeedService(db)

    # Get target profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    if profile.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    success = await service.follow_user(current_user.id, profile.user_id)

    # Get updated follower count
    await db.refresh(profile)

    return FollowResponse(
        success=success,
        follower_count=profile.follower_count,
        is_following=True,
    )


@router.delete("/{username}/follow", response_model=FollowResponse)
async def unfollow_user(
    username: str,
    db: DB,
    current_user: CurrentUser,
):
    """Unfollow a user."""
    service = FeedService(db)

    # Get target profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    success = await service.unfollow_user(current_user.id, profile.user_id)

    # Get updated follower count
    await db.refresh(profile)

    return FollowResponse(
        success=success,
        follower_count=profile.follower_count,
        is_following=False,
    )


@router.get("/{username}/followers", response_model=ProfileListResponse)
async def get_followers(
    username: str,
    db: DB,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get a user's followers."""
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(Follow.id)).where(Follow.following_id == profile.user_id)
    )
    total = count_result.scalar() or 0

    # Get follower profiles
    query = (
        select(UserProfile)
        .join(Follow, Follow.follower_id == UserProfile.user_id)
        .where(Follow.following_id == profile.user_id)
        .order_by(Follow.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    followers = result.scalars().all()

    # Check which ones current user follows
    following_ids = set()
    if current_user:
        follow_result = await db.execute(
            select(Follow.following_id).where(Follow.follower_id == current_user.id)
        )
        following_ids = {row[0] for row in follow_result.fetchall()}

    return ProfileListResponse(
        profiles=[
            ProfileResponse(
                id=p.id,
                user_id=p.user_id,
                username=p.username,
                display_name=p.display_name,
                bio=p.bio,
                avatar_url=p.avatar_url,
                cover_image_url=p.cover_image_url,
                website_url=p.website_url,
                follower_count=p.follower_count,
                following_count=p.following_count,
                post_count=p.post_count,
                is_verified=p.is_verified,
                niche_tags=p.niche_tags or [],
                is_following=p.user_id in following_ids,
            )
            for p in followers
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{username}/following", response_model=ProfileListResponse)
async def get_following(
    username: str,
    db: DB,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Get users that a user follows."""
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(Follow.id)).where(Follow.follower_id == profile.user_id)
    )
    total = count_result.scalar() or 0

    # Get following profiles
    query = (
        select(UserProfile)
        .join(Follow, Follow.following_id == UserProfile.user_id)
        .where(Follow.follower_id == profile.user_id)
        .order_by(Follow.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    following = result.scalars().all()

    # Check which ones current user follows
    following_ids = set()
    if current_user:
        follow_result = await db.execute(
            select(Follow.following_id).where(Follow.follower_id == current_user.id)
        )
        following_ids = {row[0] for row in follow_result.fetchall()}

    return ProfileListResponse(
        profiles=[
            ProfileResponse(
                id=p.id,
                user_id=p.user_id,
                username=p.username,
                display_name=p.display_name,
                bio=p.bio,
                avatar_url=p.avatar_url,
                cover_image_url=p.cover_image_url,
                website_url=p.website_url,
                follower_count=p.follower_count,
                following_count=p.following_count,
                post_count=p.post_count,
                is_verified=p.is_verified,
                niche_tags=p.niche_tags or [],
                is_following=p.user_id in following_ids,
            )
            for p in following
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
