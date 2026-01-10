"""
Brand Deal API Endpoints

REST API for brand deal matching and monetization.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class InfluencerProfileRequest(BaseModel):
    """Influencer profile for matching."""
    display_name: str
    total_followers: int = 10000
    platform_followers: dict[str, int] = Field(default_factory=dict)
    engagement_rate: float = 3.0
    niches: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    minimum_budget: float = 0.0
    blacklisted_industries: list[str] = Field(default_factory=list)


class BrandOpportunityResponse(BaseModel):
    """Brand deal opportunity response."""
    opportunity_id: str
    brand_name: str
    title: str
    description: str
    deal_type: str
    deliverables: list[str] = []
    compensation_amount: float = 0.0
    currency: str = "USD"
    includes_free_product: bool = False
    product_value: float = 0.0
    target_niches: list[str] = []
    target_platforms: list[str] = []
    min_followers: int = 0
    max_followers: int = 0
    min_engagement_rate: float = 0.0
    spots_available: int = 1
    application_deadline: Optional[datetime] = None
    campaign_start: Optional[datetime] = None
    campaign_end: Optional[datetime] = None


class MatchScoreResponse(BaseModel):
    """Match score for an opportunity."""
    overall_score: float
    niche_score: float
    platform_score: float
    reach_score: float
    engagement_score: float
    rate_score: float
    matching_niches: list[str] = []
    matching_platforms: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    estimated_fair_rate: float = 0.0
    rate_comparison: str = ""


class OpportunityWithScoreResponse(BaseModel):
    """Opportunity with match score."""
    opportunity: BrandOpportunityResponse
    match_score: MatchScoreResponse


class ApplicationRequest(BaseModel):
    """Application to a brand deal."""
    opportunity_id: str
    pitch_message: str
    portfolio_links: list[str] = Field(default_factory=list)
    proposed_rate: Optional[float] = None


class EarningsSummaryResponse(BaseModel):
    """Earnings summary response."""
    total_earnings: float
    completed_deals: int
    avg_deal_value: float
    pending_payments: float
    period_days: int
    by_type: dict[str, float] = {}


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post("/find", response_model=list[OpportunityWithScoreResponse])
async def find_opportunities(
    profile: InfluencerProfileRequest,
    min_match_score: float = Query(default=50.0, ge=0, le=100),
    deal_types: Optional[list[str]] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    """
    Find brand deal opportunities matching influencer profile.

    Returns opportunities sorted by match score.
    """
    from app.services.monetization import (
        BrandDealMatcher,
        DealType,
    )
    from app.services.monetization.brand_matcher import InfluencerProfile, NicheCategory

    matcher = BrandDealMatcher()

    # Convert to internal model
    influencer = InfluencerProfile(
        user_id="current_user",
        display_name=profile.display_name,
        total_followers=profile.total_followers,
        platform_followers=profile.platform_followers,
        engagement_rate=profile.engagement_rate,
        niches=[NicheCategory(n) for n in profile.niches if n in [e.value for e in NicheCategory]],
        platforms=profile.platforms,
        minimum_budget=profile.minimum_budget,
        blacklisted_industries=profile.blacklisted_industries,
    )

    # Convert deal types
    deal_type_filter = None
    if deal_types:
        deal_type_filter = [DealType(dt) for dt in deal_types]

    opportunities = await matcher.find_opportunities(
        influencer=influencer,
        limit=limit,
        min_match_score=min_match_score,
        deal_types=deal_type_filter,
    )

    return [
        OpportunityWithScoreResponse(
            opportunity=BrandOpportunityResponse(
                opportunity_id=opp.opportunity_id,
                brand_name=opp.brand_name,
                title=opp.title,
                description=opp.description,
                deal_type=opp.deal_type.value,
                deliverables=opp.deliverables,
                compensation_amount=opp.compensation_amount,
                currency=opp.currency,
                includes_free_product=opp.includes_free_product,
                product_value=opp.product_value,
                target_niches=[n.value for n in opp.target_niches],
                target_platforms=opp.target_platforms,
                min_followers=opp.min_followers,
                max_followers=opp.max_followers,
                min_engagement_rate=opp.min_engagement_rate,
                spots_available=opp.spots_available,
                application_deadline=opp.application_deadline,
                campaign_start=opp.campaign_start,
                campaign_end=opp.campaign_end,
            ),
            match_score=MatchScoreResponse(
                overall_score=score.overall_score,
                niche_score=score.niche_score,
                platform_score=score.platform_score,
                reach_score=score.reach_score,
                engagement_score=score.engagement_score,
                rate_score=score.rate_score,
                matching_niches=score.matching_niches,
                matching_platforms=score.matching_platforms,
                strengths=score.strengths,
                weaknesses=score.weaknesses,
                suggestions=score.suggestions,
                estimated_fair_rate=score.estimated_fair_rate,
                rate_comparison=score.rate_comparison,
            ),
        )
        for opp, score in opportunities
    ]


@router.get("/opportunities", response_model=list[BrandOpportunityResponse])
async def list_opportunities(
    platform: Optional[str] = None,
    niche: Optional[str] = None,
    min_compensation: Optional[float] = None,
    deal_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List all available brand deal opportunities.

    Filter by platform, niche, compensation, or deal type.
    """
    from app.services.monetization import BrandDealMatcher

    matcher = BrandDealMatcher()
    opportunities = matcher._generate_mock_opportunities()

    # Apply filters
    if platform:
        opportunities = [
            o for o in opportunities
            if platform in o.target_platforms
        ]

    if niche:
        opportunities = [
            o for o in opportunities
            if any(n.value == niche for n in o.target_niches)
        ]

    if min_compensation:
        opportunities = [
            o for o in opportunities
            if o.compensation_amount >= min_compensation
        ]

    if deal_type:
        opportunities = [
            o for o in opportunities
            if o.deal_type.value == deal_type
        ]

    return [
        BrandOpportunityResponse(
            opportunity_id=opp.opportunity_id,
            brand_name=opp.brand_name,
            title=opp.title,
            description=opp.description,
            deal_type=opp.deal_type.value,
            deliverables=opp.deliverables,
            compensation_amount=opp.compensation_amount,
            currency=opp.currency,
            includes_free_product=opp.includes_free_product,
            product_value=opp.product_value,
            target_niches=[n.value for n in opp.target_niches],
            target_platforms=opp.target_platforms,
            min_followers=opp.min_followers,
            max_followers=opp.max_followers,
            min_engagement_rate=opp.min_engagement_rate,
            spots_available=opp.spots_available,
        )
        for opp in opportunities[:limit]
    ]


@router.get("/opportunities/{opportunity_id}", response_model=BrandOpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
):
    """Get details of a specific brand deal opportunity."""
    from app.services.monetization import BrandDealMatcher

    matcher = BrandDealMatcher()
    opportunities = matcher._generate_mock_opportunities()

    opp = next((o for o in opportunities if o.opportunity_id == opportunity_id), None)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return BrandOpportunityResponse(
        opportunity_id=opp.opportunity_id,
        brand_name=opp.brand_name,
        title=opp.title,
        description=opp.description,
        deal_type=opp.deal_type.value,
        deliverables=opp.deliverables,
        compensation_amount=opp.compensation_amount,
        currency=opp.currency,
        includes_free_product=opp.includes_free_product,
        product_value=opp.product_value,
        target_niches=[n.value for n in opp.target_niches],
        target_platforms=opp.target_platforms,
        min_followers=opp.min_followers,
        max_followers=opp.max_followers,
        min_engagement_rate=opp.min_engagement_rate,
        spots_available=opp.spots_available,
    )


@router.post("/apply")
async def apply_to_opportunity(
    application: ApplicationRequest,
):
    """
    Apply to a brand deal opportunity.

    Submit your pitch and portfolio for consideration.
    """
    from app.services.monetization import BrandDealMatcher, DealStatus

    matcher = BrandDealMatcher()

    result = await matcher.track_application(
        user_id="current_user",
        opportunity_id=application.opportunity_id,
        status=DealStatus.APPLIED,
        notes=application.pitch_message,
    )

    return {
        "success": True,
        "application": result,
        "message": "Application submitted successfully",
    }


@router.get("/applications")
async def get_my_applications(
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """Get user's brand deal applications."""
    from app.services.monetization import BrandDealMatcher, DealStatus

    matcher = BrandDealMatcher()

    status_filter = DealStatus(status) if status else None
    history = await matcher.get_deal_history(
        user_id="current_user",
        status=status_filter,
        limit=limit,
    )

    return {"applications": history}


@router.get("/earnings", response_model=EarningsSummaryResponse)
async def get_earnings_summary(
    period_days: int = Query(default=90, ge=7, le=365),
):
    """Get earnings summary from brand deals."""
    from app.services.monetization import BrandDealMatcher

    matcher = BrandDealMatcher()

    summary = await matcher.get_earnings_summary(
        user_id="current_user",
        period_days=period_days,
    )

    return EarningsSummaryResponse(**summary)


@router.post("/estimate-rate")
async def estimate_fair_rate(
    profile: InfluencerProfileRequest,
    deliverables: list[str],
    platforms: list[str],
    deal_type: str = "sponsored_post",
):
    """
    Estimate fair compensation rate for deliverables.

    Based on follower count, engagement, and market rates.
    """
    from app.services.monetization import BrandDealMatcher, DealType
    from app.services.monetization.brand_matcher import (
        BrandOpportunity,
        InfluencerProfile,
        NicheCategory,
    )

    matcher = BrandDealMatcher()

    influencer = InfluencerProfile(
        user_id="current_user",
        display_name=profile.display_name,
        total_followers=profile.total_followers,
        platform_followers=profile.platform_followers,
        engagement_rate=profile.engagement_rate,
        platforms=profile.platforms,
    )

    opportunity = BrandOpportunity(
        deliverables=deliverables,
        target_platforms=platforms,
        deal_type=DealType(deal_type),
    )

    estimated_rate = matcher.estimate_fair_rate(influencer, opportunity)

    return {
        "estimated_rate": estimated_rate,
        "currency": "USD",
        "breakdown": {
            "base_calculation": "Based on follower count and platform rates",
            "engagement_multiplier": f"{profile.engagement_rate}% engagement rate applied",
            "deal_type_modifier": f"{deal_type} rate adjustment",
        },
        "range": {
            "low": round(estimated_rate * 0.8, 2),
            "fair": estimated_rate,
            "high": round(estimated_rate * 1.3, 2),
        },
    }


@router.get("/deal-types")
async def get_deal_types():
    """Get list of available deal types."""
    from app.services.monetization import DealType

    return {
        "deal_types": [
            {
                "id": dt.value,
                "name": dt.value.replace("_", " ").title(),
                "description": _get_deal_type_description(dt),
            }
            for dt in DealType
        ]
    }


def _get_deal_type_description(deal_type) -> str:
    """Get description for deal type."""
    from app.services.monetization import DealType

    descriptions = {
        DealType.SPONSORED_POST: "One-time paid post featuring the brand",
        DealType.AFFILIATE: "Commission-based promotion with tracking link",
        DealType.AMBASSADOR: "Long-term partnership as brand representative",
        DealType.PRODUCT_REVIEW: "Review and share opinions about a product",
        DealType.GIVEAWAY: "Host a giveaway for the brand",
        DealType.EVENT: "Attend or promote a brand event",
        DealType.LONG_TERM: "Extended multi-post campaign",
        DealType.UGC: "Create content for brand's use",
    }
    return descriptions.get(deal_type, "")
