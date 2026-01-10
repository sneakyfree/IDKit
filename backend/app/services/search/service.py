"""
Search Service

Unified search across all content types with relevance ranking.
"""

import logging
import re
import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import text, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import (
    SearchResult,
    SearchResultType,
    SearchFilters,
    SearchSortBy,
    SearchResponse,
    SearchSuggestion,
    UserSearchResult,
    PostSearchResult,
    HashtagSearchResult,
    PodcastSearchResult,
)

logger = logging.getLogger(__name__)


class SearchService:
    """
    Unified search service for IDKit platform.

    Supports:
    - Full-text search across users, posts, hashtags, podcasts
    - Relevance ranking
    - Filtering and sorting
    - Autocomplete suggestions
    - Recent searches
    """

    def __init__(self):
        self._stopwords = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "has", "he", "in", "is", "it", "its", "of", "on",
            "that", "the", "to", "was", "were", "will", "with",
        }

    # =========================================================================
    # Main Search Methods
    # =========================================================================

    async def search(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort_by: SearchSortBy = SearchSortBy.RELEVANCE,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
    ) -> SearchResponse:
        """
        Perform unified search across all content types.

        Args:
            db: Database session
            query: Search query string
            filters: Optional filters
            sort_by: Sort order
            page: Page number
            page_size: Results per page
            user_id: Current user ID (for personalization)

        Returns:
            SearchResponse with results
        """
        start_time = time.time()

        if not query or len(query.strip()) < 2:
            return SearchResponse(
                query=query,
                total=0,
                results=[],
                page=page,
                page_size=page_size,
                has_more=False,
                filters_applied={},
                search_time_ms=0,
            )

        filters = filters or SearchFilters()
        cleaned_query = self._clean_query(query)
        search_terms = self._tokenize_query(cleaned_query)

        results: list[SearchResult] = []
        total = 0

        # Search each content type based on filters
        if SearchResultType.USER in filters.types:
            user_results, user_total = await self._search_users(
                db, search_terms, cleaned_query, filters, sort_by, page, page_size
            )
            results.extend(user_results)
            total += user_total

        if SearchResultType.POST in filters.types:
            post_results, post_total = await self._search_posts(
                db, search_terms, cleaned_query, filters, sort_by, page, page_size
            )
            results.extend(post_results)
            total += post_total

        if SearchResultType.HASHTAG in filters.types:
            hashtag_results, hashtag_total = await self._search_hashtags(
                db, search_terms, cleaned_query, filters, sort_by, page, page_size
            )
            results.extend(hashtag_results)
            total += hashtag_total

        if SearchResultType.PODCAST in filters.types:
            podcast_results, podcast_total = await self._search_podcasts(
                db, search_terms, cleaned_query, filters, sort_by, page, page_size
            )
            results.extend(podcast_results)
            total += podcast_total

        # Sort combined results by relevance
        if sort_by == SearchSortBy.RELEVANCE:
            results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Apply pagination to combined results
        offset = (page - 1) * page_size
        paginated_results = results[offset:offset + page_size]

        # Log search for analytics (async)
        if user_id:
            await self._log_search(db, user_id, query, len(results))

        search_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query,
            total=total,
            results=paginated_results,
            page=page,
            page_size=page_size,
            has_more=total > offset + page_size,
            filters_applied=self._filters_to_dict(filters),
            search_time_ms=round(search_time_ms, 2),
        )

    async def get_suggestions(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
    ) -> list[SearchSuggestion]:
        """
        Get autocomplete suggestions for a partial query.

        Args:
            db: Database session
            query: Partial query string
            limit: Maximum suggestions

        Returns:
            List of suggestions
        """
        if not query or len(query.strip()) < 2:
            return []

        query = query.strip().lower()
        suggestions: list[SearchSuggestion] = []

        # Search usernames
        user_result = await db.execute(
            text("""
                SELECT username, display_name, follower_count
                FROM users u
                JOIN user_profiles up ON u.id = up.user_id
                WHERE u.username ILIKE :query || '%'
                AND u.is_active = true
                ORDER BY up.follower_count DESC
                LIMIT :limit
            """),
            {"query": query, "limit": limit // 3},
        )
        for row in user_result.fetchall():
            suggestions.append(
                SearchSuggestion(
                    text=f"@{row.username}",
                    type=SearchResultType.USER,
                    count=row.follower_count,
                    metadata={"display_name": row.display_name},
                )
            )

        # Search hashtags
        hashtag_result = await db.execute(
            text("""
                SELECT tag, post_count
                FROM hashtags
                WHERE tag ILIKE :query || '%'
                ORDER BY post_count DESC
                LIMIT :limit
            """),
            {"query": query, "limit": limit // 3},
        )
        for row in hashtag_result.fetchall():
            suggestions.append(
                SearchSuggestion(
                    text=f"#{row.tag}",
                    type=SearchResultType.HASHTAG,
                    count=row.post_count,
                )
            )

        # Search recent/popular searches
        popular_result = await db.execute(
            text("""
                SELECT query, COUNT(*) as count
                FROM search_logs
                WHERE query ILIKE :query || '%'
                AND created_at > NOW() - INTERVAL '7 days'
                GROUP BY query
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": query, "limit": limit // 3},
        )
        for row in popular_result.fetchall():
            if not any(s.text.lower() == row.query.lower() for s in suggestions):
                suggestions.append(
                    SearchSuggestion(
                        text=row.query,
                        type=SearchResultType.POST,
                        count=row.count,
                    )
                )

        return suggestions[:limit]

    async def get_trending_searches(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get trending search terms.

        Args:
            db: Database session
            limit: Maximum results

        Returns:
            List of trending searches
        """
        result = await db.execute(
            text("""
                SELECT query, COUNT(*) as search_count
                FROM search_logs
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY query
                ORDER BY search_count DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )

        return [
            {"query": row.query, "count": row.search_count}
            for row in result.fetchall()
        ]

    async def get_recent_searches(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get user's recent searches.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum results

        Returns:
            List of recent searches
        """
        result = await db.execute(
            text("""
                SELECT DISTINCT ON (query) query, created_at
                FROM search_logs
                WHERE user_id = :user_id
                ORDER BY query, created_at DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "limit": limit},
        )

        return [
            {"query": row.query, "searched_at": row.created_at.isoformat()}
            for row in result.fetchall()
        ]

    async def clear_recent_searches(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Clear user's recent search history."""
        result = await db.execute(
            text("DELETE FROM search_logs WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        await db.commit()
        return result.rowcount

    # =========================================================================
    # Content-Specific Search Methods
    # =========================================================================

    async def _search_users(
        self,
        db: AsyncSession,
        search_terms: list[str],
        query: str,
        filters: SearchFilters,
        sort_by: SearchSortBy,
        page: int,
        page_size: int,
    ) -> tuple[list[SearchResult], int]:
        """Search users."""
        # Build search condition
        search_pattern = f"%{query}%"

        # Build filter conditions
        filter_conditions = ["u.is_active = true"]
        params = {"query": search_pattern, "limit": page_size, "offset": (page - 1) * page_size}

        if filters.verified_only:
            filter_conditions.append("up.is_verified = true")

        if filters.min_followers:
            filter_conditions.append("up.follower_count >= :min_followers")
            params["min_followers"] = filters.min_followers

        if filters.max_followers:
            filter_conditions.append("up.follower_count <= :max_followers")
            params["max_followers"] = filters.max_followers

        where_clause = " AND ".join(filter_conditions)

        # Determine sort
        order_by = "relevance_score DESC"
        if sort_by == SearchSortBy.FOLLOWERS:
            order_by = "up.follower_count DESC"
        elif sort_by == SearchSortBy.RECENT:
            order_by = "u.created_at DESC"

        result = await db.execute(
            text(f"""
                SELECT
                    u.id, u.username, up.display_name, up.avatar_url, up.bio,
                    up.follower_count, up.is_verified,
                    CASE
                        WHEN u.username ILIKE :query THEN 1.0
                        WHEN up.display_name ILIKE :query THEN 0.9
                        WHEN up.bio ILIKE :query THEN 0.5
                        ELSE 0.3
                    END as relevance_score
                FROM users u
                JOIN user_profiles up ON u.id = up.user_id
                WHERE (u.username ILIKE :query OR up.display_name ILIKE :query OR up.bio ILIKE :query)
                AND {where_clause}
                ORDER BY {order_by}
                LIMIT :limit OFFSET :offset
            """),
            params,
        )

        users = result.fetchall()
        results = []

        for u in users:
            user_result = UserSearchResult(
                id=u.id,
                username=u.username,
                display_name=u.display_name,
                avatar_url=u.avatar_url,
                bio=u.bio[:200] if u.bio else None,
                follower_count=u.follower_count,
                is_verified=u.is_verified,
                relevance_score=u.relevance_score,
            )
            results.append(
                SearchResult(
                    type=SearchResultType.USER,
                    data=user_result,
                    relevance_score=u.relevance_score,
                )
            )

        # Get total count
        count_result = await db.execute(
            text(f"""
                SELECT COUNT(*) FROM users u
                JOIN user_profiles up ON u.id = up.user_id
                WHERE (u.username ILIKE :query OR up.display_name ILIKE :query OR up.bio ILIKE :query)
                AND {where_clause}
            """),
            params,
        )
        total = count_result.scalar() or 0

        return results, total

    async def _search_posts(
        self,
        db: AsyncSession,
        search_terms: list[str],
        query: str,
        filters: SearchFilters,
        sort_by: SearchSortBy,
        page: int,
        page_size: int,
    ) -> tuple[list[SearchResult], int]:
        """Search posts."""
        search_pattern = f"%{query}%"

        filter_conditions = ["fp.visibility = 'public'"]
        params = {"query": search_pattern, "limit": page_size, "offset": (page - 1) * page_size}

        if filters.date_from:
            filter_conditions.append("fp.created_at >= :date_from")
            params["date_from"] = filters.date_from

        if filters.date_to:
            filter_conditions.append("fp.created_at <= :date_to")
            params["date_to"] = filters.date_to

        if filters.has_media is not None:
            if filters.has_media:
                filter_conditions.append("jsonb_array_length(fp.media_urls) > 0")
            else:
                filter_conditions.append("jsonb_array_length(fp.media_urls) = 0")

        if filters.user_id:
            filter_conditions.append("fp.user_id = :filter_user_id")
            params["filter_user_id"] = filters.user_id

        where_clause = " AND ".join(filter_conditions)

        # Determine sort
        order_by = "relevance_score DESC"
        if sort_by == SearchSortBy.RECENT:
            order_by = "fp.created_at DESC"
        elif sort_by == SearchSortBy.POPULAR:
            order_by = "fp.engagement_score DESC"
        elif sort_by == SearchSortBy.ENGAGEMENT:
            order_by = "(fp.like_count + fp.comment_count * 2) DESC"

        result = await db.execute(
            text(f"""
                SELECT
                    fp.id, fp.user_id, u.username, up.avatar_url,
                    LEFT(fp.content_text, 200) as content_preview,
                    fp.media_urls, fp.thumbnail_url,
                    fp.like_count, fp.comment_count, fp.created_at,
                    CASE
                        WHEN fp.content_text ILIKE :query THEN 0.8
                        ELSE 0.5
                    END as relevance_score
                FROM feed_posts fp
                JOIN users u ON fp.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE fp.content_text ILIKE :query
                AND {where_clause}
                ORDER BY {order_by}
                LIMIT :limit OFFSET :offset
            """),
            params,
        )

        posts = result.fetchall()
        results = []

        for p in posts:
            post_result = PostSearchResult(
                id=p.id,
                user_id=p.user_id,
                username=p.username,
                user_avatar=p.avatar_url,
                content_preview=p.content_preview or "",
                media_urls=p.media_urls or [],
                thumbnail_url=p.thumbnail_url,
                like_count=p.like_count,
                comment_count=p.comment_count,
                created_at=p.created_at,
                relevance_score=p.relevance_score,
            )
            results.append(
                SearchResult(
                    type=SearchResultType.POST,
                    data=post_result,
                    relevance_score=p.relevance_score,
                )
            )

        # Get total count
        count_result = await db.execute(
            text(f"""
                SELECT COUNT(*) FROM feed_posts fp
                WHERE fp.content_text ILIKE :query
                AND {where_clause}
            """),
            params,
        )
        total = count_result.scalar() or 0

        return results, total

    async def _search_hashtags(
        self,
        db: AsyncSession,
        search_terms: list[str],
        query: str,
        filters: SearchFilters,
        sort_by: SearchSortBy,
        page: int,
        page_size: int,
    ) -> tuple[list[SearchResult], int]:
        """Search hashtags."""
        # Remove # if present
        clean_query = query.lstrip("#")
        search_pattern = f"%{clean_query}%"

        order_by = "relevance_score DESC"
        if sort_by == SearchSortBy.POPULAR:
            order_by = "h.post_count DESC"

        result = await db.execute(
            text(f"""
                SELECT
                    h.id, h.tag, h.post_count, h.trending_score,
                    CASE
                        WHEN h.tag ILIKE :exact THEN 1.0
                        WHEN h.tag ILIKE :query THEN 0.7
                        ELSE 0.5
                    END as relevance_score
                FROM hashtags h
                WHERE h.tag ILIKE :query
                ORDER BY {order_by}
                LIMIT :limit OFFSET :offset
            """),
            {
                "query": search_pattern,
                "exact": clean_query,
                "limit": page_size,
                "offset": (page - 1) * page_size,
            },
        )

        hashtags = result.fetchall()
        results = []

        for h in hashtags:
            hashtag_result = HashtagSearchResult(
                id=h.id,
                tag=h.tag,
                post_count=h.post_count,
                trending_score=h.trending_score,
                relevance_score=h.relevance_score,
            )
            results.append(
                SearchResult(
                    type=SearchResultType.HASHTAG,
                    data=hashtag_result,
                    relevance_score=h.relevance_score,
                )
            )

        # Get total count
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM hashtags WHERE tag ILIKE :query"),
            {"query": search_pattern},
        )
        total = count_result.scalar() or 0

        return results, total

    async def _search_podcasts(
        self,
        db: AsyncSession,
        search_terms: list[str],
        query: str,
        filters: SearchFilters,
        sort_by: SearchSortBy,
        page: int,
        page_size: int,
    ) -> tuple[list[SearchResult], int]:
        """Search podcasts."""
        search_pattern = f"%{query}%"

        order_by = "relevance_score DESC"
        if sort_by == SearchSortBy.POPULAR:
            order_by = "p.subscriber_count DESC"
        elif sort_by == SearchSortBy.RECENT:
            order_by = "p.created_at DESC"

        result = await db.execute(
            text(f"""
                SELECT
                    p.id, p.title, p.description, p.cover_art_url,
                    p.user_id, u.username, p.episode_count, p.subscriber_count,
                    CASE
                        WHEN p.title ILIKE :query THEN 1.0
                        WHEN p.description ILIKE :query THEN 0.7
                        ELSE 0.5
                    END as relevance_score
                FROM podcasts p
                JOIN users u ON p.user_id = u.id
                WHERE (p.title ILIKE :query OR p.description ILIKE :query)
                ORDER BY {order_by}
                LIMIT :limit OFFSET :offset
            """),
            {
                "query": search_pattern,
                "limit": page_size,
                "offset": (page - 1) * page_size,
            },
        )

        podcasts = result.fetchall()
        results = []

        for p in podcasts:
            podcast_result = PodcastSearchResult(
                id=p.id,
                title=p.title,
                description=p.description[:200] if p.description else None,
                cover_art_url=p.cover_art_url,
                user_id=p.user_id,
                username=p.username,
                episode_count=p.episode_count,
                subscriber_count=p.subscriber_count,
                relevance_score=p.relevance_score,
            )
            results.append(
                SearchResult(
                    type=SearchResultType.PODCAST,
                    data=podcast_result,
                    relevance_score=p.relevance_score,
                )
            )

        # Get total count
        count_result = await db.execute(
            text("""
                SELECT COUNT(*) FROM podcasts p
                WHERE (p.title ILIKE :query OR p.description ILIKE :query)
            """),
            {"query": search_pattern},
        )
        total = count_result.scalar() or 0

        return results, total

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _clean_query(self, query: str) -> str:
        """Clean and normalize search query."""
        # Remove special characters except @ and #
        query = re.sub(r"[^\w\s@#-]", "", query)
        # Normalize whitespace
        query = " ".join(query.split())
        return query.strip()

    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize query into search terms."""
        terms = query.lower().split()
        # Remove stopwords for relevance
        return [t for t in terms if t not in self._stopwords and len(t) > 1]

    def _filters_to_dict(self, filters: SearchFilters) -> dict:
        """Convert filters to dictionary for response."""
        return {
            "types": [t.value for t in filters.types],
            "date_from": filters.date_from.isoformat() if filters.date_from else None,
            "date_to": filters.date_to.isoformat() if filters.date_to else None,
            "min_followers": filters.min_followers,
            "max_followers": filters.max_followers,
            "verified_only": filters.verified_only,
            "has_media": filters.has_media,
            "hashtags": filters.hashtags,
        }

    async def _log_search(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        result_count: int,
    ) -> None:
        """Log search query for analytics and suggestions."""
        try:
            await db.execute(
                text("""
                    INSERT INTO search_logs (id, user_id, query, result_count, created_at)
                    VALUES (gen_random_uuid(), :user_id, :query, :result_count, NOW())
                """),
                {
                    "user_id": user_id,
                    "query": query.lower().strip(),
                    "result_count": result_count,
                },
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to log search: {e}")


# Global service instance
search_service = SearchService()
