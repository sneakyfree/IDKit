"""
Brand Deal Matcher Service

Matches influencers with brand partnership opportunities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class DealType(str, Enum):
    """Types of brand deals."""
    SPONSORED_POST = "sponsored_post"
    AFFILIATE = "affiliate"
    AMBASSADOR = "ambassador"
    PRODUCT_REVIEW = "product_review"
    GIVEAWAY = "giveaway"
    EVENT = "event"
    LONG_TERM = "long_term"
    UGC = "ugc"  # User Generated Content


class DealStatus(str, Enum):
    """Status of a brand deal."""
    DISCOVERED = "discovered"
    MATCHED = "matched"
    APPLIED = "applied"
    IN_NEGOTIATION = "in_negotiation"
    CONTRACTED = "contracted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class NicheCategory(str, Enum):
    """Influencer niche categories."""
    LIFESTYLE = "lifestyle"
    FASHION = "fashion"
    BEAUTY = "beauty"
    FITNESS = "fitness"
    FOOD = "food"
    TRAVEL = "travel"
    TECH = "tech"
    GAMING = "gaming"
    FINANCE = "finance"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    PARENTING = "parenting"
    HOME = "home"
    AUTOMOTIVE = "automotive"
    HEALTH = "health"
    SPORTS = "sports"
    PETS = "pets"
    ART = "art"
    MUSIC = "music"
    BUSINESS = "business"


@dataclass
class BrandProfile:
    """Profile of a brand looking for influencers."""
    brand_id: str
    name: str
    website: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

    # Industry and categories
    industry: Optional[str] = None
    niches: list[NicheCategory] = field(default_factory=list)

    # Target influencer criteria
    min_followers: int = 0
    max_followers: int = 10000000
    preferred_platforms: list[str] = field(default_factory=list)
    min_engagement_rate: float = 0.0

    # Target demographics
    target_age_range: tuple[int, int] = (18, 65)
    target_genders: list[str] = field(default_factory=lambda: ["all"])
    target_locations: list[str] = field(default_factory=list)

    # Budget
    min_budget: float = 0.0
    max_budget: float = 0.0
    currency: str = "USD"

    # Deal preferences
    preferred_deal_types: list[DealType] = field(default_factory=list)
    requires_exclusivity: bool = False
    content_rights: str = "limited"  # 'limited', 'full', 'perpetual'

    # Compliance
    requires_ftc_disclosure: bool = True
    banned_topics: list[str] = field(default_factory=list)

    # Metadata
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BrandOpportunity:
    """A brand deal opportunity."""
    opportunity_id: str = field(default_factory=lambda: str(uuid4()))
    brand: Optional[BrandProfile] = None
    brand_id: Optional[str] = None
    brand_name: str = ""

    # Opportunity details
    title: str = ""
    description: str = ""
    deal_type: DealType = DealType.SPONSORED_POST

    # Requirements
    deliverables: list[str] = field(default_factory=list)  # e.g., "1 Instagram post", "2 Stories"
    deadline: Optional[datetime] = None
    content_guidelines: Optional[str] = None

    # Compensation
    compensation_type: str = "fixed"  # 'fixed', 'per_post', 'per_click', 'revenue_share'
    compensation_amount: float = 0.0
    currency: str = "USD"
    includes_free_product: bool = False
    product_value: float = 0.0

    # Target criteria
    target_niches: list[NicheCategory] = field(default_factory=list)
    target_platforms: list[str] = field(default_factory=list)
    min_followers: int = 0
    max_followers: int = 10000000
    min_engagement_rate: float = 0.0

    # Status
    status: DealStatus = DealStatus.DISCOVERED
    spots_available: int = 1
    spots_filled: int = 0

    # Source
    source: str = ""  # 'direct', 'marketplace', 'agency', 'scraped'
    source_url: Optional[str] = None

    # Timing
    application_deadline: Optional[datetime] = None
    campaign_start: Optional[datetime] = None
    campaign_end: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MatchScore:
    """Detailed match score between influencer and brand opportunity."""
    overall_score: float = 0.0  # 0-100

    # Component scores
    niche_score: float = 0.0
    audience_score: float = 0.0
    engagement_score: float = 0.0
    reach_score: float = 0.0
    platform_score: float = 0.0
    rate_score: float = 0.0  # How well compensation matches expected rates

    # Match details
    matching_niches: list[str] = field(default_factory=list)
    matching_platforms: list[str] = field(default_factory=list)

    # Recommendations
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    # Estimated value
    estimated_fair_rate: float = 0.0
    rate_comparison: str = ""  # 'below_market', 'at_market', 'above_market'


@dataclass
class InfluencerProfile:
    """Influencer profile for matching."""
    user_id: str
    display_name: str

    # Audience metrics
    total_followers: int = 0
    platform_followers: dict[str, int] = field(default_factory=dict)
    engagement_rate: float = 0.0
    avg_views: int = 0

    # Demographics
    audience_age_range: tuple[int, int] = (18, 34)
    audience_gender_split: dict[str, float] = field(default_factory=dict)
    audience_locations: dict[str, float] = field(default_factory=dict)

    # Content
    niches: list[NicheCategory] = field(default_factory=list)
    content_style: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)

    # Rates
    rate_per_post: dict[str, float] = field(default_factory=dict)  # platform -> rate
    minimum_budget: float = 0.0

    # Preferences
    preferred_deal_types: list[DealType] = field(default_factory=list)
    blacklisted_industries: list[str] = field(default_factory=list)
    requires_product_alignment: bool = True

    # History
    completed_deals: int = 0
    avg_deal_rating: float = 0.0


class BrandDealMatcher:
    """
    Matches influencers with brand partnership opportunities.

    Features:
    - Multi-factor matching algorithm
    - Fair rate estimation
    - Opportunity discovery
    - Application tracking
    - Performance analytics
    """

    # Rate calculation factors (per 1000 followers)
    BASE_RATES = {
        "instagram": {"post": 10, "story": 3, "reel": 15},
        "tiktok": {"video": 12},
        "youtube": {"video": 20, "short": 8},
        "twitter": {"tweet": 5, "thread": 10},
        "linkedin": {"post": 15},
    }

    # Engagement rate multipliers
    ENGAGEMENT_MULTIPLIERS = {
        (0, 1): 0.5,    # <1% engagement
        (1, 3): 1.0,    # 1-3% engagement
        (3, 6): 1.5,    # 3-6% engagement
        (6, 10): 2.0,   # 6-10% engagement
        (10, 100): 2.5, # >10% engagement
    }

    def __init__(
        self,
        opportunity_sources: Optional[list] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize brand deal matcher.

        Args:
            opportunity_sources: List of opportunity source integrations
            llm_client: LLM for content analysis
        """
        self.opportunity_sources = opportunity_sources or []
        self.llm_client = llm_client
        self._opportunities_cache: dict[str, BrandOpportunity] = {}

    async def find_opportunities(
        self,
        influencer: InfluencerProfile,
        limit: int = 20,
        min_match_score: float = 50.0,
        deal_types: Optional[list[DealType]] = None,
    ) -> list[tuple[BrandOpportunity, MatchScore]]:
        """
        Find brand deal opportunities matching an influencer's profile.

        Args:
            influencer: Influencer profile
            limit: Maximum opportunities to return
            min_match_score: Minimum match score threshold
            deal_types: Filter by deal types

        Returns:
            List of (opportunity, match_score) tuples
        """
        # Get all available opportunities
        opportunities = await self._get_available_opportunities()

        # Filter by deal type if specified
        if deal_types:
            opportunities = [
                opp for opp in opportunities
                if opp.deal_type in deal_types
            ]

        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            score = self.calculate_match_score(influencer, opp)
            if score.overall_score >= min_match_score:
                scored_opportunities.append((opp, score))

        # Sort by score
        scored_opportunities.sort(key=lambda x: x[1].overall_score, reverse=True)

        return scored_opportunities[:limit]

    def calculate_match_score(
        self,
        influencer: InfluencerProfile,
        opportunity: BrandOpportunity,
    ) -> MatchScore:
        """
        Calculate detailed match score between influencer and opportunity.

        Args:
            influencer: Influencer profile
            opportunity: Brand opportunity

        Returns:
            Detailed match score
        """
        score = MatchScore()

        # 1. Niche alignment (30% weight)
        matching_niches = set(influencer.niches) & set(opportunity.target_niches)
        if opportunity.target_niches:
            score.niche_score = len(matching_niches) / len(opportunity.target_niches) * 100
        else:
            score.niche_score = 80  # No specific niches required
        score.matching_niches = [n.value for n in matching_niches]

        # 2. Platform alignment (20% weight)
        matching_platforms = set(influencer.platforms) & set(opportunity.target_platforms)
        if opportunity.target_platforms:
            score.platform_score = len(matching_platforms) / len(opportunity.target_platforms) * 100
        else:
            score.platform_score = 80
        score.matching_platforms = list(matching_platforms)

        # 3. Follower count alignment (15% weight)
        if opportunity.min_followers <= influencer.total_followers <= opportunity.max_followers:
            score.reach_score = 100
        elif influencer.total_followers < opportunity.min_followers:
            ratio = influencer.total_followers / opportunity.min_followers
            score.reach_score = ratio * 50
        else:  # Above max
            ratio = opportunity.max_followers / influencer.total_followers
            score.reach_score = ratio * 70

        # 4. Engagement rate alignment (20% weight)
        if influencer.engagement_rate >= opportunity.min_engagement_rate:
            # Bonus for higher engagement
            excess = influencer.engagement_rate - opportunity.min_engagement_rate
            score.engagement_score = min(100, 80 + excess * 5)
        else:
            ratio = influencer.engagement_rate / max(opportunity.min_engagement_rate, 0.01)
            score.engagement_score = ratio * 50

        # 5. Compensation alignment (15% weight)
        estimated_rate = self.estimate_fair_rate(influencer, opportunity)
        score.estimated_fair_rate = estimated_rate

        if opportunity.compensation_amount > 0:
            rate_ratio = opportunity.compensation_amount / estimated_rate
            if 0.8 <= rate_ratio <= 1.2:
                score.rate_score = 100
                score.rate_comparison = "at_market"
            elif rate_ratio > 1.2:
                score.rate_score = 100
                score.rate_comparison = "above_market"
            else:
                score.rate_score = rate_ratio * 80
                score.rate_comparison = "below_market"
        else:
            score.rate_score = 50  # Unknown compensation

        # Calculate overall score (weighted average)
        weights = {
            "niche": 0.30,
            "platform": 0.20,
            "reach": 0.15,
            "engagement": 0.20,
            "rate": 0.15,
        }

        score.overall_score = (
            score.niche_score * weights["niche"] +
            score.platform_score * weights["platform"] +
            score.reach_score * weights["reach"] +
            score.engagement_score * weights["engagement"] +
            score.rate_score * weights["rate"]
        )

        # Generate insights
        score.strengths = self._identify_strengths(score, influencer, opportunity)
        score.weaknesses = self._identify_weaknesses(score, influencer, opportunity)
        score.suggestions = self._generate_suggestions(score, influencer, opportunity)

        return score

    def estimate_fair_rate(
        self,
        influencer: InfluencerProfile,
        opportunity: BrandOpportunity,
    ) -> float:
        """
        Estimate fair compensation for an opportunity.

        Args:
            influencer: Influencer profile
            opportunity: Brand opportunity

        Returns:
            Estimated fair rate in USD
        """
        total_rate = 0.0

        # Parse deliverables
        for deliverable in opportunity.deliverables:
            deliverable_lower = deliverable.lower()

            # Determine platform and content type
            for platform in opportunity.target_platforms or influencer.platforms:
                platform_rates = self.BASE_RATES.get(platform, {})

                # Determine content type from deliverable
                if "post" in deliverable_lower:
                    base_rate = platform_rates.get("post", 10)
                elif "story" in deliverable_lower or "stories" in deliverable_lower:
                    base_rate = platform_rates.get("story", 3)
                elif "reel" in deliverable_lower:
                    base_rate = platform_rates.get("reel", 15)
                elif "video" in deliverable_lower:
                    base_rate = platform_rates.get("video", 15)
                elif "short" in deliverable_lower:
                    base_rate = platform_rates.get("short", 8)
                else:
                    base_rate = 10  # Default

                # Calculate based on followers
                followers = influencer.platform_followers.get(
                    platform, influencer.total_followers
                )
                rate = (followers / 1000) * base_rate

                # Apply engagement multiplier
                eng_rate = influencer.engagement_rate
                for (low, high), multiplier in self.ENGAGEMENT_MULTIPLIERS.items():
                    if low <= eng_rate < high:
                        rate *= multiplier
                        break

                # Extract quantity from deliverable
                import re
                quantity_match = re.search(r'(\d+)', deliverable)
                quantity = int(quantity_match.group(1)) if quantity_match else 1

                total_rate += rate * quantity
                break  # Only count once per deliverable

        # Apply deal type modifier
        deal_modifiers = {
            DealType.SPONSORED_POST: 1.0,
            DealType.AFFILIATE: 0.5,  # Lower upfront, ongoing commission
            DealType.AMBASSADOR: 1.5,  # Premium for long-term commitment
            DealType.PRODUCT_REVIEW: 0.8,
            DealType.GIVEAWAY: 0.7,
            DealType.UGC: 0.6,
            DealType.LONG_TERM: 0.9,  # Volume discount
        }
        total_rate *= deal_modifiers.get(opportunity.deal_type, 1.0)

        # Add product value if included
        if opportunity.includes_free_product:
            total_rate += opportunity.product_value * 0.3  # Partial value

        return round(total_rate, 2)

    async def _get_available_opportunities(self) -> list[BrandOpportunity]:
        """Get available opportunities from all sources."""
        opportunities = list(self._opportunities_cache.values())

        # In production, this would query databases, APIs, etc.
        # For now, return cached + mock opportunities
        if not opportunities:
            opportunities = self._generate_mock_opportunities()

        # Filter out filled/expired opportunities
        now = datetime.utcnow()
        active = [
            opp for opp in opportunities
            if opp.status in [DealStatus.DISCOVERED, DealStatus.MATCHED]
            and (not opp.application_deadline or opp.application_deadline > now)
            and opp.spots_filled < opp.spots_available
        ]

        return active

    def _generate_mock_opportunities(self) -> list[BrandOpportunity]:
        """Generate mock opportunities for demo."""
        return [
            BrandOpportunity(
                brand_name="FitGear Pro",
                title="Summer Fitness Campaign",
                description="Looking for fitness influencers to promote our new workout gear collection",
                deal_type=DealType.SPONSORED_POST,
                deliverables=["2 Instagram posts", "4 Instagram stories", "1 TikTok video"],
                compensation_amount=1500,
                includes_free_product=True,
                product_value=300,
                target_niches=[NicheCategory.FITNESS, NicheCategory.LIFESTYLE],
                target_platforms=["instagram", "tiktok"],
                min_followers=10000,
                max_followers=500000,
                min_engagement_rate=3.0,
                spots_available=5,
            ),
            BrandOpportunity(
                brand_name="TechStart",
                title="App Review Partnership",
                description="Review our productivity app and share with your audience",
                deal_type=DealType.PRODUCT_REVIEW,
                deliverables=["1 YouTube video (5-10 min)"],
                compensation_amount=2000,
                target_niches=[NicheCategory.TECH, NicheCategory.BUSINESS],
                target_platforms=["youtube"],
                min_followers=50000,
                max_followers=1000000,
                min_engagement_rate=2.0,
                spots_available=3,
            ),
            BrandOpportunity(
                brand_name="GlowCosmetics",
                title="Beauty Box Ambassador Program",
                description="6-month ambassador program with monthly product boxes",
                deal_type=DealType.AMBASSADOR,
                deliverables=["2 Instagram reels/month", "4 Stories/month"],
                compensation_amount=500,  # Per month
                includes_free_product=True,
                product_value=150,
                target_niches=[NicheCategory.BEAUTY, NicheCategory.FASHION],
                target_platforms=["instagram", "tiktok"],
                min_followers=5000,
                max_followers=100000,
                min_engagement_rate=4.0,
                spots_available=10,
            ),
            BrandOpportunity(
                brand_name="HomeChef",
                title="Recipe Creation Campaign",
                description="Create recipes featuring our meal kits",
                deal_type=DealType.SPONSORED_POST,
                deliverables=["3 TikTok videos", "1 Instagram post"],
                compensation_amount=800,
                includes_free_product=True,
                product_value=200,
                target_niches=[NicheCategory.FOOD, NicheCategory.LIFESTYLE],
                target_platforms=["tiktok", "instagram"],
                min_followers=5000,
                max_followers=200000,
                min_engagement_rate=3.5,
                spots_available=8,
            ),
            BrandOpportunity(
                brand_name="TravelEase",
                title="Travel App Promotion",
                description="Share your travel experiences using our booking app",
                deal_type=DealType.AFFILIATE,
                deliverables=["1 Instagram reel", "Link in bio for 1 month"],
                compensation_amount=300,  # Base + 10% commission
                target_niches=[NicheCategory.TRAVEL, NicheCategory.LIFESTYLE],
                target_platforms=["instagram", "youtube"],
                min_followers=20000,
                max_followers=500000,
                min_engagement_rate=2.5,
                spots_available=20,
            ),
        ]

    def _identify_strengths(
        self,
        score: MatchScore,
        influencer: InfluencerProfile,
        opportunity: BrandOpportunity,
    ) -> list[str]:
        """Identify matching strengths."""
        strengths = []

        if score.niche_score >= 80:
            strengths.append(f"Strong niche alignment: {', '.join(score.matching_niches)}")

        if score.engagement_score >= 80:
            strengths.append(f"High engagement rate ({influencer.engagement_rate:.1f}%)")

        if score.rate_comparison == "above_market":
            strengths.append("Compensation above market rate")

        if influencer.completed_deals > 10:
            strengths.append(f"Experienced ({influencer.completed_deals} completed deals)")

        return strengths

    def _identify_weaknesses(
        self,
        score: MatchScore,
        influencer: InfluencerProfile,
        opportunity: BrandOpportunity,
    ) -> list[str]:
        """Identify potential weaknesses."""
        weaknesses = []

        if score.reach_score < 60:
            if influencer.total_followers < opportunity.min_followers:
                weaknesses.append("Below minimum follower requirement")
            else:
                weaknesses.append("Above maximum follower target")

        if score.engagement_score < 60:
            weaknesses.append(f"Engagement rate below requirement ({influencer.engagement_rate:.1f}%)")

        if score.rate_comparison == "below_market":
            weaknesses.append("Compensation below market rate")

        if not score.matching_platforms:
            weaknesses.append("No matching platforms")

        return weaknesses

    def _generate_suggestions(
        self,
        score: MatchScore,
        influencer: InfluencerProfile,
        opportunity: BrandOpportunity,
    ) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if score.niche_score < 80 and score.matching_niches:
            suggestions.append(
                f"Highlight your {score.matching_niches[0]} content in your application"
            )

        if score.rate_comparison == "below_market":
            suggestions.append(
                f"Consider negotiating - fair rate estimate: ${score.estimated_fair_rate:.0f}"
            )

        if score.platform_score < 80 and score.matching_platforms:
            primary_platform = score.matching_platforms[0]
            suggestions.append(
                f"Focus your pitch on your {primary_platform} presence"
            )

        if opportunity.includes_free_product:
            suggestions.append(
                f"Factor in product value (${opportunity.product_value}) when evaluating total compensation"
            )

        return suggestions

    async def track_application(
        self,
        user_id: str,
        opportunity_id: str,
        status: DealStatus,
        notes: Optional[str] = None,
    ) -> dict:
        """Track application status for an opportunity."""
        # In production, this would update database
        return {
            "user_id": user_id,
            "opportunity_id": opportunity_id,
            "status": status.value,
            "notes": notes,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def get_deal_history(
        self,
        user_id: str,
        status: Optional[DealStatus] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get user's brand deal history."""
        # Mock data for demo
        return [
            {
                "opportunity_id": "deal_1",
                "brand_name": "FitGear Pro",
                "status": DealStatus.COMPLETED.value,
                "compensation": 1500,
                "completed_at": "2024-06-15",
            },
            {
                "opportunity_id": "deal_2",
                "brand_name": "TechStart",
                "status": DealStatus.IN_PROGRESS.value,
                "compensation": 2000,
                "started_at": "2024-07-01",
            },
        ]

    async def get_earnings_summary(
        self,
        user_id: str,
        period_days: int = 90,
    ) -> dict:
        """Get earnings summary for user."""
        # Mock data for demo
        return {
            "total_earnings": 5500,
            "completed_deals": 4,
            "avg_deal_value": 1375,
            "pending_payments": 2000,
            "period_days": period_days,
            "by_type": {
                DealType.SPONSORED_POST.value: 3000,
                DealType.PRODUCT_REVIEW.value: 2000,
                DealType.AFFILIATE.value: 500,
            },
        }
