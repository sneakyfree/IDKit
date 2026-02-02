"""
Discovery API Endpoints

Hashtag discovery, trending topics, user search, and content search.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser, OptionalUser
from app.models.feed import (
    UserProfile,
    FeedPost,
    Hashtag,
    Follow,
)

router = APIRouter()


# ==================== Schemas ====================


class HashtagResponse(BaseModel):
    """Hashtag with stats."""

    id: uuid.UUID
    tag: str
    post_count: int
    trending_score: float

    class Config:
        from_attributes = True


class TrendingHashtagResponse(BaseModel):
    """Trending hashtag with additional context."""

    tag: str
    post_count: int
    trending_score: float
    sample_posts: List[str]  # Post IDs for preview


class UserSearchResult(BaseModel):
    """User search result."""

    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    follower_count: int
    is_verified: bool
    is_following: bool = False

    class Config:
        from_attributes = True


class PostSearchResult(BaseModel):
    """Post search result."""

    id: uuid.UUID
    user_id: uuid.UUID
    post_type: str
    content_text: Optional[str]
    thumbnail_url: Optional[str]
    like_count: int
    comment_count: int
    created_at: str
    author_username: str
    author_avatar_url: Optional[str]

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Combined search response."""

    users: List[UserSearchResult]
    posts: List[PostSearchResult]
    hashtags: List[HashtagResponse]


class SuggestedUserResponse(BaseModel):
    """Suggested user to follow."""

    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    follower_count: int
    is_verified: bool
    mutual_followers: int = 0
    reason: str  # "Popular creator", "Followed by X", etc.

    class Config:
        from_attributes = True


# ==================== Hashtag Endpoints ====================


@router.get("/hashtags/trending", response_model=List[TrendingHashtagResponse])
async def get_trending_hashtags(
    db: DB,
    limit: int = Query(default=20, ge=1, le=50),
):
    """Get trending hashtags ranked by trending score."""
    result = await db.execute(
        select(Hashtag)
        .where(Hashtag.post_count > 0)
        .order_by(desc(Hashtag.trending_score), desc(Hashtag.post_count))
        .limit(limit)
    )
    hashtags = result.scalars().all()

    trending = []
    for tag in hashtags:
        # Get sample post IDs for this hashtag
        posts_result = await db.execute(
            select(FeedPost.id)
            .where(
                FeedPost.hashtags.contains([tag.tag]),
                FeedPost.visibility == "public",
            )
            .order_by(desc(FeedPost.like_count))
            .limit(3)
        )
        sample_posts = [str(row[0]) for row in posts_result.fetchall()]

        trending.append(
            TrendingHashtagResponse(
                tag=tag.tag,
                post_count=tag.post_count,
                trending_score=tag.trending_score,
                sample_posts=sample_posts,
            )
        )

    return trending


@router.get("/hashtags/{tag}", response_model=HashtagResponse)
async def get_hashtag(
    tag: str,
    db: DB,
):
    """Get hashtag details."""
    # Normalize tag (remove # if present, lowercase)
    tag = tag.lstrip("#").lower()

    result = await db.execute(
        select(Hashtag).where(Hashtag.tag == tag)
    )
    hashtag = result.scalar_one_or_none()

    if not hashtag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hashtag not found",
        )

    return hashtag


@router.get("/hashtags/{tag}/posts", response_model=List[PostSearchResult])
async def get_hashtag_posts(
    tag: str,
    db: DB,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    sort: str = Query(default="trending", pattern="^(trending|recent|top)$"),
):
    """Get posts with a specific hashtag."""
    tag = tag.lstrip("#").lower()

    # Build query
    query = select(FeedPost, UserProfile).join(
        UserProfile, FeedPost.user_id == UserProfile.user_id
    ).where(
        FeedPost.hashtags.contains([tag]),
        FeedPost.visibility == "public",
    )

    # Apply sorting
    if sort == "recent":
        query = query.order_by(desc(FeedPost.created_at))
    elif sort == "top":
        query = query.order_by(desc(FeedPost.like_count))
    else:  # trending
        query = query.order_by(desc(FeedPost.trending_score), desc(FeedPost.created_at))

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        PostSearchResult(
            id=post.id,
            user_id=post.user_id,
            post_type=post.post_type,
            content_text=post.content_text,
            thumbnail_url=post.thumbnail_url,
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at.isoformat(),
            author_username=profile.username,
            author_avatar_url=profile.avatar_url,
        )
        for post, profile in rows
    ]


# ==================== Search Endpoints ====================


@router.get("/search", response_model=SearchResponse)
async def search_all(
    q: str = Query(..., min_length=1, max_length=100),
    db: DB = None,
    current_user: OptionalUser = None,
    limit: int = Query(default=10, ge=1, le=20),
):
    """
    Universal search across users, posts, and hashtags.

    Returns top results from each category.
    """
    search_term = q.strip().lower()

    # Search users
    users_result = await db.execute(
        select(UserProfile)
        .where(
            or_(
                UserProfile.username.ilike(f"%{search_term}%"),
                UserProfile.display_name.ilike(f"%{search_term}%"),
            )
        )
        .order_by(desc(UserProfile.follower_count))
        .limit(limit)
    )
    users = users_result.scalars().all()

    # Check following status
    following_ids = set()
    if current_user:
        follow_result = await db.execute(
            select(Follow.following_id).where(Follow.follower_id == current_user.id)
        )
        following_ids = {row[0] for row in follow_result.fetchall()}

    user_results = [
        UserSearchResult(
            id=u.id,
            user_id=u.user_id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            bio=u.bio,
            follower_count=u.follower_count,
            is_verified=u.is_verified,
            is_following=u.user_id in following_ids,
        )
        for u in users
    ]

    # Search posts
    posts_result = await db.execute(
        select(FeedPost, UserProfile)
        .join(UserProfile, FeedPost.user_id == UserProfile.user_id)
        .where(
            FeedPost.visibility == "public",
            FeedPost.content_text.ilike(f"%{search_term}%"),
        )
        .order_by(desc(FeedPost.like_count))
        .limit(limit)
    )
    posts = posts_result.fetchall()

    post_results = [
        PostSearchResult(
            id=post.id,
            user_id=post.user_id,
            post_type=post.post_type,
            content_text=post.content_text,
            thumbnail_url=post.thumbnail_url,
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at.isoformat(),
            author_username=profile.username,
            author_avatar_url=profile.avatar_url,
        )
        for post, profile in posts
    ]

    # Search hashtags
    hashtags_result = await db.execute(
        select(Hashtag)
        .where(Hashtag.tag.ilike(f"%{search_term}%"))
        .order_by(desc(Hashtag.post_count))
        .limit(limit)
    )
    hashtags = hashtags_result.scalars().all()

    return SearchResponse(
        users=user_results,
        posts=post_results,
        hashtags=[
            HashtagResponse(
                id=h.id,
                tag=h.tag,
                post_count=h.post_count,
                trending_score=h.trending_score,
            )
            for h in hashtags
        ],
    )


@router.get("/search/users", response_model=List[UserSearchResult])
async def search_users(
    q: str = Query(..., min_length=1, max_length=100),
    db: DB = None,
    current_user: OptionalUser = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Search users by username or display name."""
    search_term = q.strip().lower()

    result = await db.execute(
        select(UserProfile)
        .where(
            or_(
                UserProfile.username.ilike(f"%{search_term}%"),
                UserProfile.display_name.ilike(f"%{search_term}%"),
            )
        )
        .order_by(desc(UserProfile.follower_count))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()

    # Check following status
    following_ids = set()
    if current_user:
        follow_result = await db.execute(
            select(Follow.following_id).where(Follow.follower_id == current_user.id)
        )
        following_ids = {row[0] for row in follow_result.fetchall()}

    return [
        UserSearchResult(
            id=u.id,
            user_id=u.user_id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            bio=u.bio,
            follower_count=u.follower_count,
            is_verified=u.is_verified,
            is_following=u.user_id in following_ids,
        )
        for u in users
    ]


@router.get("/search/posts", response_model=List[PostSearchResult])
async def search_posts(
    q: str = Query(..., min_length=1, max_length=100),
    db: DB = None,
    current_user: OptionalUser = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    sort: str = Query(default="relevant", pattern="^(relevant|recent|top)$"),
):
    """Search posts by content text."""
    search_term = q.strip().lower()

    query = (
        select(FeedPost, UserProfile)
        .join(UserProfile, FeedPost.user_id == UserProfile.user_id)
        .where(
            FeedPost.visibility == "public",
            FeedPost.content_text.ilike(f"%{search_term}%"),
        )
    )

    if sort == "recent":
        query = query.order_by(desc(FeedPost.created_at))
    elif sort == "top":
        query = query.order_by(desc(FeedPost.like_count))
    else:
        query = query.order_by(desc(FeedPost.engagement_score))

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        PostSearchResult(
            id=post.id,
            user_id=post.user_id,
            post_type=post.post_type,
            content_text=post.content_text,
            thumbnail_url=post.thumbnail_url,
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at.isoformat(),
            author_username=profile.username,
            author_avatar_url=profile.avatar_url,
        )
        for post, profile in rows
    ]


# ==================== User Discovery ====================


@router.get("/suggestions/users", response_model=List[SuggestedUserResponse])
async def get_suggested_users(
    db: DB,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get suggested users to follow.

    Algorithm considers:
    - Popular creators (high follower count)
    - Users followed by people you follow (mutual connections)
    - Users with similar niche tags
    - Verified creators
    """
    suggestions = []

    # Get user's following list
    following_result = await db.execute(
        select(Follow.following_id).where(Follow.follower_id == current_user.id)
    )
    following_ids = {row[0] for row in following_result.fetchall()}
    following_ids.add(current_user.id)  # Exclude self

    # Get current user's profile for niche matching
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    current_profile = profile_result.scalar_one_or_none()
    user_niches = current_profile.niche_tags if current_profile else []

    # 1. Popular verified creators not followed
    popular_result = await db.execute(
        select(UserProfile)
        .where(
            UserProfile.user_id.notin_(following_ids),
            UserProfile.is_verified == True,
        )
        .order_by(desc(UserProfile.follower_count))
        .limit(limit // 2)
    )
    for profile in popular_result.scalars():
        suggestions.append(
            SuggestedUserResponse(
                id=profile.id,
                user_id=profile.user_id,
                username=profile.username,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                bio=profile.bio,
                follower_count=profile.follower_count,
                is_verified=profile.is_verified,
                mutual_followers=0,
                reason="Popular creator",
            )
        )

    # 2. Users with mutual followers (friends of friends)
    if following_ids:
        mutual_result = await db.execute(
            select(
                UserProfile,
                func.count(Follow.follower_id).label("mutual_count"),
            )
            .join(Follow, Follow.following_id == UserProfile.user_id)
            .where(
                Follow.follower_id.in_(following_ids - {current_user.id}),
                UserProfile.user_id.notin_(following_ids),
            )
            .group_by(UserProfile.id)
            .order_by(desc("mutual_count"))
            .limit(limit // 2)
        )

        for profile, mutual_count in mutual_result.fetchall():
            # Avoid duplicates
            if any(s.user_id == profile.user_id for s in suggestions):
                continue

            suggestions.append(
                SuggestedUserResponse(
                    id=profile.id,
                    user_id=profile.user_id,
                    username=profile.username,
                    display_name=profile.display_name,
                    avatar_url=profile.avatar_url,
                    bio=profile.bio,
                    follower_count=profile.follower_count,
                    is_verified=profile.is_verified,
                    mutual_followers=mutual_count,
                    reason=f"Followed by {mutual_count} {'person' if mutual_count == 1 else 'people'} you follow",
                )
            )

    # 3. Fill remaining with high-engagement creators
    if len(suggestions) < limit:
        remaining = limit - len(suggestions)
        existing_ids = {s.user_id for s in suggestions} | following_ids

        filler_result = await db.execute(
            select(UserProfile)
            .where(UserProfile.user_id.notin_(existing_ids))
            .order_by(desc(UserProfile.follower_count))
            .limit(remaining)
        )

        for profile in filler_result.scalars():
            suggestions.append(
                SuggestedUserResponse(
                    id=profile.id,
                    user_id=profile.user_id,
                    username=profile.username,
                    display_name=profile.display_name,
                    avatar_url=profile.avatar_url,
                    bio=profile.bio,
                    follower_count=profile.follower_count,
                    is_verified=profile.is_verified,
                    mutual_followers=0,
                    reason="Rising creator",
                )
            )

    return suggestions[:limit]
