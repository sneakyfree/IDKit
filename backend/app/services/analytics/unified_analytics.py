"""
Unified Analytics Service

Aggregates analytics from all connected social platforms into
a single, normalized view with cross-platform insights.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.social import SocialAccount, AnalyticsDaily


class MetricType(str, Enum):
    """Types of metrics tracked."""
    IMPRESSIONS = "impressions"
    REACH = "reach"
    ENGAGEMENT = "engagement"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    CLICKS = "clicks"
    FOLLOWERS = "followers"
    VIEWS = "views"
    WATCH_TIME = "watch_time"


@dataclass
class PlatformMetrics:
    """Metrics for a single platform."""
    platform: str
    account_id: uuid.UUID
    account_name: str
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    engagement_rate: float = 0.0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    followers: int = 0
    follower_change: int = 0
    views: int = 0
    watch_time_seconds: int = 0
    posts_count: int = 0
    best_post_id: Optional[str] = None
    best_post_engagement: int = 0


@dataclass
class UnifiedMetrics:
    """Aggregated metrics across all platforms."""
    total_impressions: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_saves: int = 0
    total_clicks: int = 0
    total_followers: int = 0
    total_follower_change: int = 0
    total_views: int = 0
    total_watch_time_seconds: int = 0
    total_posts: int = 0
    average_engagement_rate: float = 0.0
    platform_breakdown: List[PlatformMetrics] = field(default_factory=list)


@dataclass
class TimeSeriesPoint:
    """Single point in time series data."""
    date: datetime
    value: float
    platform: Optional[str] = None


@dataclass
class TrendData:
    """Trend analysis data."""
    metric: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # "up", "down", "stable"
    is_significant: bool  # > 5% change


@dataclass
class ContentPerformance:
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
    performance_score: float  # Normalized 0-100


@dataclass
class AudienceInsights:
    """Audience demographics and behavior."""
    total_followers: int
    gender_breakdown: Dict[str, float]  # {"male": 45.2, "female": 52.1, "other": 2.7}
    age_breakdown: Dict[str, float]  # {"18-24": 25.5, "25-34": 35.2, ...}
    top_countries: List[Dict[str, Any]]  # [{"country": "US", "percent": 45.2}, ...]
    top_cities: List[Dict[str, Any]]
    active_hours: Dict[int, float]  # {0: 2.1, 1: 1.5, ..., 23: 5.2} - hourly activity
    active_days: Dict[str, float]  # {"monday": 14.2, ...}


@dataclass
class BestTimeToPost:
    """Optimal posting time recommendations."""
    platform: str
    day_of_week: str
    hour: int
    timezone: str
    engagement_score: float
    confidence: float  # 0-1


class UnifiedAnalyticsService:
    """
    Unified analytics aggregation across all social platforms.

    Provides:
    - Cross-platform metric aggregation
    - Time series analytics
    - Trend analysis
    - Content performance ranking
    - Audience insights
    - Best time to post recommendations
    """

    # Platform weights for engagement calculation
    ENGAGEMENT_WEIGHTS = {
        "like": 1.0,
        "comment": 3.0,
        "share": 5.0,
        "save": 4.0,
        "click": 2.0,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._adapters = {}

    async def _get_adapter(self, platform: str):
        """Get platform adapter lazily."""
        if platform not in self._adapters:
            if platform == "youtube":
                from app.adapters.youtube.adapter import YouTubeAdapter
                self._adapters[platform] = YouTubeAdapter()
            elif platform == "instagram":
                from app.adapters.instagram.adapter import InstagramAdapter
                self._adapters[platform] = InstagramAdapter()
            elif platform == "tiktok":
                from app.adapters.tiktok.adapter import TikTokAdapter
                self._adapters[platform] = TikTokAdapter()
            elif platform == "twitter":
                from app.adapters.twitter.adapter import TwitterAdapter
                self._adapters[platform] = TwitterAdapter()
            elif platform == "facebook":
                from app.adapters.facebook.adapter import FacebookAdapter
                self._adapters[platform] = FacebookAdapter()
            elif platform == "linkedin":
                from app.adapters.linkedin.adapter import LinkedInAdapter
                self._adapters[platform] = LinkedInAdapter()
        return self._adapters.get(platform)

    async def get_unified_metrics(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]] = None,
    ) -> UnifiedMetrics:
        """
        Get aggregated metrics across all connected platforms.

        Args:
            user_id: User to get metrics for
            start_date: Start of date range
            end_date: End of date range
            platforms: Optional filter for specific platforms

        Returns:
            UnifiedMetrics with aggregated data
        """
        # Get user's connected accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            query = query.where(SocialAccount.platform.in_(platforms))

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        unified = UnifiedMetrics()
        platform_metrics = []

        for account in accounts:
            # Get stored analytics data
            analytics_query = select(AnalyticsDaily).where(
                AnalyticsDaily.account_id == account.id,
                AnalyticsDaily.date >= start_date.date(),
                AnalyticsDaily.date <= end_date.date(),
            )
            analytics_result = await self.db.execute(analytics_query)
            daily_data = analytics_result.scalars().all()

            # Aggregate platform metrics
            platform = PlatformMetrics(
                platform=account.platform,
                account_id=account.id,
                account_name=account.account_name or account.platform_user_id,
            )

            for day in daily_data:
                platform.impressions += day.impressions or 0
                platform.reach += day.reach or 0
                platform.likes += day.likes or 0
                platform.comments += day.comments or 0
                platform.shares += day.shares or 0
                platform.saves += day.saves or 0
                platform.clicks += day.clicks or 0
                platform.views += day.views or 0
                if day.watch_time_seconds:
                    platform.watch_time_seconds += day.watch_time_seconds

            # Calculate engagement
            platform.engagement = (
                platform.likes +
                platform.comments * 3 +
                platform.shares * 5 +
                platform.saves * 4
            )

            # Calculate engagement rate
            if platform.impressions > 0:
                platform.engagement_rate = (platform.engagement / platform.impressions) * 100

            # Get current follower count from account
            platform.followers = account.follower_count or 0

            # Calculate follower change over period
            if daily_data:
                first_day = min(daily_data, key=lambda d: d.date)
                last_day = max(daily_data, key=lambda d: d.date)
                if first_day.follower_count and last_day.follower_count:
                    platform.follower_change = last_day.follower_count - first_day.follower_count

            platform.posts_count = len(set(d.post_id for d in daily_data if d.post_id))

            platform_metrics.append(platform)

            # Add to unified totals
            unified.total_impressions += platform.impressions
            unified.total_reach += platform.reach
            unified.total_engagement += platform.engagement
            unified.total_likes += platform.likes
            unified.total_comments += platform.comments
            unified.total_shares += platform.shares
            unified.total_saves += platform.saves
            unified.total_clicks += platform.clicks
            unified.total_followers += platform.followers
            unified.total_follower_change += platform.follower_change
            unified.total_views += platform.views
            unified.total_watch_time_seconds += platform.watch_time_seconds
            unified.total_posts += platform.posts_count

        # Calculate average engagement rate
        if unified.total_impressions > 0:
            unified.average_engagement_rate = (unified.total_engagement / unified.total_impressions) * 100

        unified.platform_breakdown = platform_metrics

        return unified

    async def get_time_series(
        self,
        user_id: uuid.UUID,
        metric: MetricType,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "day",  # "day", "week", "month"
        platforms: Optional[List[str]] = None,
    ) -> List[TimeSeriesPoint]:
        """
        Get time series data for a specific metric.

        Returns data points for charting over time.
        """
        # Get user's connected accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            query = query.where(SocialAccount.platform.in_(platforms))

        result = await self.db.execute(query)
        accounts = result.scalars().all()
        account_ids = [a.id for a in accounts]

        if not account_ids:
            return []

        # Map metric type to column
        metric_column_map = {
            MetricType.IMPRESSIONS: AnalyticsDaily.impressions,
            MetricType.REACH: AnalyticsDaily.reach,
            MetricType.LIKES: AnalyticsDaily.likes,
            MetricType.COMMENTS: AnalyticsDaily.comments,
            MetricType.SHARES: AnalyticsDaily.shares,
            MetricType.SAVES: AnalyticsDaily.saves,
            MetricType.CLICKS: AnalyticsDaily.clicks,
            MetricType.VIEWS: AnalyticsDaily.views,
            MetricType.FOLLOWERS: AnalyticsDaily.follower_count,
            MetricType.WATCH_TIME: AnalyticsDaily.watch_time_seconds,
        }

        metric_column = metric_column_map.get(metric, AnalyticsDaily.impressions)

        # Query aggregated by date
        analytics_query = (
            select(
                AnalyticsDaily.date,
                func.sum(metric_column).label("value")
            )
            .where(
                AnalyticsDaily.account_id.in_(account_ids),
                AnalyticsDaily.date >= start_date.date(),
                AnalyticsDaily.date <= end_date.date(),
            )
            .group_by(AnalyticsDaily.date)
            .order_by(AnalyticsDaily.date)
        )

        result = await self.db.execute(analytics_query)
        rows = result.all()

        time_series = []
        for row in rows:
            time_series.append(TimeSeriesPoint(
                date=datetime.combine(row.date, datetime.min.time()),
                value=float(row.value or 0),
            ))

        # Aggregate by granularity if needed
        if granularity == "week":
            time_series = self._aggregate_by_week(time_series)
        elif granularity == "month":
            time_series = self._aggregate_by_month(time_series)

        return time_series

    async def get_trends(
        self,
        user_id: uuid.UUID,
        period_days: int = 30,
        platforms: Optional[List[str]] = None,
    ) -> List[TrendData]:
        """
        Calculate trends by comparing current period to previous period.

        Returns trend analysis for key metrics.
        """
        end_date = datetime.now(timezone.utc)
        mid_date = end_date - timedelta(days=period_days)
        start_date = mid_date - timedelta(days=period_days)

        # Get metrics for both periods
        current_metrics = await self.get_unified_metrics(
            user_id=user_id,
            start_date=mid_date,
            end_date=end_date,
            platforms=platforms,
        )

        previous_metrics = await self.get_unified_metrics(
            user_id=user_id,
            start_date=start_date,
            end_date=mid_date,
            platforms=platforms,
        )

        trends = []

        # Calculate trends for each metric
        metrics_to_compare = [
            ("impressions", current_metrics.total_impressions, previous_metrics.total_impressions),
            ("reach", current_metrics.total_reach, previous_metrics.total_reach),
            ("engagement", current_metrics.total_engagement, previous_metrics.total_engagement),
            ("likes", current_metrics.total_likes, previous_metrics.total_likes),
            ("comments", current_metrics.total_comments, previous_metrics.total_comments),
            ("shares", current_metrics.total_shares, previous_metrics.total_shares),
            ("followers", current_metrics.total_followers, previous_metrics.total_followers),
            ("engagement_rate", current_metrics.average_engagement_rate, previous_metrics.average_engagement_rate),
        ]

        for metric_name, current_val, previous_val in metrics_to_compare:
            if previous_val > 0:
                change_percent = ((current_val - previous_val) / previous_val) * 100
            elif current_val > 0:
                change_percent = 100.0
            else:
                change_percent = 0.0

            if change_percent > 5:
                trend_direction = "up"
            elif change_percent < -5:
                trend_direction = "down"
            else:
                trend_direction = "stable"

            trends.append(TrendData(
                metric=metric_name,
                current_value=float(current_val),
                previous_value=float(previous_val),
                change_percent=round(change_percent, 2),
                trend_direction=trend_direction,
                is_significant=abs(change_percent) > 5,
            ))

        return trends

    async def get_top_content(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
        platforms: Optional[List[str]] = None,
        sort_by: str = "engagement",  # "engagement", "impressions", "engagement_rate"
    ) -> List[ContentPerformance]:
        """
        Get top performing content across platforms.
        """
        # Get user's connected accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            query = query.where(SocialAccount.platform.in_(platforms))

        result = await self.db.execute(query)
        accounts = result.scalars().all()
        account_ids = [a.id for a in accounts]

        if not account_ids:
            return []

        # Get aggregated post performance
        analytics_query = (
            select(
                AnalyticsDaily.post_id,
                AnalyticsDaily.account_id,
                func.sum(AnalyticsDaily.impressions).label("impressions"),
                func.sum(AnalyticsDaily.likes).label("likes"),
                func.sum(AnalyticsDaily.comments).label("comments"),
                func.sum(AnalyticsDaily.shares).label("shares"),
                func.sum(AnalyticsDaily.saves).label("saves"),
                func.min(AnalyticsDaily.date).label("first_date"),
            )
            .where(
                AnalyticsDaily.account_id.in_(account_ids),
                AnalyticsDaily.date >= start_date.date(),
                AnalyticsDaily.date <= end_date.date(),
                AnalyticsDaily.post_id.isnot(None),
            )
            .group_by(AnalyticsDaily.post_id, AnalyticsDaily.account_id)
        )

        result = await self.db.execute(analytics_query)
        posts = result.all()

        # Build account lookup
        account_lookup = {a.id: a for a in accounts}

        content_list = []
        for post in posts:
            account = account_lookup.get(post.account_id)
            if not account:
                continue

            impressions = post.impressions or 0
            likes = post.likes or 0
            comments = post.comments or 0
            shares = post.shares or 0
            saves = post.saves or 0

            engagement = likes + comments * 3 + shares * 5 + saves * 4
            engagement_rate = (engagement / impressions * 100) if impressions > 0 else 0

            # Calculate normalized performance score (0-100)
            performance_score = min(100, engagement_rate * 10)

            content_list.append(ContentPerformance(
                content_id=post.post_id,
                platform=account.platform,
                post_type="post",  # Would need to query platform for actual type
                title=None,
                posted_at=datetime.combine(post.first_date, datetime.min.time()),
                impressions=impressions,
                engagement=engagement,
                engagement_rate=round(engagement_rate, 2),
                likes=likes,
                comments=comments,
                shares=shares,
                performance_score=round(performance_score, 1),
            ))

        # Sort by requested metric
        if sort_by == "engagement":
            content_list.sort(key=lambda x: x.engagement, reverse=True)
        elif sort_by == "impressions":
            content_list.sort(key=lambda x: x.impressions, reverse=True)
        elif sort_by == "engagement_rate":
            content_list.sort(key=lambda x: x.engagement_rate, reverse=True)

        return content_list[:limit]

    async def get_audience_insights(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
    ) -> AudienceInsights:
        """
        Get aggregated audience demographics across platforms.

        Note: Actual implementation requires live API calls to platforms.
        """
        # Get user's connected accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            query = query.where(SocialAccount.platform.in_(platforms))

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        total_followers = sum(a.follower_count or 0 for a in accounts)

        # Aggregate demographics from stored account metadata
        # In production, this would fetch fresh data from platform APIs
        gender_totals = {"male": 0.0, "female": 0.0, "other": 0.0}
        age_totals = {}
        country_totals = {}
        city_totals = {}
        hour_totals = {i: 0.0 for i in range(24)}
        day_totals = {
            "monday": 0.0, "tuesday": 0.0, "wednesday": 0.0,
            "thursday": 0.0, "friday": 0.0, "saturday": 0.0, "sunday": 0.0
        }

        weighted_accounts = 0

        for account in accounts:
            if not account.metadata:
                continue

            demographics = account.metadata.get("demographics", {})
            followers = account.follower_count or 0
            weight = followers / total_followers if total_followers > 0 else 0

            # Gender
            if "gender" in demographics:
                for gender, percent in demographics["gender"].items():
                    if gender.lower() in gender_totals:
                        gender_totals[gender.lower()] += percent * weight

            # Age
            if "age" in demographics:
                for age_range, percent in demographics["age"].items():
                    age_totals[age_range] = age_totals.get(age_range, 0) + percent * weight

            # Countries
            if "countries" in demographics:
                for country_data in demographics["countries"]:
                    country = country_data.get("country", "Unknown")
                    percent = country_data.get("percent", 0)
                    country_totals[country] = country_totals.get(country, 0) + percent * weight

            # Active hours
            if "active_hours" in demographics:
                for hour, activity in demographics["active_hours"].items():
                    hour_totals[int(hour)] += activity * weight

            weighted_accounts += 1

        # Normalize
        if weighted_accounts > 0:
            for gender in gender_totals:
                gender_totals[gender] = round(gender_totals[gender], 1)

        # Format country data
        top_countries = [
            {"country": k, "percent": round(v, 1)}
            for k, v in sorted(country_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return AudienceInsights(
            total_followers=total_followers,
            gender_breakdown=gender_totals,
            age_breakdown={k: round(v, 1) for k, v in age_totals.items()},
            top_countries=top_countries,
            top_cities=[],  # Would require city-level data
            active_hours={k: round(v, 1) for k, v in hour_totals.items()},
            active_days={k: round(v, 1) for k, v in day_totals.items()},
        )

    async def get_best_times_to_post(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
    ) -> List[BestTimeToPost]:
        """
        Analyze historical performance to recommend best posting times.
        """
        # Get user's connected accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            query = query.where(SocialAccount.platform.in_(platforms))

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        recommendations = []

        for account in accounts:
            # Analyze posting patterns from analytics
            # In production, this would analyze actual post timestamps and their performance

            # Default recommendations based on platform best practices
            platform_defaults = {
                "instagram": [
                    ("tuesday", 11, 0.9),
                    ("wednesday", 11, 0.88),
                    ("friday", 10, 0.85),
                ],
                "twitter": [
                    ("wednesday", 9, 0.9),
                    ("tuesday", 9, 0.87),
                    ("thursday", 12, 0.85),
                ],
                "linkedin": [
                    ("tuesday", 10, 0.92),
                    ("wednesday", 12, 0.89),
                    ("thursday", 9, 0.86),
                ],
                "tiktok": [
                    ("tuesday", 19, 0.91),
                    ("thursday", 19, 0.88),
                    ("friday", 17, 0.85),
                ],
                "youtube": [
                    ("thursday", 15, 0.90),
                    ("friday", 15, 0.87),
                    ("saturday", 11, 0.84),
                ],
                "facebook": [
                    ("wednesday", 11, 0.89),
                    ("thursday", 13, 0.86),
                    ("friday", 9, 0.83),
                ],
            }

            platform_times = platform_defaults.get(account.platform, [])

            for day, hour, score in platform_times:
                recommendations.append(BestTimeToPost(
                    platform=account.platform,
                    day_of_week=day,
                    hour=hour,
                    timezone="UTC",
                    engagement_score=score,
                    confidence=0.7,  # Lower confidence for defaults
                ))

        # Sort by engagement score
        recommendations.sort(key=lambda x: x.engagement_score, reverse=True)

        return recommendations

    async def sync_platform_analytics(
        self,
        user_id: uuid.UUID,
        platform: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Sync latest analytics from connected platforms.

        Returns dict of platform -> success status.
        """
        # Get accounts to sync
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platform:
            query = query.where(SocialAccount.platform == platform)

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        sync_results = {}

        for account in accounts:
            try:
                adapter = await self._get_adapter(account.platform)
                if not adapter:
                    sync_results[account.platform] = False
                    continue

                # Fetch analytics from platform
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=7)

                analytics_data = await adapter.get_analytics(
                    access_token=account.access_token,
                    start_date=start_date,
                    end_date=end_date,
                )

                # Store analytics data
                for data in analytics_data:
                    analytics_record = AnalyticsDaily(
                        account_id=account.id,
                        date=data.date if hasattr(data, 'date') else end_date.date(),
                        post_id=getattr(data, 'post_id', None),
                        impressions=getattr(data, 'impressions', 0),
                        reach=getattr(data, 'reach', 0),
                        likes=getattr(data, 'likes', 0),
                        comments=getattr(data, 'comments', 0),
                        shares=getattr(data, 'shares', 0),
                        saves=getattr(data, 'saves', 0),
                        clicks=getattr(data, 'clicks', 0),
                        views=getattr(data, 'views', 0),
                        watch_time_seconds=getattr(data, 'watch_time_seconds', None),
                    )
                    self.db.add(analytics_record)

                await self.db.commit()
                sync_results[account.platform] = True

            except Exception as e:
                sync_results[account.platform] = False
                # Log error but continue with other platforms

        return sync_results

    async def get_comparative_analytics(
        self,
        user_id: uuid.UUID,
        compare_period_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get comparative analytics showing platform performance side-by-side.
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=compare_period_days)

        metrics = await self.get_unified_metrics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Build comparison data
        comparison = {
            "period_days": compare_period_days,
            "platforms": {},
            "rankings": {
                "by_engagement": [],
                "by_reach": [],
                "by_growth": [],
            },
        }

        for platform in metrics.platform_breakdown:
            comparison["platforms"][platform.platform] = {
                "impressions": platform.impressions,
                "reach": platform.reach,
                "engagement": platform.engagement,
                "engagement_rate": round(platform.engagement_rate, 2),
                "followers": platform.followers,
                "follower_change": platform.follower_change,
                "posts_count": platform.posts_count,
            }

        # Calculate rankings
        by_engagement = sorted(
            metrics.platform_breakdown,
            key=lambda x: x.engagement,
            reverse=True
        )
        comparison["rankings"]["by_engagement"] = [p.platform for p in by_engagement]

        by_reach = sorted(
            metrics.platform_breakdown,
            key=lambda x: x.reach,
            reverse=True
        )
        comparison["rankings"]["by_reach"] = [p.platform for p in by_reach]

        by_growth = sorted(
            metrics.platform_breakdown,
            key=lambda x: x.follower_change,
            reverse=True
        )
        comparison["rankings"]["by_growth"] = [p.platform for p in by_growth]

        return comparison

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _aggregate_by_week(self, points: List[TimeSeriesPoint]) -> List[TimeSeriesPoint]:
        """Aggregate daily points into weekly."""
        if not points:
            return []

        weekly = {}
        for point in points:
            week_start = point.date - timedelta(days=point.date.weekday())
            week_key = week_start.date()
            if week_key not in weekly:
                weekly[week_key] = 0
            weekly[week_key] += point.value

        return [
            TimeSeriesPoint(
                date=datetime.combine(week, datetime.min.time()),
                value=value
            )
            for week, value in sorted(weekly.items())
        ]

    def _aggregate_by_month(self, points: List[TimeSeriesPoint]) -> List[TimeSeriesPoint]:
        """Aggregate daily points into monthly."""
        if not points:
            return []

        monthly = {}
        for point in points:
            month_key = point.date.replace(day=1).date()
            if month_key not in monthly:
                monthly[month_key] = 0
            monthly[month_key] += point.value

        return [
            TimeSeriesPoint(
                date=datetime.combine(month, datetime.min.time()),
                value=value
            )
            for month, value in sorted(monthly.items())
        ]
