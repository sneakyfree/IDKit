"""
Competitor Analysis API Endpoints

REST API for competitor analysis features.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class CompetitorSearchRequest(BaseModel):
    """Request to discover competitors."""
    platform: str = Field(..., description="Platform to search")
    niche_keywords: list[str] = Field(..., min_length=1, description="Keywords describing the niche")
    min_followers: int = Field(default=1000, ge=0)
    max_followers: int = Field(default=1000000, ge=0)
    limit: int = Field(default=20, ge=1, le=50)


class CompetitorProfileResponse(BaseModel):
    """Competitor profile response."""
    competitor_id: str
    platform: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    engagement_rate: float = 0.0
    follower_growth_rate: float = 0.0
    posting_frequency: float = 0.0
    top_hashtags: list[str] = []
    content_categories: dict[str, float] = {}
    best_posting_times: list[str] = []
    niche_tags: list[str] = []
    competitor_type: str = "direct"
    last_updated: Optional[datetime] = None


class MatchScoreResponse(BaseModel):
    """Match score between user and competitor."""
    overall_score: float
    niche_score: float
    audience_score: float
    engagement_score: float
    reach_score: float
    platform_score: float
    rate_score: float
    matching_niches: list[str] = []
    matching_platforms: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    estimated_fair_rate: float = 0.0
    rate_comparison: str = ""


class CompetitorComparisonResponse(BaseModel):
    """Comparison between user and competitor."""
    competitor: CompetitorProfileResponse
    follower_ratio: float
    engagement_ratio: float
    posting_frequency_ratio: float
    growth_rate_ratio: float
    content_gaps: list[str] = []
    hashtag_opportunities: list[str] = []
    timing_insights: list[str] = []
    recommendations: list[str] = []
    priority: str = "medium"


class CompetitorReportResponse(BaseModel):
    """Full competitor analysis report."""
    user_id: str
    platform: str
    generated_at: datetime
    user_profile: dict = {}
    competitors: list[CompetitorProfileResponse] = []
    comparisons: list[CompetitorComparisonResponse] = []
    market_position: str = ""
    market_share_estimate: float = 0.0
    emerging_trends: list[str] = []
    declining_trends: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []
    priority_actions: list[str] = []


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post("/discover", response_model=list[CompetitorProfileResponse])
async def discover_competitors(
    request: CompetitorSearchRequest,
):
    """
    Discover potential competitors based on niche keywords.

    Returns list of competitors matching the search criteria.
    """
    from app.services.analytics import CompetitorAnalyzer

    analyzer = CompetitorAnalyzer()

    competitors = await analyzer.discover_competitors(
        user_id="current_user",  # Would come from auth
        platform=request.platform,
        niche_keywords=request.niche_keywords,
        follower_range=(request.min_followers, request.max_followers),
        limit=request.limit,
    )

    return [
        CompetitorProfileResponse(
            competitor_id=c.competitor_id,
            platform=c.platform,
            username=c.username,
            display_name=c.display_name,
            profile_url=c.profile_url,
            avatar_url=c.avatar_url,
            bio=c.bio,
            follower_count=c.follower_count,
            following_count=c.following_count,
            post_count=c.post_count,
            engagement_rate=c.engagement_rate,
            follower_growth_rate=c.follower_growth_rate,
            posting_frequency=c.posting_frequency,
            top_hashtags=c.top_hashtags,
            content_categories=c.content_categories,
            best_posting_times=c.best_posting_times,
            niche_tags=c.niche_tags,
            competitor_type=c.competitor_type.value,
            last_updated=c.last_updated,
        )
        for c in competitors
    ]


@router.get("/analyze/{platform}/{username}", response_model=CompetitorProfileResponse)
async def analyze_competitor(
    platform: str,
    username: str,
    include_content: bool = Query(default=True),
    content_limit: int = Query(default=50, ge=1, le=100),
):
    """
    Perform deep analysis of a single competitor.

    Returns detailed competitor profile with content insights.
    """
    from app.services.analytics import CompetitorAnalyzer

    analyzer = CompetitorAnalyzer()

    profile = await analyzer.analyze_competitor(
        platform=platform,
        username=username,
        include_content=include_content,
        content_limit=content_limit,
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Competitor not found")

    return CompetitorProfileResponse(
        competitor_id=profile.competitor_id,
        platform=profile.platform,
        username=profile.username,
        display_name=profile.display_name,
        profile_url=profile.profile_url,
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        follower_count=profile.follower_count,
        following_count=profile.following_count,
        post_count=profile.post_count,
        engagement_rate=profile.engagement_rate,
        follower_growth_rate=profile.follower_growth_rate,
        posting_frequency=profile.posting_frequency,
        top_hashtags=profile.top_hashtags,
        content_categories=profile.content_categories,
        best_posting_times=profile.best_posting_times,
        niche_tags=profile.niche_tags,
        competitor_type=profile.competitor_type.value,
        last_updated=profile.last_updated,
    )


@router.post("/compare/{platform}/{username}", response_model=CompetitorComparisonResponse)
async def compare_with_competitor(
    platform: str,
    username: str,
):
    """
    Compare user's metrics with a specific competitor.

    Returns detailed comparison with insights and recommendations.
    """
    from app.services.analytics import CompetitorAnalyzer

    analyzer = CompetitorAnalyzer()

    # Get competitor profile
    competitor = await analyzer.analyze_competitor(platform, username)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Mock user profile (would come from analytics service)
    user_profile = {
        "follower_count": 50000,
        "engagement_rate": 4.5,
        "posting_frequency": 7,
        "growth_rate": 3.0,
        "top_hashtags": ["creator", "content"],
        "content_categories": {"educational": 0.4, "entertainment": 0.3},
    }

    comparison = await analyzer.compare_with_user(
        user_id="current_user",
        user_profile=user_profile,
        competitor=competitor,
    )

    return CompetitorComparisonResponse(
        competitor=CompetitorProfileResponse(
            competitor_id=competitor.competitor_id,
            platform=competitor.platform,
            username=competitor.username,
            display_name=competitor.display_name,
            follower_count=competitor.follower_count,
            engagement_rate=competitor.engagement_rate,
            top_hashtags=competitor.top_hashtags,
            content_categories=competitor.content_categories,
            competitor_type=competitor.competitor_type.value,
        ),
        follower_ratio=comparison.follower_ratio,
        engagement_ratio=comparison.engagement_ratio,
        posting_frequency_ratio=comparison.posting_frequency_ratio,
        growth_rate_ratio=comparison.growth_rate_ratio,
        content_gaps=comparison.content_gaps,
        hashtag_opportunities=comparison.hashtag_opportunities,
        timing_insights=comparison.timing_insights,
        recommendations=comparison.recommendations,
        priority=comparison.priority,
    )


@router.post("/report", response_model=CompetitorReportResponse)
async def generate_competitor_report(
    platform: str = Query(...),
    niche_keywords: list[str] = Query(...),
    competitor_limit: int = Query(default=10, ge=1, le=20),
):
    """
    Generate a comprehensive competitor analysis report.

    Returns full report with market position, SWOT analysis, and actions.
    """
    from app.services.analytics import CompetitorAnalyzer

    analyzer = CompetitorAnalyzer()

    # Discover competitors
    competitors = await analyzer.discover_competitors(
        user_id="current_user",
        platform=platform,
        niche_keywords=niche_keywords,
        limit=competitor_limit,
    )

    # Mock user profile
    user_profile = {
        "follower_count": 50000,
        "engagement_rate": 4.5,
        "posting_frequency": 7,
        "growth_rate": 3.0,
    }

    report = await analyzer.generate_report(
        user_id="current_user",
        platform=platform,
        competitors=competitors,
        user_profile=user_profile,
    )

    return CompetitorReportResponse(
        user_id=report.user_id,
        platform=report.platform,
        generated_at=report.generated_at,
        user_profile=report.user_profile,
        competitors=[
            CompetitorProfileResponse(
                competitor_id=c.competitor_id,
                platform=c.platform,
                username=c.username,
                display_name=c.display_name,
                follower_count=c.follower_count,
                engagement_rate=c.engagement_rate,
                competitor_type=c.competitor_type.value,
            )
            for c in report.competitors
        ],
        market_position=report.market_position,
        emerging_trends=report.emerging_trends,
        declining_trends=report.declining_trends,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        opportunities=report.opportunities,
        threats=report.threats,
        priority_actions=report.priority_actions,
    )
