"""
Search API

Unified search endpoints for users, posts, hashtags, podcasts, and content.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_current_user_optional, get_db
from app.models.user import User
from app.services.search import (
    search_service,
    SearchFilters,
    SearchSortBy,
    SearchResultType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class SearchRequest(BaseModel):
    """Search request body for complex searches."""

    query: str = Field(..., min_length=2, max_length=200)
    types: list[str] = Field(default=["user", "post", "hashtag", "podcast"])
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_followers: Optional[int] = Field(None, ge=0)
    max_followers: Optional[int] = Field(None, ge=0)
    verified_only: bool = False
    has_media: Optional[bool] = None
    hashtags: list[str] = Field(default=[])
    sort_by: str = "relevance"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SearchResultItem(BaseModel):
    """Individual search result."""

    type: str
    data: dict
    relevance_score: float


class SearchResponseModel(BaseModel):
    """Search response."""

    query: str
    total: int
    results: list[SearchResultItem]
    page: int
    page_size: int
    has_more: bool
    filters_applied: dict
    search_time_ms: float


class SuggestionItem(BaseModel):
    """Search suggestion item."""

    text: str
    type: str
    count: Optional[int]
    metadata: dict = {}


# =============================================================================
# Search Endpoints
# =============================================================================


@router.get("", response_model=SearchResponseModel)
async def search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    types: str = Query("user,post,hashtag,podcast", description="Comma-separated result types"),
    sort_by: str = Query("relevance", regex="^(relevance|recent|popular|followers|engagement)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    verified_only: bool = Query(False),
    has_media: Optional[bool] = Query(None),
    min_followers: Optional[int] = Query(None, ge=0),
    max_followers: Optional[int] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Search across users, posts, hashtags, and podcasts.

    - **q**: Search query (required, min 2 characters)
    - **types**: Comma-separated list of result types (user, post, hashtag, podcast)
    - **sort_by**: Sort order (relevance, recent, popular, followers, engagement)
    - **verified_only**: Only return verified users
    - **has_media**: Filter posts by media presence
    """
    # Parse types
    type_list = [t.strip() for t in types.split(",") if t.strip()]
    result_types = []
    for t in type_list:
        try:
            result_types.append(SearchResultType(t))
        except ValueError:
            pass

    if not result_types:
        result_types = list(SearchResultType)

    # Build filters
    filters = SearchFilters(
        types=result_types,
        verified_only=verified_only,
        has_media=has_media,
        min_followers=min_followers,
        max_followers=max_followers,
    )

    # Parse sort
    try:
        sort = SearchSortBy(sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    # Execute search
    result = await search_service.search(
        db=db,
        query=q,
        filters=filters,
        sort_by=sort,
        page=page,
        page_size=page_size,
        user_id=current_user.id if current_user else None,
    )

    return SearchResponseModel(
        query=result.query,
        total=result.total,
        results=[
            SearchResultItem(
                type=r.type.value,
                data=r.data.to_dict() if hasattr(r.data, "to_dict") else r.data,
                relevance_score=r.relevance_score,
            )
            for r in result.results
        ],
        page=result.page,
        page_size=result.page_size,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
        search_time_ms=result.search_time_ms,
    )


@router.post("", response_model=SearchResponseModel)
async def search_advanced(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Advanced search with full filter options.

    Use this endpoint for complex searches with date ranges and multiple filters.
    """
    # Parse types
    result_types = []
    for t in request.types:
        try:
            result_types.append(SearchResultType(t))
        except ValueError:
            pass

    if not result_types:
        result_types = list(SearchResultType)

    # Build filters
    filters = SearchFilters(
        types=result_types,
        date_from=request.date_from,
        date_to=request.date_to,
        min_followers=request.min_followers,
        max_followers=request.max_followers,
        verified_only=request.verified_only,
        has_media=request.has_media,
        hashtags=request.hashtags,
    )

    # Parse sort
    try:
        sort = SearchSortBy(request.sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    # Execute search
    result = await search_service.search(
        db=db,
        query=request.query,
        filters=filters,
        sort_by=sort,
        page=request.page,
        page_size=request.page_size,
        user_id=current_user.id if current_user else None,
    )

    return SearchResponseModel(
        query=result.query,
        total=result.total,
        results=[
            SearchResultItem(
                type=r.type.value,
                data=r.data.to_dict() if hasattr(r.data, "to_dict") else r.data,
                relevance_score=r.relevance_score,
            )
            for r in result.results
        ],
        page=result.page,
        page_size=result.page_size,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
        search_time_ms=result.search_time_ms,
    )


@router.get("/users")
async def search_users(
    q: str = Query(..., min_length=2, max_length=200),
    sort_by: str = Query("relevance", regex="^(relevance|followers|recent)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    verified_only: bool = Query(False),
    min_followers: Optional[int] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Search users only.

    Searches usernames, display names, and bios.
    """
    filters = SearchFilters(
        types=[SearchResultType.USER],
        verified_only=verified_only,
        min_followers=min_followers,
    )

    try:
        sort = SearchSortBy(sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    result = await search_service.search(
        db=db,
        query=q,
        filters=filters,
        sort_by=sort,
        page=page,
        page_size=page_size,
        user_id=current_user.id if current_user else None,
    )

    return {
        "query": result.query,
        "total": result.total,
        "users": [
            r.data.to_dict() if hasattr(r.data, "to_dict") else r.data
            for r in result.results
        ],
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more,
    }


@router.get("/posts")
async def search_posts(
    q: str = Query(..., min_length=2, max_length=200),
    sort_by: str = Query("relevance", regex="^(relevance|recent|popular|engagement)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    has_media: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Search posts only.

    Searches post content text.
    """
    filters = SearchFilters(
        types=[SearchResultType.POST],
        has_media=has_media,
    )

    try:
        sort = SearchSortBy(sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    result = await search_service.search(
        db=db,
        query=q,
        filters=filters,
        sort_by=sort,
        page=page,
        page_size=page_size,
        user_id=current_user.id if current_user else None,
    )

    return {
        "query": result.query,
        "total": result.total,
        "posts": [
            r.data.to_dict() if hasattr(r.data, "to_dict") else r.data
            for r in result.results
        ],
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more,
    }


@router.get("/hashtags")
async def search_hashtags(
    q: str = Query(..., min_length=1, max_length=100),
    sort_by: str = Query("relevance", regex="^(relevance|popular)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Search hashtags.

    Returns matching hashtags with post counts.
    """
    filters = SearchFilters(types=[SearchResultType.HASHTAG])

    try:
        sort = SearchSortBy(sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    result = await search_service.search(
        db=db,
        query=q,
        filters=filters,
        sort_by=sort,
        page=page,
        page_size=page_size,
    )

    return {
        "query": result.query,
        "total": result.total,
        "hashtags": [
            r.data.to_dict() if hasattr(r.data, "to_dict") else r.data
            for r in result.results
        ],
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more,
    }


@router.get("/podcasts")
async def search_podcasts(
    q: str = Query(..., min_length=2, max_length=200),
    sort_by: str = Query("relevance", regex="^(relevance|popular|recent)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Search podcasts.

    Searches podcast titles and descriptions.
    """
    filters = SearchFilters(types=[SearchResultType.PODCAST])

    try:
        sort = SearchSortBy(sort_by)
    except ValueError:
        sort = SearchSortBy.RELEVANCE

    result = await search_service.search(
        db=db,
        query=q,
        filters=filters,
        sort_by=sort,
        page=page,
        page_size=page_size,
        user_id=current_user.id if current_user else None,
    )

    return {
        "query": result.query,
        "total": result.total,
        "podcasts": [
            r.data.to_dict() if hasattr(r.data, "to_dict") else r.data
            for r in result.results
        ],
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more,
    }


# =============================================================================
# Suggestions & History Endpoints
# =============================================================================


@router.get("/suggestions", response_model=list[SuggestionItem])
async def get_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Get search autocomplete suggestions.

    Returns suggestions for usernames, hashtags, and popular searches.
    """
    suggestions = await search_service.get_suggestions(
        db=db,
        query=q,
        limit=limit,
    )

    return [
        SuggestionItem(
            text=s.text,
            type=s.type.value,
            count=s.count,
            metadata=s.metadata,
        )
        for s in suggestions
    ]


@router.get("/trending")
async def get_trending_searches(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending search terms.

    Returns popular searches from the last 24 hours.
    """
    trending = await search_service.get_trending_searches(
        db=db,
        limit=limit,
    )

    return {"trending": trending}


@router.get("/recent")
async def get_recent_searches(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's recent searches.

    Returns the user's search history.
    """
    recent = await search_service.get_recent_searches(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    return {"recent_searches": recent}


@router.delete("/recent")
async def clear_recent_searches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear user's search history.
    """
    deleted = await search_service.clear_recent_searches(
        db=db,
        user_id=current_user.id,
    )

    return {"cleared": deleted, "message": "Search history cleared"}
