"""
Affiliate Link Manager API Endpoints

Manage affiliate programs, links, and track conversions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from enum import Enum

router = APIRouter()


# ============== Enums ==============

class AffiliateNetworkEnum(str, Enum):
    """Supported affiliate networks."""
    AMAZON = "amazon"
    SHAREASALE = "shareasale"
    CJ_AFFILIATE = "cj_affiliate"
    RAKUTEN = "rakuten"
    IMPACT = "impact"
    AWIN = "awin"
    PARTNERSTACK = "partnerstack"
    REFERSION = "refersion"
    CUSTOM = "custom"


class LinkStatusEnum(str, Enum):
    """Link status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    BROKEN = "broken"


class ConversionStatusEnum(str, Enum):
    """Conversion status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PAID = "paid"


# ============== Request Models ==============

class AffiliateProgramCreate(BaseModel):
    """Create an affiliate program."""
    name: str = Field(min_length=2, max_length=200)
    network: AffiliateNetworkEnum
    merchant_name: str
    commission_rate: float = Field(ge=0, le=100)  # Percentage
    commission_type: str = "percentage"  # percentage, fixed
    cookie_duration_days: Optional[int] = Field(default=30, ge=1, le=365)
    affiliate_id: str
    api_credentials: Optional[Dict[str, str]] = None
    notes: Optional[str] = None


class AffiliateProgramUpdate(BaseModel):
    """Update an affiliate program."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    commission_rate: Optional[float] = Field(default=None, ge=0, le=100)
    cookie_duration_days: Optional[int] = Field(default=None, ge=1, le=365)
    api_credentials: Optional[Dict[str, str]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class AffiliateLinkCreate(BaseModel):
    """Create an affiliate link."""
    program_id: UUID
    original_url: str
    product_name: str
    campaign_name: Optional[str] = None
    custom_slug: Optional[str] = Field(default=None, min_length=3, max_length=50)
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class AffiliateLinkUpdate(BaseModel):
    """Update an affiliate link."""
    product_name: Optional[str] = None
    campaign_name: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ConversionCreate(BaseModel):
    """Manually log a conversion."""
    link_id: UUID
    order_id: Optional[str] = None
    order_value: float = Field(ge=0)
    commission_amount: float = Field(ge=0)
    customer_country: Optional[str] = None
    notes: Optional[str] = None


class BulkLinkCreate(BaseModel):
    """Create multiple links at once."""
    program_id: UUID
    links: List[Dict[str, str]]  # List of {original_url, product_name, campaign_name?}


# ============== Response Models ==============

class AffiliateProgram(BaseModel):
    """An affiliate program."""
    id: UUID
    user_id: UUID
    name: str
    network: AffiliateNetworkEnum
    merchant_name: str
    commission_rate: float
    commission_type: str
    cookie_duration_days: int
    affiliate_id: str
    is_active: bool
    total_clicks: int
    total_conversions: int
    total_revenue: float
    total_commission: float
    created_at: datetime


class AffiliateLink(BaseModel):
    """An affiliate link."""
    id: UUID
    program_id: UUID
    original_url: str
    short_url: str
    product_name: str
    campaign_name: Optional[str] = None
    tags: List[str]
    status: LinkStatusEnum
    click_count: int
    conversion_count: int
    revenue: float
    commission_earned: float
    last_clicked: Optional[datetime] = None
    created_at: datetime


class ClickEvent(BaseModel):
    """A click event."""
    id: UUID
    link_id: UUID
    timestamp: datetime
    ip_hash: str
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    device_type: Optional[str] = None


class ConversionEvent(BaseModel):
    """A conversion event."""
    id: UUID
    link_id: UUID
    click_id: Optional[UUID] = None
    order_id: Optional[str] = None
    order_value: float
    commission_amount: float
    status: ConversionStatusEnum
    customer_country: Optional[str] = None
    converted_at: datetime
    confirmed_at: Optional[datetime] = None


class LinkStats(BaseModel):
    """Statistics for a link."""
    link_id: UUID
    total_clicks: int
    unique_clicks: int
    conversions: int
    conversion_rate: float
    revenue: float
    commission: float
    clicks_by_day: Dict[str, int]
    clicks_by_country: Dict[str, int]
    clicks_by_device: Dict[str, int]
    top_referrers: List[Dict[str, Any]]


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_programs: int
    total_links: int
    total_clicks: int
    total_conversions: int
    total_revenue: float
    total_commission: float
    conversion_rate: float
    pending_commission: float
    paid_commission: float
    top_performing_links: List[Dict[str, Any]]
    revenue_by_network: Dict[str, float]
    clicks_trend: List[Dict[str, Any]]
    conversions_trend: List[Dict[str, Any]]


class LinkHealthReport(BaseModel):
    """Link health check report."""
    link_id: UUID
    url: str
    status: str
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    last_checked: datetime
    issues: List[str]


# ============== Endpoints ==============

# ---- Programs ----

@router.post("/programs", response_model=AffiliateProgram)
async def create_program(
    program: AffiliateProgramCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new affiliate program.
    """
    return AffiliateProgram(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=program.name,
        network=program.network,
        merchant_name=program.merchant_name,
        commission_rate=program.commission_rate,
        commission_type=program.commission_type,
        cookie_duration_days=program.cookie_duration_days or 30,
        affiliate_id=program.affiliate_id,
        is_active=True,
        total_clicks=0,
        total_conversions=0,
        total_revenue=0.0,
        total_commission=0.0,
        created_at=datetime.utcnow()
    )


@router.get("/programs", response_model=List[AffiliateProgram])
async def list_programs(
    network: Optional[AffiliateNetworkEnum] = None,
    is_active: Optional[bool] = None,
    # current_user = Depends(get_current_user)
):
    """
    List all affiliate programs.
    """
    return []


@router.get("/programs/{program_id}", response_model=AffiliateProgram)
async def get_program(
    program_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific affiliate program.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Affiliate program not found"
    )


@router.patch("/programs/{program_id}", response_model=AffiliateProgram)
async def update_program(
    program_id: UUID,
    update: AffiliateProgramUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update an affiliate program.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Affiliate program not found"
    )


@router.delete("/programs/{program_id}")
async def delete_program(
    program_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete an affiliate program.
    """
    return {"message": "Program deleted successfully"}


# ---- Links ----

@router.post("/links", response_model=AffiliateLink)
async def create_link(
    link: AffiliateLinkCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new affiliate link with automatic shortening.
    """
    short_url = f"https://idkit.link/{link.custom_slug or 'abc123'}"

    return AffiliateLink(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        program_id=link.program_id,
        original_url=link.original_url,
        short_url=short_url,
        product_name=link.product_name,
        campaign_name=link.campaign_name,
        tags=link.tags or [],
        status=LinkStatusEnum.ACTIVE,
        click_count=0,
        conversion_count=0,
        revenue=0.0,
        commission_earned=0.0,
        last_clicked=None,
        created_at=datetime.utcnow()
    )


@router.post("/links/bulk", response_model=List[AffiliateLink])
async def create_bulk_links(
    request: BulkLinkCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create multiple affiliate links at once.
    """
    return []


@router.get("/links", response_model=List[AffiliateLink])
async def list_links(
    program_id: Optional[UUID] = None,
    campaign_name: Optional[str] = None,
    status: Optional[LinkStatusEnum] = None,
    tags: Optional[List[str]] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    # current_user = Depends(get_current_user)
):
    """
    List all affiliate links with optional filtering.
    """
    return []


@router.get("/links/{link_id}", response_model=AffiliateLink)
async def get_link(
    link_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific affiliate link.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Affiliate link not found"
    )


@router.patch("/links/{link_id}", response_model=AffiliateLink)
async def update_link(
    link_id: UUID,
    update: AffiliateLinkUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update an affiliate link.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Affiliate link not found"
    )


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete an affiliate link.
    """
    return {"message": "Link deleted successfully"}


@router.get("/links/{link_id}/stats", response_model=LinkStats)
async def get_link_stats(
    link_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    # current_user = Depends(get_current_user)
):
    """
    Get detailed statistics for a link.
    """
    return LinkStats(
        link_id=link_id,
        total_clicks=0,
        unique_clicks=0,
        conversions=0,
        conversion_rate=0.0,
        revenue=0.0,
        commission=0.0,
        clicks_by_day={},
        clicks_by_country={},
        clicks_by_device={},
        top_referrers=[]
    )


# ---- Tracking ----

@router.post("/track/click/{short_code}")
async def track_click(
    short_code: str,
    referrer: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Track a click and redirect to the destination URL.

    This endpoint is called when someone clicks an affiliate link.
    """
    # In production, this would redirect to the actual URL
    return {
        "message": "Click tracked",
        "redirect_url": "https://example.com/product"
    }


@router.post("/track/conversion", response_model=ConversionEvent)
async def track_conversion(
    conversion: ConversionCreate,
    # current_user = Depends(get_current_user)
):
    """
    Manually log a conversion event.
    """
    return ConversionEvent(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        link_id=conversion.link_id,
        click_id=None,
        order_id=conversion.order_id,
        order_value=conversion.order_value,
        commission_amount=conversion.commission_amount,
        status=ConversionStatusEnum.PENDING,
        customer_country=conversion.customer_country,
        converted_at=datetime.utcnow(),
        confirmed_at=None
    )


@router.get("/conversions", response_model=List[ConversionEvent])
async def list_conversions(
    link_id: Optional[UUID] = None,
    program_id: Optional[UUID] = None,
    status: Optional[ConversionStatusEnum] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    # current_user = Depends(get_current_user)
):
    """
    List conversion events.
    """
    return []


# ---- Analytics ----

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    # current_user = Depends(get_current_user)
):
    """
    Get dashboard statistics for affiliate performance.
    """
    return DashboardStats(
        total_programs=0,
        total_links=0,
        total_clicks=0,
        total_conversions=0,
        total_revenue=0.0,
        total_commission=0.0,
        conversion_rate=0.0,
        pending_commission=0.0,
        paid_commission=0.0,
        top_performing_links=[],
        revenue_by_network={},
        clicks_trend=[],
        conversions_trend=[]
    )


@router.post("/links/health-check", response_model=List[LinkHealthReport])
async def check_links_health(
    link_ids: Optional[List[UUID]] = None,
    check_all: bool = False,
    # current_user = Depends(get_current_user)
):
    """
    Check the health status of affiliate links.

    Verifies that links are still valid and working.
    """
    return []


# ---- Networks ----

@router.get("/networks")
async def list_supported_networks():
    """
    List all supported affiliate networks.
    """
    return {
        "networks": [
            {
                "value": "amazon",
                "label": "Amazon Associates",
                "description": "Amazon's affiliate program",
                "commission_range": "1-10%"
            },
            {
                "value": "shareasale",
                "label": "ShareASale",
                "description": "Large affiliate network with many merchants",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "cj_affiliate",
                "label": "CJ Affiliate",
                "description": "Commission Junction - major affiliate network",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "rakuten",
                "label": "Rakuten Advertising",
                "description": "Global affiliate network",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "impact",
                "label": "Impact",
                "description": "Partnership automation platform",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "awin",
                "label": "Awin",
                "description": "Global affiliate marketing network",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "partnerstack",
                "label": "PartnerStack",
                "description": "B2B SaaS partnership platform",
                "commission_range": "15-30% typical"
            },
            {
                "value": "refersion",
                "label": "Refersion",
                "description": "Ecommerce affiliate tracking",
                "commission_range": "Varies by merchant"
            },
            {
                "value": "custom",
                "label": "Custom",
                "description": "Direct affiliate relationship",
                "commission_range": "Custom"
            }
        ]
    }
