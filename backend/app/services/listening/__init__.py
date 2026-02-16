"""
Social Listening Service

Business logic for monitoring brand mentions and sentiment analysis.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listening import ListeningQuery, ListeningMention


class SocialListeningService:
    """Service for social listening query and mention management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_query(
        self,
        user_id: uuid.UUID,
        name: str,
        keywords: list[str],
        platforms: list[str],
    ) -> ListeningQuery:
        """Create a new listening query."""
        query = ListeningQuery(
            user_id=user_id,
            name=name,
            keywords=keywords,
            platforms=platforms,
        )
        self.db.add(query)
        await self.db.commit()
        await self.db.refresh(query)
        return query

    async def list_queries(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[ListeningQuery]:
        """List listening queries for a user."""
        stmt = (
            select(ListeningQuery)
            .where(ListeningQuery.user_id == user_id)
            .order_by(ListeningQuery.created_at.desc())
        )
        if status:
            stmt = stmt.where(ListeningQuery.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_query(self, query_id: uuid.UUID) -> Optional[ListeningQuery]:
        """Get a listening query by ID."""
        stmt = (
            select(ListeningQuery)
            .where(ListeningQuery.id == query_id)
            .options(selectinload(ListeningQuery.mentions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_mentions(
        self,
        query_id: uuid.UUID,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ListeningMention]:
        """Get mentions for a listening query."""
        stmt = (
            select(ListeningMention)
            .where(ListeningMention.query_id == query_id)
            .order_by(ListeningMention.posted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if platform:
            stmt = stmt.where(ListeningMention.platform == platform)
        if sentiment:
            stmt = stmt.where(ListeningMention.sentiment == sentiment)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_mention(
        self,
        query_id: uuid.UUID,
        platform: str,
        author_name: str,
        content: str,
        posted_at: datetime,
        url: Optional[str] = None,
        sentiment: str = "neutral",
        sentiment_score: float = 0.0,
        engagement: int = 0,
    ) -> ListeningMention:
        """Record a new mention."""
        mention = ListeningMention(
            query_id=query_id,
            platform=platform,
            author_name=author_name,
            content=content,
            posted_at=posted_at,
            url=url,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            engagement=engagement,
        )
        self.db.add(mention)

        # Update mention count
        query_obj = await self.get_query(query_id)
        if query_obj:
            query_obj.mentions_count += 1
            query_obj.last_checked_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(mention)
        return mention

    async def get_sentiment_summary(self, query_id: uuid.UUID) -> dict:
        """Get sentiment breakdown for a query."""
        stmt = (
            select(
                ListeningMention.sentiment,
                func.count(ListeningMention.id).label("count"),
                func.avg(ListeningMention.sentiment_score).label("avg_score"),
            )
            .where(ListeningMention.query_id == query_id)
            .group_by(ListeningMention.sentiment)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        breakdown = {}
        total = 0
        for row in rows:
            breakdown[row.sentiment] = {
                "count": row.count,
                "avg_score": float(row.avg_score or 0),
            }
            total += row.count

        return {
            "total_mentions": total,
            "breakdown": breakdown,
            "overall_sentiment": max(breakdown, key=lambda k: breakdown[k]["count"])
            if breakdown
            else "neutral",
        }

    async def delete_query(self, query_id: uuid.UUID) -> bool:
        """Delete a listening query and its mentions."""
        query_obj = await self.get_query(query_id)
        if not query_obj:
            return False
        await self.db.delete(query_obj)
        await self.db.commit()
        return True
