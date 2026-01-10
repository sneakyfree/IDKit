"""
Trend Detection Service

Monitor and detect trending topics, hashtags, and content opportunities
across social platforms using AI analysis.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.social import SocialAccount


class TrendCategory(str, Enum):
    """Categories of trends."""
    HASHTAG = "hashtag"
    TOPIC = "topic"
    AUDIO = "audio"
    CHALLENGE = "challenge"
    FORMAT = "format"
    MEME = "meme"
    NEWS = "news"
    SEASONAL = "seasonal"


class TrendVelocity(str, Enum):
    """How fast a trend is growing."""
    EMERGING = "emerging"  # Just starting
    RISING = "rising"  # Growing quickly
    PEAK = "peak"  # At maximum popularity
    DECLINING = "declining"  # Past peak
    STABLE = "stable"  # Consistent popularity


@dataclass
class Trend:
    """A detected trend."""
    id: str
    name: str
    category: TrendCategory
    platforms: List[str]

    # Popularity metrics
    volume: int  # Number of posts/mentions
    velocity: TrendVelocity
    growth_rate: float  # Percentage growth
    engagement_rate: float  # Average engagement

    # Timing
    first_seen: datetime
    peak_time: Optional[datetime]
    predicted_duration_hours: int

    # Content
    description: Optional[str]
    related_hashtags: List[str] = field(default_factory=list)
    example_content: List[str] = field(default_factory=list)
    audio_url: Optional[str] = None  # For audio trends

    # Relevance
    relevance_score: float = 0.0  # 0-1, how relevant to user's niche
    difficulty_score: float = 0.5  # 0-1, how hard to create content for
    opportunity_score: float = 0.0  # 0-1, overall opportunity rating

    # Metadata
    source: str = "platform"  # "platform", "ai_detected", "user_reported"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrendAlert:
    """Alert for a trend opportunity."""
    trend: Trend
    alert_type: str  # "new_trend", "peak_soon", "relevant_match", "competitor_using"
    message: str
    action_suggestion: str
    urgency: str  # "low", "medium", "high"
    expires_at: datetime


@dataclass
class TrendReport:
    """Summary report of trending content."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    platform: Optional[str]

    top_hashtags: List[Trend]
    top_topics: List[Trend]
    top_audios: List[Trend]
    emerging_trends: List[Trend]

    recommendations: List[str]
    content_ideas: List[Dict[str, Any]]


class TrendDetectorService:
    """
    AI-powered trend detection and monitoring service.

    Features:
    - Real-time trend monitoring
    - Platform-specific trend tracking
    - Relevance scoring based on user's niche
    - Content opportunity detection
    - Trend velocity analysis
    - AI-generated content suggestions
    """

    # Platform-specific trend endpoints (would use actual APIs in production)
    PLATFORM_TREND_SOURCES = {
        "tiktok": "TikTok Creative Center",
        "instagram": "Instagram Explore",
        "twitter": "Twitter Trends",
        "youtube": "YouTube Trending",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None
        self._trends_cache: Dict[str, List[Trend]] = {}
        self._user_niches: Dict[uuid.UUID, List[str]] = {}
        self._last_update: Dict[str, datetime] = {}

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    # =========================================================================
    # TREND DISCOVERY
    # =========================================================================

    async def get_trending(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
        categories: Optional[List[TrendCategory]] = None,
        limit: int = 20,
        include_relevance: bool = True,
    ) -> List[Trend]:
        """
        Get current trending topics and hashtags.

        Args:
            user_id: User to get trends for (for relevance scoring)
            platforms: Filter by platforms
            categories: Filter by trend categories
            limit: Maximum trends to return
            include_relevance: Calculate relevance to user's niche

        Returns:
            List of Trend objects sorted by opportunity score
        """
        all_trends = []

        # Get cached trends or fetch new
        target_platforms = platforms or ["tiktok", "instagram", "twitter", "youtube"]

        for platform in target_platforms:
            platform_trends = await self._get_platform_trends(platform)
            all_trends.extend(platform_trends)

        # Filter by category
        if categories:
            category_values = [c.value for c in categories]
            all_trends = [t for t in all_trends if t.category.value in category_values]

        # Calculate relevance if requested
        if include_relevance:
            user_niche = await self._get_user_niche(user_id)
            for trend in all_trends:
                trend.relevance_score = await self._calculate_relevance(trend, user_niche)
                trend.opportunity_score = self._calculate_opportunity(trend)

        # Sort by opportunity score
        all_trends.sort(key=lambda t: t.opportunity_score, reverse=True)

        return all_trends[:limit]

    async def _get_platform_trends(self, platform: str) -> List[Trend]:
        """Get trends for a specific platform."""
        # Check cache freshness (15 minute TTL)
        cache_key = platform
        now = datetime.now(timezone.utc)

        if cache_key in self._last_update:
            if now - self._last_update[cache_key] < timedelta(minutes=15):
                return self._trends_cache.get(cache_key, [])

        # In production, this would call actual platform APIs
        # For now, generate sample trends
        trends = await self._fetch_platform_trends(platform)

        # Cache results
        self._trends_cache[cache_key] = trends
        self._last_update[cache_key] = now

        return trends

    async def _fetch_platform_trends(self, platform: str) -> List[Trend]:
        """
        Fetch trends from platform API.

        In production, this would integrate with:
        - TikTok Creative Center API
        - Instagram Graph API
        - Twitter Trends API
        - YouTube Trending API
        """
        # Generate sample trends for demonstration
        now = datetime.now(timezone.utc)

        sample_trends = []

        if platform == "tiktok":
            sample_trends = [
                Trend(
                    id=f"tiktok_trend_1",
                    name="#MorningRoutine",
                    category=TrendCategory.HASHTAG,
                    platforms=["tiktok"],
                    volume=1500000,
                    velocity=TrendVelocity.RISING,
                    growth_rate=25.5,
                    engagement_rate=8.2,
                    first_seen=now - timedelta(days=3),
                    peak_time=now + timedelta(hours=12),
                    predicted_duration_hours=72,
                    description="Morning routine content showing daily habits",
                    related_hashtags=["#GRWM", "#DayInMyLife", "#HealthyHabits"],
                ),
                Trend(
                    id=f"tiktok_trend_2",
                    name="POV Transitions",
                    category=TrendCategory.FORMAT,
                    platforms=["tiktok"],
                    volume=800000,
                    velocity=TrendVelocity.PEAK,
                    growth_rate=5.2,
                    engagement_rate=12.5,
                    first_seen=now - timedelta(days=7),
                    peak_time=now,
                    predicted_duration_hours=48,
                    description="Point-of-view transition videos with creative cuts",
                    related_hashtags=["#POV", "#Transition", "#Viral"],
                ),
                Trend(
                    id=f"tiktok_trend_3",
                    name="AI Generated Art",
                    category=TrendCategory.TOPIC,
                    platforms=["tiktok", "instagram"],
                    volume=2000000,
                    velocity=TrendVelocity.RISING,
                    growth_rate=45.0,
                    engagement_rate=6.8,
                    first_seen=now - timedelta(days=14),
                    peak_time=now + timedelta(days=3),
                    predicted_duration_hours=168,
                    description="Content showcasing AI art generation and reactions",
                    related_hashtags=["#AIArt", "#Midjourney", "#DALLE"],
                ),
            ]
        elif platform == "instagram":
            sample_trends = [
                Trend(
                    id=f"instagram_trend_1",
                    name="#Reels",
                    category=TrendCategory.HASHTAG,
                    platforms=["instagram"],
                    volume=5000000,
                    velocity=TrendVelocity.STABLE,
                    growth_rate=2.1,
                    engagement_rate=5.5,
                    first_seen=now - timedelta(days=365),
                    peak_time=None,
                    predicted_duration_hours=8760,
                    description="Instagram Reels short-form video content",
                    related_hashtags=["#ReelsViral", "#InstaReels"],
                ),
                Trend(
                    id=f"instagram_trend_2",
                    name="Carousel Educational Content",
                    category=TrendCategory.FORMAT,
                    platforms=["instagram", "linkedin"],
                    volume=1200000,
                    velocity=TrendVelocity.RISING,
                    growth_rate=18.3,
                    engagement_rate=9.2,
                    first_seen=now - timedelta(days=30),
                    peak_time=now + timedelta(days=7),
                    predicted_duration_hours=336,
                    description="Educational content in carousel/slide format",
                    related_hashtags=["#LearnOnInstagram", "#EducationalContent"],
                ),
            ]
        elif platform == "twitter":
            sample_trends = [
                Trend(
                    id=f"twitter_trend_1",
                    name="#TechTwitter",
                    category=TrendCategory.HASHTAG,
                    platforms=["twitter"],
                    volume=300000,
                    velocity=TrendVelocity.STABLE,
                    growth_rate=1.5,
                    engagement_rate=4.2,
                    first_seen=now - timedelta(days=180),
                    peak_time=None,
                    predicted_duration_hours=4320,
                    description="Technology discussions and news",
                    related_hashtags=["#Tech", "#Coding", "#AI"],
                ),
            ]
        elif platform == "youtube":
            sample_trends = [
                Trend(
                    id=f"youtube_trend_1",
                    name="Day in My Life Vlogs",
                    category=TrendCategory.FORMAT,
                    platforms=["youtube"],
                    volume=800000,
                    velocity=TrendVelocity.STABLE,
                    growth_rate=3.2,
                    engagement_rate=6.1,
                    first_seen=now - timedelta(days=365),
                    peak_time=None,
                    predicted_duration_hours=8760,
                    description="Daily life vlogs showing routines and activities",
                    related_hashtags=["#Vlog", "#DayInMyLife"],
                ),
                Trend(
                    id=f"youtube_trend_2",
                    name="#Shorts",
                    category=TrendCategory.FORMAT,
                    platforms=["youtube"],
                    volume=10000000,
                    velocity=TrendVelocity.RISING,
                    growth_rate=35.0,
                    engagement_rate=8.5,
                    first_seen=now - timedelta(days=180),
                    peak_time=now + timedelta(days=30),
                    predicted_duration_hours=2160,
                    description="YouTube Shorts vertical video format",
                    related_hashtags=["#YouTubeShorts", "#Viral"],
                ),
            ]

        return sample_trends

    async def _get_user_niche(self, user_id: uuid.UUID) -> List[str]:
        """Get user's content niche/topics."""
        if user_id in self._user_niches:
            return self._user_niches[user_id]

        # In production, analyze user's content history
        # For now, return default
        return ["general", "lifestyle"]

    async def _calculate_relevance(
        self,
        trend: Trend,
        user_niche: List[str],
    ) -> float:
        """Calculate how relevant a trend is to user's niche."""
        # In production, use AI to analyze relevance
        # For now, simple keyword matching

        niche_keywords = {
            "tech": ["ai", "tech", "coding", "software", "app"],
            "lifestyle": ["routine", "life", "day", "grwm", "habits"],
            "fitness": ["workout", "fitness", "health", "gym", "exercise"],
            "beauty": ["makeup", "skincare", "beauty", "cosmetics"],
            "food": ["recipe", "cooking", "food", "restaurant", "meal"],
            "travel": ["travel", "adventure", "destination", "trip"],
            "business": ["entrepreneur", "business", "startup", "money"],
            "general": [],
        }

        trend_text = f"{trend.name} {trend.description or ''} {' '.join(trend.related_hashtags)}".lower()

        relevance = 0.3  # Base relevance

        for niche in user_niche:
            keywords = niche_keywords.get(niche, [])
            for keyword in keywords:
                if keyword in trend_text:
                    relevance += 0.15

        return min(1.0, relevance)

    def _calculate_opportunity(self, trend: Trend) -> float:
        """Calculate overall opportunity score for a trend."""
        # Factors: velocity, engagement, relevance, difficulty

        velocity_scores = {
            TrendVelocity.EMERGING: 0.9,
            TrendVelocity.RISING: 1.0,
            TrendVelocity.PEAK: 0.7,
            TrendVelocity.DECLINING: 0.3,
            TrendVelocity.STABLE: 0.5,
        }

        velocity_factor = velocity_scores.get(trend.velocity, 0.5)
        engagement_factor = min(1.0, trend.engagement_rate / 10)
        relevance_factor = trend.relevance_score
        ease_factor = 1 - trend.difficulty_score

        # Weighted average
        score = (
            velocity_factor * 0.3 +
            engagement_factor * 0.25 +
            relevance_factor * 0.3 +
            ease_factor * 0.15
        )

        return round(score, 3)

    # =========================================================================
    # TREND ANALYSIS
    # =========================================================================

    async def analyze_trend(
        self,
        trend_id: str,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of a specific trend.
        """
        # Find trend
        trend = None
        for platform_trends in self._trends_cache.values():
            for t in platform_trends:
                if t.id == trend_id:
                    trend = t
                    break

        if not trend:
            raise ValueError("Trend not found")

        # Get AI analysis
        client = await self._get_llm_client()

        prompt = f"""Analyze this social media trend and provide actionable insights:

TREND: {trend.name}
CATEGORY: {trend.category.value}
PLATFORMS: {', '.join(trend.platforms)}
CURRENT VELOCITY: {trend.velocity.value}
ENGAGEMENT RATE: {trend.engagement_rate}%
DESCRIPTION: {trend.description or 'N/A'}
RELATED HASHTAGS: {', '.join(trend.related_hashtags)}

Provide:
1. Why this trend is popular (2-3 sentences)
2. Best content types to create for this trend
3. 3 specific content ideas
4. Best time to post for maximum impact
5. Potential risks or considerations
6. Predicted lifespan (how long will it stay relevant)

Format as JSON with keys: why_popular, best_content_types, content_ideas, best_posting_time, risks, predicted_lifespan"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media trend analyst providing actionable insights for content creators.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        import json
        analysis = {}
        try:
            response_text = response.choices[0].message.content
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                analysis = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            analysis = {
                "why_popular": "Unable to analyze",
                "best_content_types": [],
                "content_ideas": [],
                "best_posting_time": "N/A",
                "risks": "N/A",
                "predicted_lifespan": "N/A",
            }

        return {
            "trend": {
                "id": trend.id,
                "name": trend.name,
                "category": trend.category.value,
                "platforms": trend.platforms,
                "velocity": trend.velocity.value,
                "volume": trend.volume,
                "engagement_rate": trend.engagement_rate,
                "growth_rate": trend.growth_rate,
                "related_hashtags": trend.related_hashtags,
                "opportunity_score": trend.opportunity_score,
            },
            "analysis": analysis,
        }

    async def get_trend_report(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
        period_days: int = 7,
    ) -> TrendReport:
        """
        Generate a comprehensive trend report.
        """
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=period_days)

        # Get all trends
        all_trends = await self.get_trending(
            user_id=user_id,
            platforms=platforms,
            limit=50,
        )

        # Categorize trends
        hashtag_trends = [t for t in all_trends if t.category == TrendCategory.HASHTAG][:10]
        topic_trends = [t for t in all_trends if t.category == TrendCategory.TOPIC][:10]
        audio_trends = [t for t in all_trends if t.category == TrendCategory.AUDIO][:5]
        emerging = [t for t in all_trends if t.velocity == TrendVelocity.EMERGING][:5]

        # Generate AI recommendations
        recommendations = await self._generate_recommendations(all_trends[:10], user_id)

        # Generate content ideas
        content_ideas = await self._generate_content_ideas(all_trends[:5], user_id)

        return TrendReport(
            generated_at=now,
            period_start=period_start,
            period_end=now,
            platform=platforms[0] if platforms and len(platforms) == 1 else None,
            top_hashtags=hashtag_trends,
            top_topics=topic_trends,
            top_audios=audio_trends,
            emerging_trends=emerging,
            recommendations=recommendations,
            content_ideas=content_ideas,
        )

    async def _generate_recommendations(
        self,
        trends: List[Trend],
        user_id: uuid.UUID,
    ) -> List[str]:
        """Generate AI recommendations based on trends."""
        if not trends:
            return ["No trends available for recommendations"]

        trend_summary = "\n".join([
            f"- {t.name} ({t.category.value}, {t.velocity.value}, {t.engagement_rate}% engagement)"
            for t in trends[:5]
        ])

        client = await self._get_llm_client()

        prompt = f"""Based on these current trends, provide 5 actionable recommendations for a content creator:

TRENDS:
{trend_summary}

Provide specific, actionable recommendations that help the creator capitalize on these trends.
Return as a JSON array of 5 recommendation strings."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media strategist providing actionable recommendations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        import json
        recommendations = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                recommendations = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            recommendations = ["Check trending hashtags in your niche"]

        return recommendations[:5]

    async def _generate_content_ideas(
        self,
        trends: List[Trend],
        user_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Generate content ideas based on trends."""
        if not trends:
            return []

        ideas = []
        for trend in trends[:3]:
            ideas.append({
                "trend_id": trend.id,
                "trend_name": trend.name,
                "idea": f"Create content about {trend.name} with {', '.join(trend.related_hashtags[:3])}",
                "platforms": trend.platforms,
                "difficulty": "easy" if trend.difficulty_score < 0.3 else "medium" if trend.difficulty_score < 0.7 else "hard",
                "estimated_reach": trend.volume // 100,  # Rough estimate
            })

        return ideas

    # =========================================================================
    # TREND ALERTS
    # =========================================================================

    async def get_trend_alerts(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> List[TrendAlert]:
        """
        Get personalized trend alerts for a user.
        """
        all_trends = await self.get_trending(
            user_id=user_id,
            limit=30,
            include_relevance=True,
        )

        alerts = []
        now = datetime.now(timezone.utc)

        for trend in all_trends:
            # New emerging trend alert
            if trend.velocity == TrendVelocity.EMERGING and trend.relevance_score > 0.5:
                alerts.append(TrendAlert(
                    trend=trend,
                    alert_type="new_trend",
                    message=f"New trend '{trend.name}' is emerging and matches your niche!",
                    action_suggestion=f"Create content using {trend.name} and related hashtags",
                    urgency="high",
                    expires_at=now + timedelta(hours=24),
                ))

            # Peak soon alert
            if trend.velocity == TrendVelocity.RISING and trend.peak_time:
                hours_to_peak = (trend.peak_time - now).total_seconds() / 3600
                if 0 < hours_to_peak < 24:
                    alerts.append(TrendAlert(
                        trend=trend,
                        alert_type="peak_soon",
                        message=f"'{trend.name}' is about to peak in {int(hours_to_peak)} hours!",
                        action_suggestion="Post now to maximize visibility",
                        urgency="high" if hours_to_peak < 6 else "medium",
                        expires_at=trend.peak_time,
                    ))

            # High relevance match
            if trend.relevance_score > 0.7 and trend.opportunity_score > 0.6:
                alerts.append(TrendAlert(
                    trend=trend,
                    alert_type="relevant_match",
                    message=f"'{trend.name}' is highly relevant to your content",
                    action_suggestion=f"Consider incorporating into your content strategy",
                    urgency="medium",
                    expires_at=now + timedelta(hours=48),
                ))

        # Sort by urgency and limit
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda a: urgency_order.get(a.urgency, 2))

        return alerts[:limit]

    # =========================================================================
    # MONITORING
    # =========================================================================

    async def set_user_niche(
        self,
        user_id: uuid.UUID,
        niches: List[str],
    ):
        """Set user's content niches for relevance scoring."""
        self._user_niches[user_id] = niches

    async def track_hashtag(
        self,
        user_id: uuid.UUID,
        hashtag: str,
    ) -> Optional[Trend]:
        """
        Track a specific hashtag's trend status.
        """
        # Search for hashtag in cached trends
        hashtag_lower = hashtag.lower().strip("#")

        for platform_trends in self._trends_cache.values():
            for trend in platform_trends:
                if hashtag_lower in trend.name.lower():
                    return trend

        # If not found, create a new tracking entry
        # In production, this would query platform APIs
        return None

    async def refresh_trends(
        self,
        platforms: Optional[List[str]] = None,
    ):
        """Force refresh trends from platforms."""
        target_platforms = platforms or ["tiktok", "instagram", "twitter", "youtube"]

        for platform in target_platforms:
            # Clear cache for platform
            if platform in self._last_update:
                del self._last_update[platform]

            # Fetch fresh data
            await self._get_platform_trends(platform)
