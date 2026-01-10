"""
Competitor Analysis Service

Analyzes competitor influencers to provide strategic insights.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class CompetitorType(str, Enum):
    """Types of competitor relationships."""
    DIRECT = "direct"  # Same niche, similar audience size
    ASPIRATIONAL = "aspirational"  # Same niche, larger audience
    ADJACENT = "adjacent"  # Related niche
    EMERGING = "emerging"  # Smaller but fast-growing


class ContentCategory(str, Enum):
    """Content categories for analysis."""
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    INSPIRATIONAL = "inspirational"
    PROMOTIONAL = "promotional"
    PERSONAL = "personal"
    NEWS = "news"
    TUTORIAL = "tutorial"


@dataclass
class CompetitorProfile:
    """Profile data for a competitor."""
    competitor_id: str
    platform: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    # Audience metrics
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0

    # Engagement metrics
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    avg_shares: float = 0.0
    avg_views: float = 0.0
    engagement_rate: float = 0.0

    # Growth metrics
    follower_growth_rate: float = 0.0  # % growth per month
    follower_growth_30d: int = 0

    # Content insights
    posting_frequency: float = 0.0  # posts per week
    best_posting_times: list[str] = field(default_factory=list)
    top_hashtags: list[str] = field(default_factory=list)
    content_categories: dict[str, float] = field(default_factory=dict)

    # Niche data
    niche_tags: list[str] = field(default_factory=list)
    competitor_type: CompetitorType = CompetitorType.DIRECT

    # Analysis timestamps
    last_updated: Optional[datetime] = None
    data_freshness_hours: float = 0.0


@dataclass
class ContentInsight:
    """Insight from competitor content analysis."""
    content_id: str
    platform: str
    content_type: str  # video, image, text, carousel
    posted_at: datetime

    # Performance
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0

    # Content analysis
    caption: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    category: Optional[ContentCategory] = None
    topics: list[str] = field(default_factory=list)
    sentiment: Optional[str] = None

    # What made it successful
    success_factors: list[str] = field(default_factory=list)
    hook_text: Optional[str] = None
    cta_text: Optional[str] = None


@dataclass
class CompetitorComparison:
    """Comparison between user and competitor."""
    competitor: CompetitorProfile

    # Relative metrics (user / competitor)
    follower_ratio: float = 0.0
    engagement_ratio: float = 0.0
    posting_frequency_ratio: float = 0.0
    growth_rate_ratio: float = 0.0

    # Gaps and opportunities
    content_gaps: list[str] = field(default_factory=list)  # Topics competitor covers that user doesn't
    hashtag_opportunities: list[str] = field(default_factory=list)  # Hashtags competitor uses effectively
    timing_insights: list[str] = field(default_factory=list)  # When competitor posts successfully

    # Strategic recommendations
    recommendations: list[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high


@dataclass
class CompetitorReport:
    """Full competitor analysis report."""
    user_id: str
    platform: str
    generated_at: datetime

    # User baseline
    user_profile: dict = field(default_factory=dict)

    # Competitors
    competitors: list[CompetitorProfile] = field(default_factory=list)
    comparisons: list[CompetitorComparison] = field(default_factory=list)

    # Aggregated insights
    market_position: str = ""  # "leader", "challenger", "follower", "nicher"
    market_share_estimate: float = 0.0

    # Top performing content across competitors
    top_content: list[ContentInsight] = field(default_factory=list)

    # Trends in the competitive landscape
    emerging_trends: list[str] = field(default_factory=list)
    declining_trends: list[str] = field(default_factory=list)

    # Strategic summary
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)

    # Action items
    priority_actions: list[str] = field(default_factory=list)


class CompetitorAnalyzer:
    """
    Analyzes competitors to provide strategic insights.

    Features:
    - Competitor discovery based on niche/keywords
    - Performance benchmarking
    - Content strategy analysis
    - Growth comparison
    - Opportunity identification
    """

    def __init__(
        self,
        social_adapters: Optional[dict] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize competitor analyzer.

        Args:
            social_adapters: Dict of platform to adapter for fetching data
            llm_client: LLM client for content analysis
        """
        self.social_adapters = social_adapters or {}
        self.llm_client = llm_client
        self._cache: dict[str, Any] = {}

    async def discover_competitors(
        self,
        user_id: str,
        platform: str,
        niche_keywords: list[str],
        follower_range: tuple[int, int] = (1000, 1000000),
        limit: int = 20,
    ) -> list[CompetitorProfile]:
        """
        Discover potential competitors based on niche keywords.

        Args:
            user_id: User ID for context
            platform: Platform to search
            niche_keywords: Keywords describing the niche
            follower_range: Min/max follower count
            limit: Maximum competitors to return

        Returns:
            List of potential competitors
        """
        competitors = []

        # Search using platform adapter
        adapter = self.social_adapters.get(platform)
        if not adapter:
            # Return mock data for demo
            return self._generate_mock_competitors(
                platform, niche_keywords, follower_range, limit
            )

        try:
            # Search for each keyword
            for keyword in niche_keywords:
                results = await adapter.search_users(
                    query=keyword,
                    min_followers=follower_range[0],
                    max_followers=follower_range[1],
                    limit=limit // len(niche_keywords),
                )

                for result in results:
                    profile = await self._fetch_competitor_profile(
                        platform, result.get("username")
                    )
                    if profile:
                        profile.niche_tags = niche_keywords
                        competitors.append(profile)

        except Exception as e:
            logger.error(f"Error discovering competitors: {e}")

        # Deduplicate and sort by relevance
        seen = set()
        unique_competitors = []
        for c in competitors:
            if c.username not in seen:
                seen.add(c.username)
                unique_competitors.append(c)

        # Sort by engagement rate
        unique_competitors.sort(key=lambda x: x.engagement_rate, reverse=True)

        return unique_competitors[:limit]

    async def analyze_competitor(
        self,
        platform: str,
        username: str,
        include_content: bool = True,
        content_limit: int = 50,
    ) -> CompetitorProfile:
        """
        Perform deep analysis of a single competitor.

        Args:
            platform: Platform name
            username: Competitor username
            include_content: Whether to analyze their content
            content_limit: Number of posts to analyze

        Returns:
            Detailed competitor profile
        """
        profile = await self._fetch_competitor_profile(platform, username)

        if include_content and profile:
            # Analyze recent content
            content_analysis = await self._analyze_competitor_content(
                platform, username, content_limit
            )
            profile.top_hashtags = content_analysis.get("top_hashtags", [])
            profile.content_categories = content_analysis.get("categories", {})
            profile.best_posting_times = content_analysis.get("best_times", [])

        return profile

    async def compare_with_user(
        self,
        user_id: str,
        user_profile: dict,
        competitor: CompetitorProfile,
    ) -> CompetitorComparison:
        """
        Compare user metrics with a competitor.

        Args:
            user_id: User ID
            user_profile: User's profile metrics
            competitor: Competitor profile to compare

        Returns:
            Comparison analysis
        """
        user_followers = user_profile.get("follower_count", 1)
        user_engagement = user_profile.get("engagement_rate", 0)
        user_posting_freq = user_profile.get("posting_frequency", 0)
        user_growth = user_profile.get("growth_rate", 0)

        comparison = CompetitorComparison(
            competitor=competitor,
            follower_ratio=user_followers / max(competitor.follower_count, 1),
            engagement_ratio=user_engagement / max(competitor.engagement_rate, 0.01),
            posting_frequency_ratio=user_posting_freq / max(competitor.posting_frequency, 0.1),
            growth_rate_ratio=user_growth / max(competitor.follower_growth_rate, 0.01),
        )

        # Identify content gaps
        comparison.content_gaps = self._identify_content_gaps(
            user_profile.get("content_categories", {}),
            competitor.content_categories,
        )

        # Identify hashtag opportunities
        user_hashtags = set(user_profile.get("top_hashtags", []))
        competitor_hashtags = set(competitor.top_hashtags)
        comparison.hashtag_opportunities = list(competitor_hashtags - user_hashtags)[:10]

        # Generate timing insights
        comparison.timing_insights = self._generate_timing_insights(
            competitor.best_posting_times
        )

        # Generate recommendations
        comparison.recommendations = self._generate_recommendations(comparison)

        # Set priority based on competitor type and gaps
        if len(comparison.content_gaps) > 3 or comparison.engagement_ratio < 0.5:
            comparison.priority = "high"
        elif len(comparison.content_gaps) > 1 or comparison.engagement_ratio < 0.8:
            comparison.priority = "medium"
        else:
            comparison.priority = "low"

        return comparison

    async def generate_report(
        self,
        user_id: str,
        platform: str,
        competitors: list[CompetitorProfile],
        user_profile: dict,
    ) -> CompetitorReport:
        """
        Generate a comprehensive competitor analysis report.

        Args:
            user_id: User ID
            platform: Platform being analyzed
            competitors: List of competitors to include
            user_profile: User's profile metrics

        Returns:
            Full analysis report
        """
        report = CompetitorReport(
            user_id=user_id,
            platform=platform,
            generated_at=datetime.utcnow(),
            user_profile=user_profile,
            competitors=competitors,
        )

        # Compare with each competitor
        for competitor in competitors:
            comparison = await self.compare_with_user(
                user_id, user_profile, competitor
            )
            report.comparisons.append(comparison)

        # Determine market position
        report.market_position = self._determine_market_position(
            user_profile, competitors
        )

        # Aggregate trends
        all_hashtags = []
        for c in competitors:
            all_hashtags.extend(c.top_hashtags)

        # Count hashtag frequency
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

        # Sort by frequency
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        report.emerging_trends = [tag for tag, count in sorted_hashtags[:10] if count >= 2]

        # SWOT analysis
        report.strengths, report.weaknesses, report.opportunities, report.threats = \
            self._generate_swot(user_profile, competitors, report.comparisons)

        # Priority actions
        report.priority_actions = self._generate_priority_actions(report)

        return report

    async def _fetch_competitor_profile(
        self,
        platform: str,
        username: str,
    ) -> Optional[CompetitorProfile]:
        """Fetch competitor profile from platform."""
        cache_key = f"{platform}:{username}"

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.utcnow() - cached["timestamp"]).total_seconds() < 3600:
                return cached["profile"]

        adapter = self.social_adapters.get(platform)

        if not adapter:
            # Return mock profile
            return self._generate_mock_profile(platform, username)

        try:
            data = await adapter.get_user_profile(username)

            profile = CompetitorProfile(
                competitor_id=data.get("id", username),
                platform=platform,
                username=username,
                display_name=data.get("display_name"),
                profile_url=data.get("profile_url"),
                avatar_url=data.get("avatar_url"),
                bio=data.get("bio"),
                follower_count=data.get("follower_count", 0),
                following_count=data.get("following_count", 0),
                post_count=data.get("post_count", 0),
                avg_likes=data.get("avg_likes", 0),
                avg_comments=data.get("avg_comments", 0),
                engagement_rate=data.get("engagement_rate", 0),
                follower_growth_rate=data.get("growth_rate", 0),
                posting_frequency=data.get("posting_frequency", 0),
                last_updated=datetime.utcnow(),
            )

            self._cache[cache_key] = {
                "profile": profile,
                "timestamp": datetime.utcnow(),
            }

            return profile

        except Exception as e:
            logger.error(f"Error fetching profile for {username}: {e}")
            return None

    async def _analyze_competitor_content(
        self,
        platform: str,
        username: str,
        limit: int,
    ) -> dict:
        """Analyze competitor's recent content."""
        adapter = self.social_adapters.get(platform)

        if not adapter:
            return self._generate_mock_content_analysis()

        try:
            posts = await adapter.get_user_posts(username, limit=limit)

            # Analyze hashtags
            all_hashtags = []
            for post in posts:
                all_hashtags.extend(post.get("hashtags", []))

            hashtag_counts = {}
            for tag in all_hashtags:
                hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

            top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:20]

            # Analyze posting times
            posting_times = []
            for post in posts:
                if post.get("created_at"):
                    posting_times.append(post["created_at"])

            best_times = self._calculate_best_posting_times(posting_times)

            # Analyze content categories (would use LLM in production)
            categories = self._estimate_content_categories(posts)

            return {
                "top_hashtags": [tag for tag, _ in top_hashtags],
                "best_times": best_times,
                "categories": categories,
            }

        except Exception as e:
            logger.error(f"Error analyzing content for {username}: {e}")
            return {}

    def _generate_mock_competitors(
        self,
        platform: str,
        keywords: list[str],
        follower_range: tuple[int, int],
        limit: int,
    ) -> list[CompetitorProfile]:
        """Generate mock competitor data for demo."""
        import random

        competitors = []
        names = [
            "creator_pro", "influencer_hub", "content_king", "viral_master",
            "digital_guru", "social_star", "trend_setter", "niche_expert",
            "growth_hacker", "engagement_pro"
        ]

        for i, name in enumerate(names[:limit]):
            followers = random.randint(follower_range[0], follower_range[1])

            competitors.append(CompetitorProfile(
                competitor_id=f"mock_{i}",
                platform=platform,
                username=f"{name}_{platform}",
                display_name=name.replace("_", " ").title(),
                follower_count=followers,
                following_count=random.randint(100, 5000),
                post_count=random.randint(100, 2000),
                avg_likes=random.randint(100, followers // 10),
                avg_comments=random.randint(10, followers // 100),
                engagement_rate=random.uniform(2.0, 10.0),
                follower_growth_rate=random.uniform(-2.0, 15.0),
                posting_frequency=random.uniform(3.0, 14.0),
                top_hashtags=random.sample(keywords, min(3, len(keywords))) + ["trending", "viral"],
                content_categories={
                    "educational": random.uniform(0.1, 0.4),
                    "entertainment": random.uniform(0.1, 0.4),
                    "promotional": random.uniform(0.1, 0.3),
                },
                best_posting_times=["9:00 AM", "12:00 PM", "6:00 PM"],
                niche_tags=keywords,
                last_updated=datetime.utcnow(),
            ))

        return competitors

    def _generate_mock_profile(self, platform: str, username: str) -> CompetitorProfile:
        """Generate mock profile for demo."""
        import random

        return CompetitorProfile(
            competitor_id=f"mock_{username}",
            platform=platform,
            username=username,
            display_name=username.replace("_", " ").title(),
            follower_count=random.randint(10000, 500000),
            following_count=random.randint(100, 5000),
            post_count=random.randint(100, 2000),
            avg_likes=random.randint(500, 10000),
            avg_comments=random.randint(50, 500),
            engagement_rate=random.uniform(2.0, 8.0),
            follower_growth_rate=random.uniform(1.0, 10.0),
            posting_frequency=random.uniform(5.0, 10.0),
            top_hashtags=["trending", "viral", "fyp", "explore"],
            content_categories={
                "educational": 0.3,
                "entertainment": 0.4,
                "promotional": 0.2,
                "personal": 0.1,
            },
            best_posting_times=["9:00 AM", "12:00 PM", "6:00 PM", "9:00 PM"],
            last_updated=datetime.utcnow(),
        )

    def _generate_mock_content_analysis(self) -> dict:
        """Generate mock content analysis for demo."""
        return {
            "top_hashtags": ["trending", "viral", "fyp", "explore", "creator", "content"],
            "best_times": ["9:00 AM", "12:00 PM", "6:00 PM"],
            "categories": {
                "educational": 0.3,
                "entertainment": 0.4,
                "promotional": 0.2,
                "personal": 0.1,
            },
        }

    def _identify_content_gaps(
        self,
        user_categories: dict,
        competitor_categories: dict,
    ) -> list[str]:
        """Identify content categories where competitor is stronger."""
        gaps = []

        for category, competitor_share in competitor_categories.items():
            user_share = user_categories.get(category, 0)
            if competitor_share > user_share + 0.1:
                gaps.append(f"{category} content ({int(competitor_share * 100)}% vs your {int(user_share * 100)}%)")

        return gaps

    def _generate_timing_insights(self, best_times: list[str]) -> list[str]:
        """Generate insights about posting times."""
        insights = []

        if best_times:
            insights.append(f"Best performing times: {', '.join(best_times[:3])}")
            insights.append("Consider testing these times for your content")

        return insights

    def _generate_recommendations(self, comparison: CompetitorComparison) -> list[str]:
        """Generate strategic recommendations based on comparison."""
        recommendations = []

        # Engagement recommendations
        if comparison.engagement_ratio < 0.8:
            recommendations.append(
                "Focus on engagement - your competitor has higher engagement rates. "
                "Try more interactive content like polls, questions, or challenges."
            )

        # Content gap recommendations
        if comparison.content_gaps:
            recommendations.append(
                f"Content opportunity: Consider creating more {comparison.content_gaps[0]}"
            )

        # Hashtag recommendations
        if comparison.hashtag_opportunities:
            top_tags = comparison.hashtag_opportunities[:5]
            recommendations.append(
                f"Try these hashtags: {', '.join(['#' + tag for tag in top_tags])}"
            )

        # Posting frequency
        if comparison.posting_frequency_ratio < 0.7:
            recommendations.append(
                "Increase posting frequency to match competitor's visibility"
            )

        return recommendations

    def _determine_market_position(
        self,
        user_profile: dict,
        competitors: list[CompetitorProfile],
    ) -> str:
        """Determine user's market position relative to competitors."""
        user_followers = user_profile.get("follower_count", 0)
        user_engagement = user_profile.get("engagement_rate", 0)

        avg_competitor_followers = sum(c.follower_count for c in competitors) / max(len(competitors), 1)
        avg_competitor_engagement = sum(c.engagement_rate for c in competitors) / max(len(competitors), 1)

        # Determine position based on relative metrics
        if user_followers > avg_competitor_followers * 1.5 and user_engagement > avg_competitor_engagement:
            return "leader"
        elif user_followers > avg_competitor_followers * 0.8:
            return "challenger"
        elif user_engagement > avg_competitor_engagement * 1.2:
            return "nicher"  # Smaller but highly engaged
        else:
            return "follower"

    def _calculate_best_posting_times(self, timestamps: list[datetime]) -> list[str]:
        """Calculate best posting times from engagement data."""
        if not timestamps:
            return ["9:00 AM", "12:00 PM", "6:00 PM"]

        # Group by hour
        hour_counts = {}
        for ts in timestamps:
            hour = ts.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Sort by count
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)

        # Convert to readable format
        best_times = []
        for hour, _ in sorted_hours[:3]:
            if hour < 12:
                best_times.append(f"{hour}:00 AM" if hour > 0 else "12:00 AM")
            elif hour == 12:
                best_times.append("12:00 PM")
            else:
                best_times.append(f"{hour - 12}:00 PM")

        return best_times

    def _estimate_content_categories(self, posts: list[dict]) -> dict:
        """Estimate content categories from posts."""
        # In production, this would use LLM for classification
        # For now, return default distribution
        return {
            "educational": 0.25,
            "entertainment": 0.35,
            "promotional": 0.2,
            "personal": 0.2,
        }

    def _generate_swot(
        self,
        user_profile: dict,
        competitors: list[CompetitorProfile],
        comparisons: list[CompetitorComparison],
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        """Generate SWOT analysis."""
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []

        user_engagement = user_profile.get("engagement_rate", 0)
        avg_comp_engagement = sum(c.competitor.engagement_rate for c in comparisons) / max(len(comparisons), 1)

        # Strengths
        if user_engagement > avg_comp_engagement:
            strengths.append("Higher than average engagement rate")

        for comp in comparisons:
            if comp.engagement_ratio > 1.2:
                strengths.append(f"Outperforming {comp.competitor.username} in engagement")

        # Weaknesses
        all_content_gaps = []
        for comp in comparisons:
            all_content_gaps.extend(comp.content_gaps)

        if all_content_gaps:
            unique_gaps = list(set(all_content_gaps))[:3]
            weaknesses.append(f"Content gaps in: {', '.join(unique_gaps)}")

        # Opportunities
        all_hashtags = []
        for comp in comparisons:
            all_hashtags.extend(comp.hashtag_opportunities)

        if all_hashtags:
            unique_tags = list(set(all_hashtags))[:5]
            opportunities.append(f"Untapped hashtags: {', '.join(['#' + t for t in unique_tags])}")

        # Threats
        fast_growing = [c for c in competitors if c.follower_growth_rate > 10]
        if fast_growing:
            threats.append(f"{len(fast_growing)} competitors growing rapidly (>10%/month)")

        return strengths, weaknesses, opportunities, threats

    def _generate_priority_actions(self, report: CompetitorReport) -> list[str]:
        """Generate prioritized action items."""
        actions = []

        # From comparisons
        high_priority_comps = [c for c in report.comparisons if c.priority == "high"]
        for comp in high_priority_comps[:2]:
            if comp.recommendations:
                actions.append(comp.recommendations[0])

        # From opportunities
        if report.opportunities:
            actions.append(f"Opportunity: {report.opportunities[0]}")

        # From weaknesses
        if report.weaknesses:
            actions.append(f"Address: {report.weaknesses[0]}")

        return actions[:5]  # Top 5 actions
