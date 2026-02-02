"""
Revenue Schemas

Schema definitions for revenue intelligence: ROI projections,
pricing recommendations, and payout aggregation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RevenueSource(str, Enum):
    """Sources of creator revenue."""
    BRAND_DEAL = "brand_deal"
    AFFILIATE = "affiliate"
    SPONSORSHIP = "sponsorship"
    AD_REVENUE = "ad_revenue"
    SUBSCRIPTION = "subscription"
    MERCHANDISE = "merchandise"
    TIPS = "tips"
    COURSE = "course"
    OTHER = "other"


class Platform(str, Enum):
    """Content platforms."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class ConfidenceInterval(BaseModel):
    """Confidence interval for projections."""
    lower: float
    estimate: float
    upper: float
    confidence_level: float = 0.80  # 80% confidence


class ROIProjection(BaseModel):
    """
    ROI projection with confidence intervals.
    
    Shows expected return with uncertainty bands.
    """
    projection_id: UUID
    
    # Input scenario
    scenario_name: str
    scenario_type: str  # content, collaboration, monetization
    time_horizon_days: int = 90
    
    # Investment
    investment: ConfidenceInterval
    investment_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    # Projected return
    projected_revenue: ConfidenceInterval
    revenue_breakdown: Dict[str, ConfidenceInterval] = Field(default_factory=dict)
    
    # ROI calculation
    roi_percent: ConfidenceInterval
    payback_period_days: Optional[ConfidenceInterval] = None
    
    # Evidence
    assumptions: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    comparable_cases: int = 0
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MarketBenchmark(BaseModel):
    """Industry benchmark data for pricing."""
    metric_name: str
    
    # Distribution
    p25: float  # 25th percentile
    median: float
    p75: float  # 75th percentile
    
    # Context
    sample_size: int
    niche: str
    tier: str  # micro, mid, macro, mega
    data_period: str  # e.g., "Q4 2025"
    
    # Source
    source: str
    last_updated: datetime


class PricingRecommendation(BaseModel):
    """
    Rate recommendation with market benchmarks.
    
    Cites industry data for credibility.
    """
    recommendation_id: UUID
    
    # Content type
    content_type: str  # post, story, video, reel, etc.
    platform: Platform
    
    # Recommended rates
    recommended_rate: ConfidenceInterval
    rate_per_1k_followers: float
    
    # Market context
    benchmarks: List[MarketBenchmark] = Field(default_factory=list)
    your_percentile: float  # Where you fall in the market
    
    # Factors
    factors: Dict[str, float] = Field(default_factory=dict)
    # e.g., {"engagement_premium": 1.2, "niche_premium": 1.1}
    
    # Evidence
    reasoning: str
    comparable_creators: int = 0
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RevenueEntry(BaseModel):
    """A single revenue entry."""
    entry_id: UUID
    user_id: UUID
    
    # Source
    source: RevenueSource
    platform: Optional[Platform] = None
    description: str
    
    # Amount
    gross_amount: float
    net_amount: float
    currency: str = "USD"
    
    # Timing
    earned_at: datetime
    paid_at: Optional[datetime] = None
    
    # Reference
    external_id: Optional[str] = None  # Stripe, platform ID
    brand_deal_id: Optional[UUID] = None


class RevenueStream(BaseModel):
    """Aggregated revenue from a source."""
    source: RevenueSource
    platform: Optional[Platform] = None
    
    # Totals
    total_gross: float
    total_net: float
    count: int
    
    # Period
    period_start: datetime
    period_end: datetime
    
    # Trend
    growth_percent: Optional[float] = None
    previous_period_total: Optional[float] = None


class PayoutSummary(BaseModel):
    """
    Unified payout dashboard data.
    
    Aggregates all revenue streams.
    """
    user_id: UUID
    
    # Period
    period_start: datetime
    period_end: datetime
    
    # Totals
    total_gross: float
    total_net: float
    total_pending: float
    total_paid: float
    
    # By source
    by_source: List[RevenueStream] = Field(default_factory=list)
    by_platform: List[RevenueStream] = Field(default_factory=list)
    
    # Top contributors
    top_deals: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Stripe status
    stripe_connected: bool = False
    next_payout_date: Optional[datetime] = None
    next_payout_amount: Optional[float] = None


# ============== Request/Response Schemas ==============

class ProjectROIRequest(BaseModel):
    """Request to project ROI."""
    scenario_id: Optional[UUID] = None
    scenario_name: str
    scenario_type: str
    
    # Investment details
    investment_amount: float
    investment_breakdown: Optional[Dict[str, float]] = None
    
    # Projection settings
    time_horizon_days: int = 90
    confidence_level: float = 0.80


class ProjectROIResponse(BaseModel):
    """Response with ROI projection."""
    projection: ROIProjection


class PricingRequest(BaseModel):
    """Request for pricing recommendation."""
    content_type: str
    platform: Platform
    follower_count: int
    engagement_rate: float
    niche: Optional[str] = None


class PricingResponse(BaseModel):
    """Response with pricing recommendation."""
    recommendation: PricingRecommendation


class PayoutRequest(BaseModel):
    """Request for payout summary."""
    period: str = "30d"  # 7d, 30d, 90d, ytd, all


class PayoutResponse(BaseModel):
    """Response with payout summary."""
    summary: PayoutSummary
