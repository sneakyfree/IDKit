"""
Revenue Intelligence API Endpoints

REST API for ROI projections, pricing, brand deals, and payouts.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.revenue import (
    PayoutRequest,
    PayoutResponse,
    Platform,
    PricingRequest,
    PricingResponse,
    ProjectROIRequest,
    ProjectROIResponse,
)
from app.schemas.brand_deals import (
    AddDeliverableRequest,
    AddNoteRequest,
    BrandDeal,
    CreateDealRequest,
    CreateDealResponse,
    DealListResponse,
    DealStage,
    DeliverableType,
    PipelineResponse,
    UpdateStageRequest,
)
from app.services.roi_engine import ROIEngine
from app.services.pricing_engine import PricingEngine
from app.services.brand_deal_service import BrandDealService
from app.services.payout_service import PayoutService

router = APIRouter(prefix="/revenue", tags=["Revenue Intelligence"])


# ============== ROI Endpoints ==============

@router.post("/roi/project", response_model=ProjectROIResponse)
async def project_roi(
    request: ProjectROIRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Project ROI for a scenario with confidence intervals.
    
    Returns expected return with 80% confidence bands.
    """
    engine = ROIEngine()
    
    projection = engine.project_roi(
        scenario_name=request.scenario_name,
        scenario_type=request.scenario_type,
        investment_amount=request.investment_amount,
        investment_breakdown=request.investment_breakdown,
        time_horizon_days=request.time_horizon_days,
        confidence_level=request.confidence_level,
    )

    return ProjectROIResponse(projection=projection)


@router.post("/roi/compare")
async def compare_scenarios(
    scenarios: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
):
    """Compare multiple scenarios side-by-side."""
    engine = ROIEngine()
    result = engine.compare_scenarios(scenarios)
    return result


# ============== Pricing Endpoints ==============

@router.post("/pricing/recommend", response_model=PricingResponse)
async def recommend_pricing(
    request: PricingRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get pricing recommendation based on market benchmarks.
    
    Cites industry data sources for credibility.
    """
    engine = PricingEngine()
    
    recommendation = engine.recommend_rate(
        content_type=request.content_type,
        platform=request.platform,
        follower_count=request.follower_count,
        engagement_rate=request.engagement_rate,
        niche=request.niche,
    )

    return PricingResponse(recommendation=recommendation)


@router.get("/pricing/benchmarks")
async def get_benchmarks(
    platform: Platform,
    content_type: str,
    tier: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get raw market benchmark data."""
    engine = PricingEngine()
    benchmarks = engine.get_market_benchmarks(platform, content_type, tier)
    return {"benchmarks": [b.model_dump() for b in benchmarks]}


@router.post("/pricing/package")
async def calculate_package_rate(
    deliverables: List[Dict[str, Any]],
    follower_count: int,
    engagement_rate: float,
    niche: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Calculate rate for a package of deliverables."""
    engine = PricingEngine()
    result = engine.calculate_package_rate(
        deliverables=deliverables,
        follower_count=follower_count,
        engagement_rate=engagement_rate,
        niche=niche,
    )
    return result


# ============== Brand Deal Endpoints ==============

@router.post("/deals", response_model=CreateDealResponse)
async def create_deal(
    request: CreateDealRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new brand deal."""
    service = BrandDealService(db)
    
    deal = await service.create_deal(
        user_id=current_user.id,
        brand_name=request.brand_name,
        title=request.title,
        description=request.description,
        deal_type=request.deal_type,
        deal_value=request.deal_value,
        currency=request.currency,
        expected_close_date=request.expected_close_date,
        contacts=request.contacts,
    )
    
    await db.commit()
    return CreateDealResponse(deal=deal)


@router.get("/deals", response_model=DealListResponse)
async def list_deals(
    stage: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all brand deals."""
    service = BrandDealService(db)
    
    stage_filter = DealStage(stage) if stage else None
    deals = await service.get_deals_for_user(
        user_id=current_user.id,
        stage=stage_filter,
        limit=limit,
    )

    return DealListResponse(
        deals=deals,
        total_count=len(deals),
    )


@router.get("/deals/pipeline", response_model=PipelineResponse)
async def get_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get deal pipeline with metrics."""
    service = BrandDealService(db)
    result = await service.get_pipeline(current_user.id)
    
    return PipelineResponse(
        metrics=result["metrics"],
        deals_by_stage=result["deals_by_stage"],
    )


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific brand deal."""
    service = BrandDealService(db)
    deal = await service.get_deal(deal_id, current_user.id)
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    return {"deal": deal}


@router.post("/deals/{deal_id}/stage")
async def update_deal_stage(
    deal_id: UUID,
    request: UpdateStageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update deal pipeline stage."""
    service = BrandDealService(db)
    
    try:
        deal = await service.update_stage(
            deal_id=deal_id,
            user_id=current_user.id,
            new_stage=request.new_stage,
            note=request.note,
        )
        await db.commit()
        return {"deal": deal}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/deals/{deal_id}/deliverables")
async def add_deliverable(
    deal_id: UUID,
    request: AddDeliverableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a deliverable to a deal."""
    service = BrandDealService(db)
    
    try:
        deal = await service.add_deliverable(
            deal_id=deal_id,
            user_id=current_user.id,
            deliverable_type=request.type,
            description=request.description,
            due_date=request.due_date,
            requirements=request.requirements,
        )
        await db.commit()
        return {"deal": deal}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/deals/{deal_id}/notes")
async def add_note(
    deal_id: UUID,
    request: AddNoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a negotiation note to a deal."""
    service = BrandDealService(db)
    
    try:
        deal = await service.add_note(
            deal_id=deal_id,
            user_id=current_user.id,
            content=request.content,
        )
        await db.commit()
        return {"deal": deal}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/deals/templates")
async def get_contract_templates(
    deal_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get available contract templates."""
    from app.schemas.brand_deals import DealType
    
    service = BrandDealService(db)
    type_filter = DealType(deal_type) if deal_type else None
    templates = await service.get_contract_templates(type_filter)
    
    return {"templates": [t.model_dump() for t in templates]}


# ============== Payout Endpoints ==============

@router.get("/payouts", response_model=PayoutResponse)
async def get_payout_summary(
    period: str = "30d",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get unified payout dashboard.
    
    Aggregates all revenue streams across platforms.
    """
    service = PayoutService(db)
    summary = await service.get_payout_summary(current_user.id, period)
    return PayoutResponse(summary=summary)


@router.get("/payouts/history")
async def get_payout_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payout transaction history."""
    service = PayoutService(db)
    history = await service.get_payout_history(current_user.id, limit)
    return {"history": history}


@router.post("/payouts/process")
async def process_payout(
    amount: float,
    currency: str = "USD",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process payout to creator via Stripe Connect."""
    service = PayoutService(db)
    result = await service.process_payout(current_user.id, amount, currency)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Payout failed"),
        )
    
    await db.commit()
    return result


@router.post("/payouts/connect")
async def connect_stripe(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Stripe Connect onboarding URL."""
    service = PayoutService(db)
    result = await service.connect_stripe_account(current_user.id)
    return result
