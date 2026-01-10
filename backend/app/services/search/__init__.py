"""
Search Service Module

Provides unified search across users, posts, hashtags, and content.
"""

from app.services.search.service import SearchService, search_service
from app.services.search.models import (
    SearchResult,
    SearchResultType,
    SearchFilters,
    SearchSortBy,
)

__all__ = [
    "SearchService",
    "search_service",
    "SearchResult",
    "SearchResultType",
    "SearchFilters",
    "SearchSortBy",
]
