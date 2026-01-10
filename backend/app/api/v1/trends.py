"""
Trends API Endpoints

Trend detection, monitoring, and content opportunity discovery.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.trends import (
    TrendDetectorService,
    TrendCategory,
    TrendVelocity,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class TrendResponse(BaseModel):
    """Response for a detected trend."""
    id: str
    name: str
    category: str
    platforms: List[str]
    volume: int
    velocity: str
    growth_rate: float
    engagement_rate: float
    first_seen: datetime
    peak_time: Optional[datetime]
    predicted_duration_hours: int
    description: Optional[str]
    related_hashtags: List[str]
    example_content: List[str]
    audio_url: Optional[str]
    relevance_score: float
    difficulty_score: float
    opportunity_score: float
    source: str
    last_updated: datetime


class TrendAlertResponse(BaseModel):
    """Response for a trend alert."""
    trend: TrendResponse
    alert_type: str
    message: str
    action_suggestion: str
    urgency: str
    expires_at: datetime


class TrendReportResponse(BaseModel):
    """Response for a comprehensive trend report."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    platform: Optional[str]
    top_hashtags: List[TrendResponse]
    top_topics: List[TrendResponse]
    top_audios: List[TrendResponse]
    emerging_trends: List[TrendResponse]
    recommendations: List[str]
    content_ideas: List[Dict[str, Any]]


class TrendAnalysisResponse(BaseModel):
    """Response for detailed trend analysis."""
    trend: Dict[str, Any]
    analysis: Dict[str, Any]


class SetNicheRequest(BaseModel):
    """Request to set user's content niches."""
    niches: List[str] = Field(..., min_items=1, max_items=10)


class TrackHashtagRequest(BaseModel):
    """Request to track a specific hashtag."""
    hashtag: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=List[TrendResponse])
async def get_trending(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    limit: int = Query(20, ge=1, le=100),
    include_relevance: bool = Query(True, description="Include personalized relevance scores"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current trending topics and hashtags.

    Returns trends sorted by opportunity score, with personalized
    relevance based on user's content niche.
    """
    # Validate categories
    category_enums = None
    if categories:
        try:
            category_enums = [TrendCategory(c) for c in categories]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Valid options: {[c.value for c in TrendCategory]}"
            )

    service = TrendDetectorService(db)

    trends = await service.get_trending(
        user_id=current_user.id,
        platforms=platforms,
        categories=category_enums,
        limit=limit,
        include_relevance=include_relevance,
    )

    return [_trend_to_response(t) for t in trends]


@router.get("/alerts", response_model=List[TrendAlertResponse])
async def get_trend_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get personalized trend alerts.

    Returns alerts for emerging trends, peak timing, and relevant matches
    based on user's content niche.
    """
    service = TrendDetectorService(db)

    alerts = await service.get_trend_alerts(
        user_id=current_user.id,
        limit=limit,
    )

    return [
        TrendAlertResponse(
            trend=_trend_to_response(a.trend),
            alert_type=a.alert_type,
            message=a.message,
            action_suggestion=a.action_suggestion,
            urgency=a.urgency,
            expires_at=a.expires_at,
        )
        for a in alerts
    ]


@router.get("/report", response_model=TrendReportResponse)
async def get_trend_report(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    period_days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a comprehensive trend report.

    Includes top hashtags, topics, audios, emerging trends,
    and AI-generated recommendations.
    """
    service = TrendDetectorService(db)

    report = await service.get_trend_report(
        user_id=current_user.id,
        platforms=platforms,
        period_days=period_days,
    )

    return TrendReportResponse(
        generated_at=report.generated_at,
        period_start=report.period_start,
        period_end=report.period_end,
        platform=report.platform,
        top_hashtags=[_trend_to_response(t) for t in report.top_hashtags],
        top_topics=[_trend_to_response(t) for t in report.top_topics],
        top_audios=[_trend_to_response(t) for t in report.top_audios],
        emerging_trends=[_trend_to_response(t) for t in report.emerging_trends],
        recommendations=report.recommendations,
        content_ideas=report.content_ideas,
    )


@router.get("/{trend_id}/analyze", response_model=TrendAnalysisResponse)
async def analyze_trend(
    trend_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed AI analysis of a specific trend.

    Provides insights on why the trend is popular, best content types,
    content ideas, and timing recommendations.
    """
    service = TrendDetectorService(db)

    try:
        analysis = await service.analyze_trend(
            trend_id=trend_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return TrendAnalysisResponse(
        trend=analysis["trend"],
        analysis=analysis["analysis"],
    )


@router.post("/niche")
async def set_user_niche(
    request: SetNicheRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set user's content niches for personalized trend recommendations.

    Valid niches include: tech, lifestyle, fitness, beauty, food,
    travel, business, gaming, music, art, education, etc.
    """
    service = TrendDetectorService(db)

    await service.set_user_niche(
        user_id=current_user.id,
        niches=request.niches,
    )

    return {
        "message": "Niches updated successfully",
        "niches": request.niches,
    }


@router.post("/track")
async def track_hashtag(
    request: TrackHashtagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Track a specific hashtag's trend status.

    Returns current trend data if the hashtag is trending,
    or null if not currently trending.
    """
    service = TrendDetectorService(db)

    trend = await service.track_hashtag(
        user_id=current_user.id,
        hashtag=request.hashtag,
    )

    if trend:
        return {
            "is_trending": True,
            "trend": _trend_to_response(trend),
        }
    else:
        return {
            "is_trending": False,
            "trend": None,
            "message": f"#{request.hashtag.strip('#')} is not currently trending",
        }


@router.post("/refresh")
async def refresh_trends(
    platforms: Optional[List[str]] = Query(None, description="Platforms to refresh"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Force refresh trends from platform APIs.

    Use sparingly as this bypasses caching.
    """
    service = TrendDetectorService(db)

    await service.refresh_trends(platforms=platforms)

    return {
        "message": "Trends refreshed successfully",
        "platforms": platforms or ["tiktok", "instagram", "twitter", "youtube"],
    }


@router.get("/categories")
async def get_trend_categories():
    """
    Get available trend categories.
    """
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in TrendCategory
        ]
    }


@router.get("/velocities")
async def get_trend_velocities():
    """
    Get trend velocity definitions.
    """
    return {
        "velocities": [
            {
                "value": TrendVelocity.EMERGING.value,
                "label": "Emerging",
                "description": "Just starting to gain traction",
            },
            {
                "value": TrendVelocity.RISING.value,
                "label": "Rising",
                "description": "Growing quickly in popularity",
            },
            {
                "value": TrendVelocity.PEAK.value,
                "label": "Peak",
                "description": "At maximum popularity",
            },
            {
                "value": TrendVelocity.DECLINING.value,
                "label": "Declining",
                "description": "Past peak, losing momentum",
            },
            {
                "value": TrendVelocity.STABLE.value,
                "label": "Stable",
                "description": "Consistent, long-term trend",
            },
        ]
    }


# ============================================================================
# Helper Functions
# ============================================================================


def _trend_to_response(trend) -> TrendResponse:
    """Convert Trend dataclass to response schema."""
    return TrendResponse(
        id=trend.id,
        name=trend.name,
        category=trend.category.value,
        platforms=trend.platforms,
        volume=trend.volume,
        velocity=trend.velocity.value,
        growth_rate=trend.growth_rate,
        engagement_rate=trend.engagement_rate,
        first_seen=trend.first_seen,
        peak_time=trend.peak_time,
        predicted_duration_hours=trend.predicted_duration_hours,
        description=trend.description,
        related_hashtags=trend.related_hashtags,
        example_content=trend.example_content,
        audio_url=trend.audio_url,
        relevance_score=trend.relevance_score,
        difficulty_score=trend.difficulty_score,
        opportunity_score=trend.opportunity_score,
        source=trend.source,
        last_updated=trend.last_updated,
    )
