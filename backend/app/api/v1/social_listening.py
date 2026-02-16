"""
Social Listening API

Real endpoints replacing stubs for FEAT-048.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.listening import SocialListeningService

router = APIRouter(prefix="/listening", tags=["Social Listening"])


# ---- Schemas ----

class QueryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    keywords: list[str] = Field(min_length=1)
    platforms: list[str] = Field(min_length=1)


class MentionCreate(BaseModel):
    platform: str
    author_name: str
    content: str
    posted_at: datetime
    url: Optional[str] = None
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    engagement: int = 0


# ---- Routes ----

@router.get("/queries")
async def list_queries(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's listening queries."""
    service = SocialListeningService(db)
    queries = await service.list_queries(current_user.id, status=status_filter)
    return {"queries": [q.to_dict() for q in queries], "total": len(queries)}


@router.post("/queries", status_code=status.HTTP_201_CREATED)
async def create_query(
    data: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new listening query."""
    service = SocialListeningService(db)
    query = await service.create_query(
        user_id=current_user.id,
        name=data.name,
        keywords=data.keywords,
        platforms=data.platforms,
    )
    return query.to_dict()


@router.get("/queries/{query_id}")
async def get_query(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a listening query with details."""
    service = SocialListeningService(db)
    query = await service.get_query(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query.to_dict()


@router.delete("/queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a listening query."""
    service = SocialListeningService(db)
    if not await service.delete_query(query_id):
        raise HTTPException(status_code=404, detail="Query not found")


@router.get("/queries/{query_id}/mentions")
async def get_mentions(
    query_id: uuid.UUID,
    platform: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mentions for a query."""
    service = SocialListeningService(db)
    mentions = await service.get_mentions(
        query_id, platform=platform, sentiment=sentiment, limit=limit, offset=offset
    )
    return {"mentions": [m.to_dict() for m in mentions], "total": len(mentions)}


@router.post("/queries/{query_id}/mentions", status_code=status.HTTP_201_CREATED)
async def add_mention(
    query_id: uuid.UUID,
    data: MentionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a new mention (webhook or manual)."""
    service = SocialListeningService(db)
    mention = await service.add_mention(query_id=query_id, **data.model_dump())
    return mention.to_dict()


@router.get("/queries/{query_id}/sentiment")
async def get_sentiment_summary(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment summary for a query."""
    service = SocialListeningService(db)
    return await service.get_sentiment_summary(query_id)
