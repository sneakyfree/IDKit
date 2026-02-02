"""
ROI Schemas

Pydantic schemas for ROI API request/response validation.
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    """Time period types for ROI reports."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CostCategory(str, Enum):
    """Categories for cost entries."""
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    ADVERTISING = "advertising"
    CONTENT_CREATION = "content_creation"
    PLATFORM_FEES = "platform_fees"
    LABOR = "labor"
    OTHER = "other"


# ============== Revenue Breakdown ==============

class RevenueBreakdown(BaseModel):
    """Breakdown of revenue by source."""
    brand_deals: int = Field(0, description="Revenue from brand deals (cents)")
    affiliate: int = Field(0, description="Affiliate commission revenue (cents)")
    subscriptions: int = Field(0, description="Subscription/membership revenue (cents)")
    royalties: int = Field(0, description="AI training royalties (cents)")
    other: int = Field(0, description="Other revenue sources (cents)")
    total: int = Field(0, description="Total revenue (cents)")


class CostBreakdown(BaseModel):
    """Breakdown of costs by category."""
    platform_fees: int = Field(0, description="Platform fees (cents)")
    content_creation: int = Field(0, description="Content creation costs (cents)")
    advertising: int = Field(0, description="Advertising/promotion costs (cents)")
    software: int = Field(0, description="Software/tools costs (cents)")
    equipment: int = Field(0, description="Equipment costs (cents)")
    labor: int = Field(0, description="Labor/contractor costs (cents)")
    other: int = Field(0, description="Other costs (cents)")
    total: int = Field(0, description="Total costs (cents)")


# ============== ROI Report ==============

class ROIMetrics(BaseModel):
    """Calculated ROI metrics."""
    net_profit_cents: int
    roi_percentage: float = Field(..., description="Return on investment as percentage")
    profit_margin: float = Field(..., description="Profit margin as percentage")
    revenue_per_content: float = Field(..., description="Average revenue per content piece (cents)")
    revenue_per_view: float = Field(..., description="Revenue per view (cents)")
    revenue_per_follower: float = Field(..., description="Revenue per new follower (cents)")
    engagement_rate: float = Field(..., description="Engagement rate as percentage")


class ROIReportResponse(BaseModel):
    """Full ROI report response."""
    id: str
    period_start: datetime
    period_end: datetime
    period_type: str

    revenue: RevenueBreakdown
    costs: CostBreakdown
    metrics: ROIMetrics

    # Engagement stats
    total_views: int
    total_engagements: int
    new_followers: int
    content_pieces: int

    created_at: datetime

    class Config:
        from_attributes = True


class ROICalculationRequest(BaseModel):
    """Request to calculate ROI for a time period."""
    start_date: date
    end_date: date
    include_projections: bool = False


class ROISummaryResponse(BaseModel):
    """Summary ROI data for dashboard."""
    current_period: ROIReportResponse
    previous_period: Optional[ROIReportResponse] = None
    revenue_change_percent: float = 0.0
    profit_change_percent: float = 0.0
    roi_change_percent: float = 0.0


# ============== Cost Entries ==============

class CostEntryCreate(BaseModel):
    """Request to create a cost entry."""
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="usd", max_length=3)
    category: CostCategory
    description: Optional[str] = None
    expense_date: date
    is_recurring: bool = False
    recurrence_period: Optional[str] = None


class CostEntryResponse(BaseModel):
    """Cost entry response."""
    id: str
    amount_cents: int
    currency: str
    category: str
    description: Optional[str]
    expense_date: datetime
    is_recurring: bool
    recurrence_period: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CostEntryListResponse(BaseModel):
    """List of cost entries with summary."""
    entries: List[CostEntryResponse]
    total_cents: int
    by_category: dict[str, int]


# ============== Projections ==============

class ProjectionDataPoint(BaseModel):
    """Single projection data point."""
    date: date
    projected_revenue_cents: int
    projected_costs_cents: int
    projected_profit_cents: int
    confidence: float = Field(..., ge=0, le=1)


class ROIProjectionResponse(BaseModel):
    """ROI projections for future periods."""
    projections: List[ProjectionDataPoint]
    average_monthly_revenue: int
    average_monthly_costs: int
    trend: str  # "growing", "stable", "declining"
    confidence_score: float
