"""
Search Models

Data models for search functionality.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID


class SearchResultType(str, Enum):
    """Types of search results."""

    USER = "user"
    POST = "post"
    HASHTAG = "hashtag"
    PODCAST = "podcast"
    CONTENT = "content"
    AI_TWIN = "ai_twin"


class SearchSortBy(str, Enum):
    """Sort options for search results."""

    RELEVANCE = "relevance"
    RECENT = "recent"
    POPULAR = "popular"
    FOLLOWERS = "followers"
    ENGAGEMENT = "engagement"


@dataclass
class SearchFilters:
    """Filters for search queries."""

    types: list[SearchResultType] = field(default_factory=lambda: list(SearchResultType))
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    verified_only: bool = False
    has_media: Optional[bool] = None
    hashtags: list[str] = field(default_factory=list)
    user_id: Optional[UUID] = None  # Filter to specific user's content


@dataclass
class UserSearchResult:
    """User search result."""

    id: UUID
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    follower_count: int
    is_verified: bool
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "follower_count": self.follower_count,
            "is_verified": self.is_verified,
        }


@dataclass
class PostSearchResult:
    """Post search result."""

    id: UUID
    user_id: UUID
    username: str
    user_avatar: Optional[str]
    content_preview: str
    media_urls: list[str]
    thumbnail_url: Optional[str]
    like_count: int
    comment_count: int
    created_at: datetime
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "username": self.username,
            "user_avatar": self.user_avatar,
            "content_preview": self.content_preview,
            "media_urls": self.media_urls,
            "thumbnail_url": self.thumbnail_url,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class HashtagSearchResult:
    """Hashtag search result."""

    id: UUID
    tag: str
    post_count: int
    trending_score: float
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "tag": self.tag,
            "post_count": self.post_count,
            "trending_score": self.trending_score,
        }


@dataclass
class PodcastSearchResult:
    """Podcast search result."""

    id: UUID
    title: str
    description: Optional[str]
    cover_art_url: Optional[str]
    user_id: UUID
    username: str
    episode_count: int
    subscriber_count: int
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "cover_art_url": self.cover_art_url,
            "user_id": str(self.user_id),
            "username": self.username,
            "episode_count": self.episode_count,
            "subscriber_count": self.subscriber_count,
        }


@dataclass
class SearchResult:
    """Unified search result."""

    type: SearchResultType
    data: Any
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "data": self.data.to_dict() if hasattr(self.data, "to_dict") else self.data,
            "relevance_score": self.relevance_score,
        }


@dataclass
class SearchResponse:
    """Complete search response."""

    query: str
    total: int
    results: list[SearchResult]
    page: int
    page_size: int
    has_more: bool
    filters_applied: dict
    search_time_ms: float

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total": self.total,
            "results": [r.to_dict() for r in self.results],
            "page": self.page,
            "page_size": self.page_size,
            "has_more": self.has_more,
            "filters_applied": self.filters_applied,
            "search_time_ms": self.search_time_ms,
        }


@dataclass
class SearchSuggestion:
    """Search autocomplete suggestion."""

    text: str
    type: SearchResultType
    count: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "type": self.type.value,
            "count": self.count,
            "metadata": self.metadata,
        }
