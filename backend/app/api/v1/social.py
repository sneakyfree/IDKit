"""
Social Media Integration API Endpoints

OAuth connections, publishing, analytics, and engagement management.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, and_

from app.config import settings
from app.dependencies import DB, CurrentUser
from app.models.social import (
    SocialAccount,
    SocialPost,
    PublishQueue,
    SocialComment,
    SocialAnalytics,
    SocialPlatform,
    PostStatus,
)
from app.adapters.youtube import YouTubeAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.interfaces.base import PublishContent, ContentType

router = APIRouter()


# ==================== Schemas ====================


class SocialAccountResponse(BaseModel):
    """Connected social account response."""

    id: uuid.UUID
    platform: str
    platform_user_id: str
    platform_username: Optional[str]
    platform_display_name: Optional[str]
    profile_url: Optional[str]
    profile_image_url: Optional[str]
    account_type: Optional[str]
    follower_count: int
    following_count: int
    is_active: bool
    is_primary: bool
    last_sync_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ConnectAccountRequest(BaseModel):
    """Request to initiate OAuth connection."""

    platform: str = Field(description="Platform to connect: youtube, instagram, tiktok, twitter, facebook, linkedin")
    redirect_uri: Optional[str] = None


class PublishContentRequest(BaseModel):
    """Request to publish content to social platforms."""

    account_id: uuid.UUID
    content_type: str = Field(default="post")  # 'post', 'video', 'reel', 'short', 'story'
    text: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    extras: dict = Field(default_factory=dict)


class SocialPostResponse(BaseModel):
    """Published post response."""

    id: uuid.UUID
    social_account_id: uuid.UUID
    platform: str
    post_type: str
    content_text: Optional[str]
    media_urls: List[str]
    platform_post_id: Optional[str]
    platform_post_url: Optional[str]
    status: str
    scheduled_at: Optional[str]
    published_at: Optional[str]
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    created_at: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Social comment response."""

    id: uuid.UUID
    platform: str
    author_username: Optional[str]
    author_display_name: Optional[str]
    author_avatar_url: Optional[str]
    content: str
    like_count: int
    reply_count: int
    sentiment: Optional[str]
    is_read: bool
    is_replied: bool
    posted_at: str
    created_at: str

    class Config:
        from_attributes = True


class ReplyRequest(BaseModel):
    """Request to reply to a comment."""

    text: str = Field(min_length=1, max_length=2000)


class AnalyticsResponse(BaseModel):
    """Analytics data response."""

    date: str
    follower_count: int
    follower_change: int
    total_reach: int
    total_impressions: int
    total_engagements: int
    engagement_rate: float
    likes_received: int
    comments_received: int
    shares_received: int
    profile_visits: int

    class Config:
        from_attributes = True


# ==================== Helper Functions ====================


def get_adapter(platform: str):
    """Get the appropriate platform adapter."""
    adapters = {
        "youtube": YouTubeAdapter(),
        "instagram": InstagramAdapter(),
        # Add more adapters as implemented
    }
    adapter = adapters.get(platform.lower())
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{platform}' is not supported",
        )
    return adapter


async def get_account_with_valid_token(
    db: DB,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SocialAccount:
    """Get account and refresh token if needed."""
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found",
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Social account is not active",
        )

    # Check if token needs refresh
    if account.token_expires_at and account.token_expires_at < datetime.now(timezone.utc):
        if account.refresh_token:
            adapter = get_adapter(account.platform)
            try:
                new_tokens = await adapter.refresh_token(account.refresh_token)
                account.access_token = new_tokens.access_token
                if new_tokens.refresh_token:
                    account.refresh_token = new_tokens.refresh_token
                account.token_expires_at = new_tokens.expires_at
                await db.commit()
            except Exception as e:
                account.is_active = False
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token refresh failed: {e}. Please reconnect the account.",
                )
        else:
            account.is_active = False
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please reconnect the account.",
            )

    return account


# ==================== OAuth Endpoints ====================


@router.get("/connect/{platform}")
async def initiate_oauth(
    platform: str,
    request: Request,
    current_user: CurrentUser,
    redirect_uri: Optional[str] = None,
):
    """
    Initiate OAuth flow for a social platform.

    Returns a redirect URL to the platform's authorization page.
    """
    adapter = get_adapter(platform)

    # Generate state token for CSRF protection
    import secrets
    state = f"{current_user.id}:{secrets.token_urlsafe(32)}"

    # Store state in session or Redis for validation
    # For now, we'll encode user_id in state (not production-ready)

    callback_uri = redirect_uri or f"{settings.frontend_url}/api/v1/social/callback/{platform}"

    auth_url = adapter.get_authorization_url(
        redirect_uri=callback_uri,
        state=state,
    )

    return {"authorization_url": auth_url, "state": state}


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str,
    state: str,
    db: DB,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handle OAuth callback from social platform.

    Exchanges code for tokens and creates/updates social account.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error} - {error_description}",
        )

    # Extract user_id from state
    try:
        user_id_str = state.split(":")[0]
        user_id = uuid.UUID(user_id_str)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token",
        )

    adapter = get_adapter(platform)
    callback_uri = f"{settings.frontend_url}/api/v1/social/callback/{platform}"

    try:
        # Exchange code for tokens
        tokens = await adapter.exchange_code(code, callback_uri)

        # Get account info
        account_info = await adapter.get_account_info(tokens.access_token)

        # Check if account already exists
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == platform,
                SocialAccount.platform_user_id == account_info.platform_user_id,
            )
        )
        existing_account = result.scalar_one_or_none()

        if existing_account:
            # Update existing account
            existing_account.access_token = tokens.access_token
            existing_account.refresh_token = tokens.refresh_token
            existing_account.token_expires_at = tokens.expires_at
            existing_account.token_scope = tokens.scope
            existing_account.platform_username = account_info.username
            existing_account.platform_display_name = account_info.display_name
            existing_account.profile_url = account_info.profile_url
            existing_account.profile_image_url = account_info.profile_image_url
            existing_account.follower_count = account_info.follower_count
            existing_account.following_count = account_info.following_count
            existing_account.capabilities = account_info.capabilities
            existing_account.is_active = True
            existing_account.last_sync_at = datetime.now(timezone.utc)
            account = existing_account
        else:
            # Create new account
            account = SocialAccount(
                user_id=user_id,
                platform=platform,
                platform_user_id=account_info.platform_user_id,
                platform_username=account_info.username,
                platform_display_name=account_info.display_name,
                profile_url=account_info.profile_url,
                profile_image_url=account_info.profile_image_url,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_expires_at=tokens.expires_at,
                token_scope=tokens.scope,
                account_type=account_info.account_type,
                follower_count=account_info.follower_count,
                following_count=account_info.following_count,
                capabilities=account_info.capabilities,
                last_sync_at=datetime.now(timezone.utc),
            )
            db.add(account)

        await db.commit()

        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{settings.frontend_url}/settings/social?connected={platform}&success=true"
        )

    except Exception as e:
        return RedirectResponse(
            url=f"{settings.frontend_url}/settings/social?error={str(e)}"
        )


# ==================== Account Management ====================


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_accounts(
    db: DB,
    current_user: CurrentUser,
    platform: Optional[str] = None,
):
    """List connected social accounts."""
    query = select(SocialAccount).where(SocialAccount.user_id == current_user.id)

    if platform:
        query = query.where(SocialAccount.platform == platform)

    query = query.order_by(desc(SocialAccount.created_at))

    result = await db.execute(query)
    accounts = result.scalars().all()

    return [
        SocialAccountResponse(
            id=a.id,
            platform=a.platform,
            platform_user_id=a.platform_user_id,
            platform_username=a.platform_username,
            platform_display_name=a.platform_display_name,
            profile_url=a.profile_url,
            profile_image_url=a.profile_image_url,
            account_type=a.account_type,
            follower_count=a.follower_count,
            following_count=a.following_count,
            is_active=a.is_active,
            is_primary=a.is_primary,
            last_sync_at=a.last_sync_at.isoformat() if a.last_sync_at else None,
            created_at=a.created_at.isoformat(),
        )
        for a in accounts
    ]


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(
    account_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Disconnect a social account."""
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found",
        )

    await db.delete(account)
    await db.commit()


@router.post("/accounts/{account_id}/sync")
async def sync_account(
    account_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Sync account data from platform."""
    account = await get_account_with_valid_token(db, account_id, current_user.id)
    adapter = get_adapter(account.platform)

    try:
        account_info = await adapter.get_account_info(account.access_token)

        account.platform_username = account_info.username
        account.platform_display_name = account_info.display_name
        account.profile_url = account_info.profile_url
        account.profile_image_url = account_info.profile_image_url
        account.follower_count = account_info.follower_count
        account.following_count = account_info.following_count
        account.capabilities = account_info.capabilities
        account.last_sync_at = datetime.now(timezone.utc)

        await db.commit()

        return {"status": "synced", "follower_count": account.follower_count}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {e}",
        )


# ==================== Publishing ====================


@router.post("/publish", response_model=SocialPostResponse)
async def publish_content(
    request: PublishContentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Publish content to a connected social account."""
    account = await get_account_with_valid_token(db, request.account_id, current_user.id)
    adapter = get_adapter(account.platform)

    # Map content type
    content_type_map = {
        "post": ContentType.POST,
        "video": ContentType.VIDEO,
        "reel": ContentType.REEL,
        "short": ContentType.SHORT,
        "story": ContentType.STORY,
        "carousel": ContentType.CAROUSEL,
    }
    content_type = content_type_map.get(request.content_type.lower(), ContentType.POST)

    # Create content object
    content = PublishContent(
        content_type=content_type,
        text=request.text,
        media_urls=request.media_urls,
        hashtags=request.hashtags,
        scheduled_at=request.scheduled_at,
        extras=request.extras,
    )

    # Create post record
    post = SocialPost(
        user_id=current_user.id,
        social_account_id=account.id,
        platform=account.platform,
        post_type=request.content_type,
        content_text=request.text,
        media_urls=request.media_urls,
        hashtags=request.hashtags,
        status=PostStatus.SCHEDULED.value if request.scheduled_at else PostStatus.PUBLISHING.value,
        scheduled_at=request.scheduled_at,
    )
    db.add(post)
    await db.flush()

    if request.scheduled_at:
        # Add to publish queue
        queue_item = PublishQueue(
            social_post_id=post.id,
            scheduled_for=request.scheduled_at,
        )
        db.add(queue_item)
        await db.commit()
        await db.refresh(post)
    else:
        # Publish immediately
        try:
            result = await adapter.publish(account.access_token, content)

            if result.success:
                post.status = PostStatus.PUBLISHED.value
                post.platform_post_id = result.platform_post_id
                post.platform_post_url = result.platform_post_url
                post.published_at = datetime.now(timezone.utc)
                post.platform_metadata = result.metadata
            else:
                post.status = PostStatus.FAILED.value
                post.error_message = result.error_message

            await db.commit()
            await db.refresh(post)

        except Exception as e:
            post.status = PostStatus.FAILED.value
            post.error_message = str(e)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Publishing failed: {e}",
            )

    return SocialPostResponse(
        id=post.id,
        social_account_id=post.social_account_id,
        platform=post.platform,
        post_type=post.post_type,
        content_text=post.content_text,
        media_urls=post.media_urls,
        platform_post_id=post.platform_post_id,
        platform_post_url=post.platform_post_url,
        status=post.status,
        scheduled_at=post.scheduled_at.isoformat() if post.scheduled_at else None,
        published_at=post.published_at.isoformat() if post.published_at else None,
        view_count=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        share_count=post.share_count,
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=List[SocialPostResponse])
async def list_posts(
    db: DB,
    current_user: CurrentUser,
    account_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """List published and scheduled posts."""
    query = select(SocialPost).where(SocialPost.user_id == current_user.id)

    if account_id:
        query = query.where(SocialPost.social_account_id == account_id)

    if status_filter:
        query = query.where(SocialPost.status == status_filter)

    query = query.order_by(desc(SocialPost.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    return [
        SocialPostResponse(
            id=p.id,
            social_account_id=p.social_account_id,
            platform=p.platform,
            post_type=p.post_type,
            content_text=p.content_text,
            media_urls=p.media_urls,
            platform_post_id=p.platform_post_id,
            platform_post_url=p.platform_post_url,
            status=p.status,
            scheduled_at=p.scheduled_at.isoformat() if p.scheduled_at else None,
            published_at=p.published_at.isoformat() if p.published_at else None,
            view_count=p.view_count,
            like_count=p.like_count,
            comment_count=p.comment_count,
            share_count=p.share_count,
            created_at=p.created_at.isoformat(),
        )
        for p in posts
    ]


# ==================== Comments ====================


@router.get("/comments", response_model=List[CommentResponse])
async def list_comments(
    db: DB,
    current_user: CurrentUser,
    platform: Optional[str] = None,
    is_unread: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """List comments from all connected accounts (unified inbox)."""
    query = select(SocialComment).where(SocialComment.user_id == current_user.id)

    if platform:
        query = query.where(SocialComment.platform == platform)

    if is_unread is not None:
        query = query.where(SocialComment.is_read == (not is_unread))

    query = query.order_by(desc(SocialComment.posted_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    comments = result.scalars().all()

    return [
        CommentResponse(
            id=c.id,
            platform=c.platform,
            author_username=c.author_username,
            author_display_name=c.author_display_name,
            author_avatar_url=c.author_avatar_url,
            content=c.content,
            like_count=c.like_count,
            reply_count=c.reply_count,
            sentiment=c.sentiment,
            is_read=c.is_read,
            is_replied=c.is_replied,
            posted_at=c.posted_at.isoformat(),
            created_at=c.created_at.isoformat(),
        )
        for c in comments
    ]


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: uuid.UUID,
    request: ReplyRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Reply to a comment."""
    result = await db.execute(
        select(SocialComment).where(
            SocialComment.id == comment_id,
            SocialComment.user_id == current_user.id,
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Get the social post to find the account
    post_result = await db.execute(
        select(SocialPost).where(SocialPost.id == comment.social_post_id)
    )
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated post not found",
        )

    account = await get_account_with_valid_token(db, post.social_account_id, current_user.id)
    adapter = get_adapter(account.platform)

    try:
        reply = await adapter.reply_to_comment(
            account.access_token,
            comment.platform_comment_id,
            request.text,
        )

        comment.is_replied = True
        await db.commit()

        return {"status": "replied", "reply_id": reply.platform_comment_id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reply failed: {e}",
        )


@router.post("/comments/{comment_id}/read")
async def mark_comment_read(
    comment_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Mark a comment as read."""
    result = await db.execute(
        select(SocialComment).where(
            SocialComment.id == comment_id,
            SocialComment.user_id == current_user.id,
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    comment.is_read = True
    await db.commit()

    return {"status": "marked_read"}


# ==================== Analytics ====================


@router.get("/analytics/overview")
async def get_analytics_overview(
    db: DB,
    current_user: CurrentUser,
):
    """Get unified analytics overview across all connected accounts."""
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True,
        )
    )
    accounts = result.scalars().all()

    total_followers = sum(a.follower_count for a in accounts)
    total_following = sum(a.following_count for a in accounts)

    platforms = {}
    for account in accounts:
        if account.platform not in platforms:
            platforms[account.platform] = {
                "accounts": 0,
                "followers": 0,
            }
        platforms[account.platform]["accounts"] += 1
        platforms[account.platform]["followers"] += account.follower_count

    return {
        "total_accounts": len(accounts),
        "total_followers": total_followers,
        "total_following": total_following,
        "platforms": platforms,
    }

@router.get("/analytics/{account_id}", response_model=List[AnalyticsResponse])
async def get_analytics(
    account_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=90),
):
    """Get analytics for a social account."""
    account = await get_account_with_valid_token(db, account_id, current_user.id)

    # Check if we have recent cached analytics
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(SocialAnalytics)
        .where(
            SocialAnalytics.social_account_id == account_id,
            SocialAnalytics.date >= start_date,
            SocialAnalytics.date <= end_date,
        )
        .order_by(SocialAnalytics.date)
    )
    cached_analytics = result.scalars().all()

    # If we have recent data, return it
    if cached_analytics:
        return [
            AnalyticsResponse(
                date=a.date.isoformat(),
                follower_count=a.follower_count,
                follower_change=a.follower_change,
                total_reach=a.total_reach,
                total_impressions=a.total_impressions,
                total_engagements=a.total_engagements,
                engagement_rate=a.engagement_rate,
                likes_received=a.likes_received,
                comments_received=a.comments_received,
                shares_received=a.shares_received,
                profile_visits=a.profile_visits,
            )
            for a in cached_analytics
        ]

    # Otherwise, fetch fresh data
    adapter = get_adapter(account.platform)

    try:
        analytics_data = await adapter.get_analytics(
            account.access_token,
            start_date,
            end_date,
        )

        # Cache the results
        for data in analytics_data:
            analytics = SocialAnalytics(
                social_account_id=account_id,
                date=data.date,
                follower_count=data.follower_count,
                follower_change=data.follower_change,
                total_reach=data.total_reach,
                total_impressions=data.total_impressions,
                total_engagements=data.total_engagements,
                engagement_rate=data.engagement_rate,
                likes_received=data.likes_received,
                comments_received=data.comments_received,
                shares_received=data.shares_received,
                profile_visits=data.profile_visits,
            )
            db.add(analytics)

        await db.commit()

        return [
            AnalyticsResponse(
                date=d.date.isoformat(),
                follower_count=d.follower_count,
                follower_change=d.follower_change,
                total_reach=d.total_reach,
                total_impressions=d.total_impressions,
                total_engagements=d.total_engagements,
                engagement_rate=d.engagement_rate,
                likes_received=d.likes_received,
                comments_received=d.comments_received,
                shares_received=d.shares_received,
                profile_visits=d.profile_visits,
            )
            for d in analytics_data
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {e}",
        )

