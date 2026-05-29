"""
ROI Calculator API

REST API endpoints for calculating and viewing creator ROI metrics.
"""

import logging
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.roi.service import ROIService
from app.schemas.roi import (
    ROIReportResponse,
    ROICalculationRequest,
    ROISummaryResponse,
    CostEntryCreate,
    CostEntryResponse,
    CostEntryListResponse,
    ROIProjectionResponse,
    ProjectionDataPoint,
    RevenueBreakdown,
    CostBreakdown,
    ROIMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _format_report_response(report_data: dict) -> ROIReportResponse:
    """Format raw report data into response schema."""
    return ROIReportResponse(
        id=report_data.get("id", ""),
        period_start=report_data["period_start"],
        period_end=report_data["period_end"],
        period_type=report_data["period_type"],
        revenue=RevenueBreakdown(**report_data["revenue"]),
        costs=CostBreakdown(**report_data["costs"]),
        metrics=ROIMetrics(**report_data["metrics"]),
        total_views=report_data["engagement"]["total_views"],
        total_engagements=report_data["engagement"]["total_engagements"],
        new_followers=report_data["engagement"]["new_followers"],
        content_pieces=report_data["engagement"]["content_pieces"],
        created_at=report_data.get("created_at", report_data["period_end"]),
    )


@router.post("/calculate", response_model=ROIReportResponse)
async def calculate_roi(
    request: ROICalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate ROI for a specific time period.
    
    Aggregates revenue and costs to compute ROI metrics.
    """
    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    roi_service = ROIService(db)

    try:
        report_data = await roi_service.calculate_roi(
            user_id=current_user.id,
            start_date=request.start_date,
            end_date=request.end_date,
            save_report=True,
        )
    except Exception as e:
        logger.error(f"Failed to calculate ROI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate ROI",
        )

    return _format_report_response(report_data)


@router.get("/summary", response_model=ROISummaryResponse)
async def get_roi_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get ROI summary comparing current and previous period.
    
    Returns current month's metrics vs previous month.
    """
    roi_service = ROIService(db)

    today = date.today()
    current_start = today.replace(day=1)
    
    # Previous month - subtract one day from current month start to get prev month end
    from datetime import timedelta
    prev_end = current_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)

    # Calculate current period
    try:
        current_data = await roi_service.calculate_roi(
            user_id=current_user.id,
            start_date=current_start,
            end_date=today,
            save_report=False,
        )
        current_report = _format_report_response(current_data)
    except Exception as e:
        logger.error(f"Failed to calculate current period: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate current period ROI",
        )

    # Calculate previous period
    try:
        prev_data = await roi_service.calculate_roi(
            user_id=current_user.id,
            start_date=prev_start,
            end_date=prev_end,
            save_report=False,
        )
        prev_report = _format_report_response(prev_data)
    except Exception:
        prev_report = None

    # Calculate changes
    revenue_change = 0.0
    profit_change = 0.0
    roi_change = 0.0

    if prev_report and prev_report.revenue.total > 0:
        revenue_change = (
            (current_report.revenue.total - prev_report.revenue.total)
            / prev_report.revenue.total * 100
        )
    if prev_report and prev_report.metrics.net_profit_cents != 0:
        profit_change = (
            (current_report.metrics.net_profit_cents - prev_report.metrics.net_profit_cents)
            / abs(prev_report.metrics.net_profit_cents) * 100
        )
    if prev_report and prev_report.metrics.roi_percentage != 0:
        roi_change = (
            current_report.metrics.roi_percentage - prev_report.metrics.roi_percentage
        )

    return ROISummaryResponse(
        current_period=current_report,
        previous_period=prev_report,
        revenue_change_percent=round(revenue_change, 2),
        profit_change_percent=round(profit_change, 2),
        roi_change_percent=round(roi_change, 2),
    )


@router.get("/history", response_model=List[ROIReportResponse])
async def get_roi_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=12, le=24),
):
    """Get historical ROI reports."""
    roi_service = ROIService(db)

    reports = await roi_service.get_historical_reports(
        user_id=current_user.id,
        limit=limit,
    )

    # Convert model instances to response format
    responses = []
    for report in reports:
        responses.append(ROIReportResponse(
            id=report.id,
            period_start=report.period_start,
            period_end=report.period_end,
            period_type=report.period_type,
            revenue=RevenueBreakdown(
                brand_deals=report.brand_deal_revenue_cents,
                affiliate=report.affiliate_revenue_cents,
                subscriptions=report.subscription_revenue_cents,
                royalties=report.royalty_revenue_cents,
                other=report.other_revenue_cents,
                total=report.total_revenue_cents,
            ),
            costs=CostBreakdown(
                platform_fees=report.platform_fees_cents,
                content_creation=report.content_creation_costs_cents,
                advertising=report.advertising_costs_cents,
                software=report.software_costs_cents,
                other=report.other_costs_cents,
                total=report.total_costs_cents,
            ),
            metrics=ROIMetrics(
                net_profit_cents=report.net_profit_cents,
                roi_percentage=report.roi_percentage,
                profit_margin=report.profit_margin,
                revenue_per_content=report.revenue_per_content,
                revenue_per_view=report.revenue_per_view,
                revenue_per_follower=report.revenue_per_follower,
                engagement_rate=report.engagement_rate,
            ),
            total_views=report.total_views,
            total_engagements=report.total_engagements,
            new_followers=report.new_followers,
            content_pieces=report.content_pieces,
            created_at=report.created_at,
        ))

    return responses


@router.get("/projections", response_model=ROIProjectionResponse)
async def get_roi_projections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    months: int = Query(default=6, ge=1, le=12),
):
    """Get ROI projections for future periods."""
    roi_service = ROIService(db)

    projections_data = await roi_service.generate_projections(
        user_id=current_user.id,
        months_ahead=months,
    )

    if not projections_data:
        return ROIProjectionResponse(
            projections=[],
            average_monthly_revenue=0,
            average_monthly_costs=0,
            trend="stable",
            confidence_score=0.0,
        )

    projections = [
        ProjectionDataPoint(**p) for p in projections_data
    ]

    avg_revenue = sum(p.projected_revenue_cents for p in projections) // len(projections)
    avg_costs = sum(p.projected_costs_cents for p in projections) // len(projections)
    avg_confidence = sum(p.confidence for p in projections) / len(projections)

    return ROIProjectionResponse(
        projections=projections,
        average_monthly_revenue=avg_revenue,
        average_monthly_costs=avg_costs,
        trend="stable",  # Would be calculated from trend analysis
        confidence_score=round(avg_confidence, 2),
    )


# ============== Cost Entries ==============

@router.post("/costs", response_model=CostEntryResponse)
async def add_cost_entry(
    request: CostEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a cost entry for ROI tracking."""
    roi_service = ROIService(db)

    try:
        entry = await roi_service.add_cost_entry(
            user_id=current_user.id,
            amount_cents=request.amount_cents,
            category=request.category.value,
            expense_date=request.expense_date,
            description=request.description,
            is_recurring=request.is_recurring,
            recurrence_period=request.recurrence_period,
        )
    except Exception as e:
        logger.error(f"Failed to add cost entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add cost entry",
        )

    return CostEntryResponse(
        id=entry.id,
        amount_cents=entry.amount_cents,
        currency=entry.currency,
        category=entry.category,
        description=entry.description,
        expense_date=entry.expense_date,
        is_recurring=bool(entry.is_recurring),
        recurrence_period=entry.recurrence_period,
        created_at=entry.created_at,
    )


@router.get("/costs", response_model=CostEntryListResponse)
async def get_cost_entries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
):
    """Get cost entries with optional filters."""
    roi_service = ROIService(db)

    entries = await roi_service.get_cost_entries(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category=category,
    )

    # Calculate totals
    total_cents = sum(e.amount_cents for e in entries)
    by_category: dict[str, int] = {}
    for entry in entries:
        by_category[entry.category] = by_category.get(entry.category, 0) + entry.amount_cents

    return CostEntryListResponse(
        entries=[
            CostEntryResponse(
                id=e.id,
                amount_cents=e.amount_cents,
                currency=e.currency,
                category=e.category,
                description=e.description,
                expense_date=e.expense_date,
                is_recurring=bool(e.is_recurring),
                recurrence_period=e.recurrence_period,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total_cents=total_cents,
        by_category=by_category,
    )


@router.delete("/costs/{entry_id}")
async def delete_cost_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a cost entry."""
    roi_service = ROIService(db)

    deleted = await roi_service.delete_cost_entry(
        user_id=current_user.id,
        entry_id=entry_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost entry not found",
        )

    return {"success": True}
