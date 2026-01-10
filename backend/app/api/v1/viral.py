"""
Viral Score Predictor API Endpoints

REST API for predicting content viral potential.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class ContentPredictionRequest(BaseModel):
    """Request to predict content viral potential."""
    platform: str = Field(..., description="Target platform")
    text: Optional[str] = Field(None, description="Post text/caption")
    hashtags: list[str] = Field(default_factory=list)
    media_urls: list[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    posting_time: Optional[datetime] = None


class CreatorStats(BaseModel):
    """Creator statistics for prediction context."""
    follower_count: int = 10000
    engagement_rate: float = 3.0
    avg_views: int = 5000


class ViralFactorResponse(BaseModel):
    """Individual viral factor score."""
    name: str
    score: float
    weight: float
    description: str
    suggestions: list[str] = []


class ViralPredictionResponse(BaseModel):
    """Viral prediction response."""
    platform: str
    viral_score: float
    viral_potential: str  # low, moderate, high, viral
    confidence: float
    predicted_views: tuple[int, int]
    predicted_likes: tuple[int, int]
    predicted_comments: tuple[int, int]
    predicted_shares: tuple[int, int]
    factors: list[ViralFactorResponse] = []
    improvement_suggestions: list[str] = []
    potential_score_increase: float = 0.0
    best_posting_times: list[str] = []
    worst_posting_times: list[str] = []
    percentile_rank: float = 0.0
    analyzed_at: datetime


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post("/predict", response_model=ViralPredictionResponse)
async def predict_viral_score(
    request: ContentPredictionRequest,
    creator_stats: Optional[CreatorStats] = None,
):
    """
    Predict the viral potential of content before publishing.

    Returns viral score, predicted metrics, and improvement suggestions.
    """
    from app.services.analytics import ViralScorePredictor

    predictor = ViralScorePredictor()

    content = {
        "text": request.text,
        "hashtags": request.hashtags,
        "media_urls": request.media_urls,
        "thumbnail_url": request.thumbnail_url,
        "duration_seconds": request.duration_seconds,
    }

    stats = None
    if creator_stats:
        stats = {
            "follower_count": creator_stats.follower_count,
            "engagement_rate": creator_stats.engagement_rate,
            "avg_views": creator_stats.avg_views,
        }

    prediction = await predictor.predict(
        content=content,
        platform=request.platform,
        creator_stats=stats,
        posting_time=request.posting_time,
    )

    return ViralPredictionResponse(
        platform=prediction.platform,
        viral_score=prediction.viral_score,
        viral_potential=prediction.viral_potential.value,
        confidence=prediction.confidence,
        predicted_views=prediction.predicted_views,
        predicted_likes=prediction.predicted_likes,
        predicted_comments=prediction.predicted_comments,
        predicted_shares=prediction.predicted_shares,
        factors=[
            ViralFactorResponse(
                name=f.name,
                score=f.score,
                weight=f.weight,
                description=f.description,
                suggestions=f.suggestions,
            )
            for f in prediction.factors
        ],
        improvement_suggestions=prediction.improvement_suggestions,
        potential_score_increase=prediction.potential_score_increase,
        best_posting_times=prediction.best_posting_times,
        worst_posting_times=prediction.worst_posting_times,
        percentile_rank=prediction.percentile_rank,
        analyzed_at=prediction.analyzed_at,
    )


@router.post("/predict/batch")
async def predict_batch(
    requests: list[ContentPredictionRequest],
    creator_stats: Optional[CreatorStats] = None,
):
    """
    Predict viral scores for multiple content items.

    Useful for comparing different versions of the same content.
    """
    from app.services.analytics import ViralScorePredictor

    predictor = ViralScorePredictor()
    results = []

    stats = None
    if creator_stats:
        stats = {
            "follower_count": creator_stats.follower_count,
            "engagement_rate": creator_stats.engagement_rate,
            "avg_views": creator_stats.avg_views,
        }

    for req in requests:
        content = {
            "text": req.text,
            "hashtags": req.hashtags,
            "media_urls": req.media_urls,
            "thumbnail_url": req.thumbnail_url,
            "duration_seconds": req.duration_seconds,
        }

        prediction = await predictor.predict(
            content=content,
            platform=req.platform,
            creator_stats=stats,
            posting_time=req.posting_time,
        )

        results.append({
            "platform": prediction.platform,
            "viral_score": prediction.viral_score,
            "viral_potential": prediction.viral_potential.value,
            "predicted_views": prediction.predicted_views,
            "improvement_suggestions": prediction.improvement_suggestions[:3],
        })

    # Sort by viral score
    results.sort(key=lambda x: x["viral_score"], reverse=True)

    return {
        "predictions": results,
        "best_option_index": 0,
        "score_range": {
            "min": min(r["viral_score"] for r in results),
            "max": max(r["viral_score"] for r in results),
        },
    }


@router.get("/optimal-times/{platform}")
async def get_optimal_posting_times(
    platform: str,
):
    """
    Get optimal posting times for a platform.

    Returns best and worst times to post.
    """
    from app.services.analytics import ViralScorePredictor

    predictor = ViralScorePredictor()

    return {
        "platform": platform,
        "best_times": predictor._get_best_posting_times(platform),
        "worst_times": predictor._get_worst_posting_times(platform),
        "timezone_note": "Times are in your local timezone",
    }


@router.get("/triggers")
async def get_viral_triggers():
    """
    Get list of viral trigger words by category.

    Returns power words that increase viral potential.
    """
    from app.services.analytics import ViralScorePredictor

    return {
        "triggers": ViralScorePredictor.VIRAL_TRIGGERS,
        "usage_tips": [
            "Use 1-2 trigger words in your opening hook",
            "Don't overuse - authenticity matters",
            "Match triggers to your content style",
            "Test different approaches and track performance",
        ],
    }
