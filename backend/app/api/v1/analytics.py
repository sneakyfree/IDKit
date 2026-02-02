"""
Analytics API Endpoints

Unified analytics aggregation across all connected social platforms.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.analytics import (
    UnifiedAnalyticsService,
    MetricType,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class PlatformMetricsResponse(BaseModel):
    """Metrics for a single platform."""
    platform: str
    account_id: str
    account_name: str
    impressions: int
    reach: int
    engagement: int
    engagement_rate: float
    likes: int
    comments: int
    shares: int
    saves: int
    clicks: int
    followers: int
    follower_change: int
    views: int
    watch_time_seconds: int
    posts_count: int


class UnifiedMetricsResponse(BaseModel):
    """Aggregated metrics across all platforms."""
    total_impressions: int
    total_reach: int
    total_engagement: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_saves: int
    total_clicks: int
    total_followers: int
    total_follower_change: int
    total_views: int
    total_watch_time_seconds: int
    total_posts: int
    average_engagement_rate: float
    platform_breakdown: List[PlatformMetricsResponse]


class TimeSeriesPointResponse(BaseModel):
    """Single point in time series data."""
    date: datetime
    value: float
    platform: Optional[str] = None


class TrendDataResponse(BaseModel):
    """Trend analysis data."""
    metric: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str
    is_significant: bool


class ContentPerformanceResponse(BaseModel):
    """Performance data for a piece of content."""
    content_id: str
    platform: str
    post_type: str
    title: Optional[str]
    posted_at: datetime
    impressions: int
    engagement: int
    engagement_rate: float
    likes: int
    comments: int
    shares: int
    performance_score: float


class AudienceInsightsResponse(BaseModel):
    """Audience demographics and behavior."""
    total_followers: int
    gender_breakdown: dict
    age_breakdown: dict
    top_countries: List[dict]
    top_cities: List[dict]
    active_hours: dict
    active_days: dict


class BestTimeToPostResponse(BaseModel):
    """Optimal posting time recommendation."""
    platform: str
    day_of_week: str
    hour: int
    timezone: str
    engagement_score: float
    confidence: float


class SyncResultResponse(BaseModel):
    """Result of analytics sync operation."""
    synced: dict


class ComparativeAnalyticsResponse(BaseModel):
    """Comparative analytics data."""
    period_days: int
    platforms: dict
    rankings: dict


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/overview", response_model=UnifiedMetricsResponse)
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get unified analytics overview across all connected platforms.

    Returns aggregated metrics including impressions, engagement, followers,
    and platform-by-platform breakdown.
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = UnifiedAnalyticsService(db)

    metrics = await service.get_unified_metrics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        platforms=platforms,
    )

    return UnifiedMetricsResponse(
        total_impressions=metrics.total_impressions,
        total_reach=metrics.total_reach,
        total_engagement=metrics.total_engagement,
        total_likes=metrics.total_likes,
        total_comments=metrics.total_comments,
        total_shares=metrics.total_shares,
        total_saves=metrics.total_saves,
        total_clicks=metrics.total_clicks,
        total_followers=metrics.total_followers,
        total_follower_change=metrics.total_follower_change,
        total_views=metrics.total_views,
        total_watch_time_seconds=metrics.total_watch_time_seconds,
        total_posts=metrics.total_posts,
        average_engagement_rate=metrics.average_engagement_rate,
        platform_breakdown=[
            PlatformMetricsResponse(
                platform=p.platform,
                account_id=str(p.account_id),
                account_name=p.account_name,
                impressions=p.impressions,
                reach=p.reach,
                engagement=p.engagement,
                engagement_rate=p.engagement_rate,
                likes=p.likes,
                comments=p.comments,
                shares=p.shares,
                saves=p.saves,
                clicks=p.clicks,
                followers=p.followers,
                follower_change=p.follower_change,
                views=p.views,
                watch_time_seconds=p.watch_time_seconds,
                posts_count=p.posts_count,
            )
            for p in metrics.platform_breakdown
        ],
    )


@router.get("/timeseries", response_model=List[TimeSeriesPointResponse])
async def get_analytics_timeseries(
    metric: str = Query(..., description="Metric to chart (impressions, reach, engagement, likes, comments, shares, views, followers)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    granularity: str = Query("day", description="Data granularity: day, week, month"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get time series data for a specific metric.

    Returns data points for charting metrics over time with
    configurable granularity (daily, weekly, monthly).
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Validate metric
    try:
        metric_type = MetricType(metric)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Valid options: {[m.value for m in MetricType]}"
        )

    # Validate granularity
    if granularity not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid granularity. Valid options: day, week, month"
        )

    service = UnifiedAnalyticsService(db)

    time_series = await service.get_time_series(
        user_id=current_user.id,
        metric=metric_type,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        platforms=platforms,
    )

    return [
        TimeSeriesPointResponse(
            date=point.date,
            value=point.value,
            platform=point.platform,
        )
        for point in time_series
    ]


@router.get("/trends", response_model=List[TrendDataResponse])
async def get_analytics_trends(
    period_days: int = Query(30, description="Period to compare (compares to previous equal period)"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get trend analysis comparing current period to previous period.

    Shows growth/decline for key metrics with percentage changes.
    """
    service = UnifiedAnalyticsService(db)

    trends = await service.get_trends(
        user_id=current_user.id,
        period_days=period_days,
        platforms=platforms,
    )

    return [
        TrendDataResponse(
            metric=t.metric,
            current_value=t.current_value,
            previous_value=t.previous_value,
            change_percent=t.change_percent,
            trend_direction=t.trend_direction,
            is_significant=t.is_significant,
        )
        for t in trends
    ]


@router.get("/top-content", response_model=List[ContentPerformanceResponse])
async def get_top_content(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    sort_by: str = Query("engagement", description="Sort by: engagement, impressions, engagement_rate"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get top performing content across platforms.

    Returns posts ranked by engagement, impressions, or engagement rate.
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    if sort_by not in ["engagement", "impressions", "engagement_rate"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort_by. Valid options: engagement, impressions, engagement_rate"
        )

    service = UnifiedAnalyticsService(db)

    content = await service.get_top_content(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        platforms=platforms,
        sort_by=sort_by,
    )

    return [
        ContentPerformanceResponse(
            content_id=c.content_id,
            platform=c.platform,
            post_type=c.post_type,
            title=c.title,
            posted_at=c.posted_at,
            impressions=c.impressions,
            engagement=c.engagement,
            engagement_rate=c.engagement_rate,
            likes=c.likes,
            comments=c.comments,
            shares=c.shares,
            performance_score=c.performance_score,
        )
        for c in content
    ]


@router.get("/audience", response_model=AudienceInsightsResponse)
async def get_audience_insights(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated audience demographics and behavior insights.

    Includes gender, age, location, and activity patterns.
    """
    service = UnifiedAnalyticsService(db)

    insights = await service.get_audience_insights(
        user_id=current_user.id,
        platforms=platforms,
    )

    return AudienceInsightsResponse(
        total_followers=insights.total_followers,
        gender_breakdown=insights.gender_breakdown,
        age_breakdown=insights.age_breakdown,
        top_countries=insights.top_countries,
        top_cities=insights.top_cities,
        active_hours=insights.active_hours,
        active_days=insights.active_days,
    )


@router.get("/best-times", response_model=List[BestTimeToPostResponse])
async def get_best_times_to_post(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recommended best times to post for optimal engagement.

    Analyzes historical performance to suggest optimal posting times
    per platform.
    """
    service = UnifiedAnalyticsService(db)

    best_times = await service.get_best_times_to_post(
        user_id=current_user.id,
        platforms=platforms,
    )

    return [
        BestTimeToPostResponse(
            platform=t.platform,
            day_of_week=t.day_of_week,
            hour=t.hour,
            timezone=t.timezone,
            engagement_score=t.engagement_score,
            confidence=t.confidence,
        )
        for t in best_times
    ]


@router.get("/compare", response_model=ComparativeAnalyticsResponse)
async def get_comparative_analytics(
    period_days: int = Query(30, description="Period to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comparative analytics showing platform performance side-by-side.

    Ranks platforms by engagement, reach, and follower growth.
    """
    service = UnifiedAnalyticsService(db)

    comparison = await service.get_comparative_analytics(
        user_id=current_user.id,
        compare_period_days=period_days,
    )

    return ComparativeAnalyticsResponse(
        period_days=comparison["period_days"],
        platforms=comparison["platforms"],
        rankings=comparison["rankings"],
    )


@router.post("/sync", response_model=SyncResultResponse)
async def sync_analytics(
    platform: Optional[str] = Query(None, description="Specific platform to sync"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sync latest analytics from connected platforms.

    Fetches fresh data from platform APIs and stores for analysis.
    """
    service = UnifiedAnalyticsService(db)

    results = await service.sync_platform_analytics(
        user_id=current_user.id,
        platform=platform,
    )

    return SyncResultResponse(synced=results)


@router.get("/platform/{platform}", response_model=PlatformMetricsResponse)
async def get_platform_analytics(
    platform: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics for a specific platform.
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = UnifiedAnalyticsService(db)

    metrics = await service.get_unified_metrics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        platforms=[platform],
    )

    # Find the platform in breakdown
    platform_data = None
    for p in metrics.platform_breakdown:
        if p.platform == platform:
            platform_data = p
            break

    if not platform_data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for platform: {platform}"
        )

    return PlatformMetricsResponse(
        platform=platform_data.platform,
        account_id=str(platform_data.account_id),
        account_name=platform_data.account_name,
        impressions=platform_data.impressions,
        reach=platform_data.reach,
        engagement=platform_data.engagement,
        engagement_rate=platform_data.engagement_rate,
        likes=platform_data.likes,
        comments=platform_data.comments,
        shares=platform_data.shares,
        saves=platform_data.saves,
        clicks=platform_data.clicks,
        followers=platform_data.followers,
        follower_change=platform_data.follower_change,
        views=platform_data.views,
        watch_time_seconds=platform_data.watch_time_seconds,
        posts_count=platform_data.posts_count,
    )


class ExportFormat(str):
    CSV = "csv"
    JSON = "json"


class ExportResponse(BaseModel):
    """Export data response."""
    format: str
    filename: str
    data: str  # Base64 encoded for CSV, JSON string for JSON
    generated_at: datetime


@router.get("/export", response_model=ExportResponse)
async def export_analytics(
    format: str = Query("csv", description="Export format: csv or json"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    include_timeseries: bool = Query(True, description="Include daily time series data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export analytics data as CSV or JSON.
    
    Includes overview metrics, platform breakdown, and optionally time series.
    """
    import csv
    import io
    import json
    import base64

    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Valid options: csv, json"
        )

    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = UnifiedAnalyticsService(db)

    # Get metrics
    metrics = await service.get_unified_metrics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        platforms=platforms,
    )

    # Get time series for engagement if requested
    timeseries = []
    if include_timeseries:
        timeseries = await service.get_time_series(
            user_id=current_user.id,
            metric=MetricType.ENGAGEMENT,
            start_date=start_date,
            end_date=end_date,
            granularity="day",
            platforms=platforms,
        )

    # Build export data
    export_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "overview": {
            "total_impressions": metrics.total_impressions,
            "total_reach": metrics.total_reach,
            "total_engagement": metrics.total_engagement,
            "total_likes": metrics.total_likes,
            "total_comments": metrics.total_comments,
            "total_shares": metrics.total_shares,
            "total_saves": metrics.total_saves,
            "total_clicks": metrics.total_clicks,
            "total_followers": metrics.total_followers,
            "total_follower_change": metrics.total_follower_change,
            "total_views": metrics.total_views,
            "total_watch_time_seconds": metrics.total_watch_time_seconds,
            "total_posts": metrics.total_posts,
            "average_engagement_rate": metrics.average_engagement_rate,
        },
        "platform_breakdown": [
            {
                "platform": p.platform,
                "account_name": p.account_name,
                "impressions": p.impressions,
                "reach": p.reach,
                "engagement": p.engagement,
                "engagement_rate": p.engagement_rate,
                "likes": p.likes,
                "comments": p.comments,
                "shares": p.shares,
                "saves": p.saves,
                "clicks": p.clicks,
                "followers": p.followers,
                "follower_change": p.follower_change,
                "views": p.views,
                "watch_time_seconds": p.watch_time_seconds,
                "posts_count": p.posts_count,
            }
            for p in metrics.platform_breakdown
        ],
        "timeseries": [
            {
                "date": point.date.isoformat(),
                "value": point.value,
                "platform": point.platform,
            }
            for point in timeseries
        ] if timeseries else [],
    }

    filename_date = start_date.strftime("%Y%m%d") + "-" + end_date.strftime("%Y%m%d")

    if format == "json":
        data_str = json.dumps(export_data, indent=2)
        return ExportResponse(
            format="json",
            filename=f"analytics_{filename_date}.json",
            data=data_str,
            generated_at=datetime.now(timezone.utc),
        )

    # CSV format
    output = io.StringIO()
    writer = csv.writer(output)

    # Overview section
    writer.writerow(["Analytics Export Report"])
    writer.writerow(["Period", f"{start_date.date()} to {end_date.date()}"])
    writer.writerow([])
    writer.writerow(["Overview Metrics"])
    for key, value in export_data["overview"].items():
        writer.writerow([key.replace("_", " ").title(), value])
    writer.writerow([])

    # Platform breakdown
    writer.writerow(["Platform Breakdown"])
    if export_data["platform_breakdown"]:
        headers = list(export_data["platform_breakdown"][0].keys())
        writer.writerow(headers)
        for platform in export_data["platform_breakdown"]:
            writer.writerow([platform[h] for h in headers])
    writer.writerow([])

    # Time series
    if export_data["timeseries"]:
        writer.writerow(["Daily Engagement"])
        writer.writerow(["Date", "Value", "Platform"])
        for point in export_data["timeseries"]:
            writer.writerow([point["date"], point["value"], point["platform"]])

    csv_content = output.getvalue()
    encoded = base64.b64encode(csv_content.encode()).decode()

    return ExportResponse(
        format="csv",
        filename=f"analytics_{filename_date}.csv",
        data=encoded,
        generated_at=datetime.now(timezone.utc),
    )

