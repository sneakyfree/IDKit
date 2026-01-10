"""
Subscriber Management API Endpoints

Manage subscriber lists, segments, and subscription preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
import io
import csv

router = APIRouter()


# ============== Enums ==============

class SubscriberStatusEnum(str, Enum):
    """Subscriber status."""
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    PENDING = "pending"  # Double opt-in pending


class SubscriptionSourceEnum(str, Enum):
    """How the subscriber was acquired."""
    WEBSITE = "website"
    IMPORT = "import"
    API = "api"
    LANDING_PAGE = "landing_page"
    SOCIAL = "social"
    REFERRAL = "referral"
    MANUAL = "manual"


class ChannelTypeEnum(str, Enum):
    """Communication channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class SegmentConditionOperator(str, Enum):
    """Operators for segment conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_SET = "is_set"
    IS_NOT_SET = "is_not_set"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


# ============== Request Models ==============

class SubscriberCreate(BaseModel):
    """Create a subscriber."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    channels: List[ChannelTypeEnum] = [ChannelTypeEnum.EMAIL]
    list_ids: Optional[List[UUID]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    source: SubscriptionSourceEnum = SubscriptionSourceEnum.API
    send_confirmation: bool = True


class SubscriberUpdate(BaseModel):
    """Update a subscriber."""
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = None
    channels: Optional[List[ChannelTypeEnum]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class SubscriberListCreate(BaseModel):
    """Create a subscriber list."""
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    double_opt_in: bool = True
    welcome_email_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


class SubscriberListUpdate(BaseModel):
    """Update a subscriber list."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = None
    double_opt_in: Optional[bool] = None
    welcome_email_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


class SegmentCondition(BaseModel):
    """A condition for segmentation."""
    field: str
    operator: SegmentConditionOperator
    value: Any


class SegmentCreate(BaseModel):
    """Create a segment."""
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    conditions: List[SegmentCondition]
    match_type: str = "all"  # all, any
    list_id: Optional[UUID] = None  # If None, applies to all subscribers


class SegmentUpdate(BaseModel):
    """Update a segment."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = None
    conditions: Optional[List[SegmentCondition]] = None
    match_type: Optional[str] = None


class BulkAddRequest(BaseModel):
    """Bulk add subscribers to a list."""
    subscriber_ids: List[UUID]
    list_id: UUID


class BulkTagRequest(BaseModel):
    """Bulk tag subscribers."""
    subscriber_ids: List[UUID]
    tags: List[str]
    action: str = "add"  # add, remove, replace


class ImportRequest(BaseModel):
    """Import configuration."""
    list_id: UUID
    update_existing: bool = True
    send_confirmation: bool = True
    tags: Optional[List[str]] = None


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request."""
    channels: Optional[List[ChannelTypeEnum]] = None  # None = all channels
    reason: Optional[str] = None
    feedback: Optional[str] = None


# ============== Response Models ==============

class Subscriber(BaseModel):
    """A subscriber."""
    id: UUID
    user_id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    status: SubscriberStatusEnum
    channels: List[ChannelTypeEnum]
    source: SubscriptionSourceEnum
    tags: List[str]
    custom_fields: Dict[str, Any]
    list_ids: List[UUID]
    engagement_score: float
    email_opens: int
    email_clicks: int
    last_engaged: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SubscriberList(BaseModel):
    """A subscriber list."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    subscriber_count: int
    active_count: int
    unsubscribed_count: int
    double_opt_in: bool
    welcome_email_id: Optional[UUID] = None
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class Segment(BaseModel):
    """A segment."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    conditions: List[SegmentCondition]
    match_type: str
    list_id: Optional[UUID] = None
    subscriber_count: int
    last_calculated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ImportResult(BaseModel):
    """Result of an import operation."""
    total_rows: int
    imported: int
    updated: int
    skipped: int
    errors: List[Dict[str, Any]]


class EngagementStats(BaseModel):
    """Engagement statistics for a subscriber."""
    subscriber_id: UUID
    total_emails_sent: int
    total_opens: int
    total_clicks: int
    open_rate: float
    click_rate: float
    last_open: Optional[datetime] = None
    last_click: Optional[datetime] = None
    engagement_score: float
    engagement_trend: str  # increasing, stable, decreasing


class ListGrowthStats(BaseModel):
    """Growth statistics for a list."""
    list_id: UUID
    total_subscribers: int
    active_subscribers: int
    growth_rate: float
    net_growth_30d: int
    new_subscribers_30d: int
    unsubscribes_30d: int
    growth_by_source: Dict[str, int]
    growth_trend: List[Dict[str, Any]]


# ============== Endpoints ==============

# ---- Subscribers ----

@router.post("/", response_model=Subscriber)
async def create_subscriber(
    subscriber: SubscriberCreate,
    # current_user = Depends(get_current_user)
):
    """
    Add a new subscriber.
    """
    if not subscriber.email and not subscriber.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required"
        )

    full_name = None
    if subscriber.first_name or subscriber.last_name:
        full_name = f"{subscriber.first_name or ''} {subscriber.last_name or ''}".strip()

    return Subscriber(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        email=subscriber.email,
        phone=subscriber.phone,
        first_name=subscriber.first_name,
        last_name=subscriber.last_name,
        full_name=full_name,
        status=SubscriberStatusEnum.PENDING if subscriber.send_confirmation else SubscriberStatusEnum.ACTIVE,
        channels=subscriber.channels,
        source=subscriber.source,
        tags=subscriber.tags or [],
        custom_fields=subscriber.custom_fields or {},
        list_ids=subscriber.list_ids or [],
        engagement_score=0.0,
        email_opens=0,
        email_clicks=0,
        last_engaged=None,
        confirmed_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/", response_model=List[Subscriber])
async def list_subscribers(
    list_id: Optional[UUID] = None,
    segment_id: Optional[UUID] = None,
    status: Optional[SubscriberStatusEnum] = None,
    channel: Optional[ChannelTypeEnum] = None,
    tags: Optional[List[str]] = Query(default=None),
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    # current_user = Depends(get_current_user)
):
    """
    List subscribers with optional filtering.
    """
    return []


@router.get("/{subscriber_id}", response_model=Subscriber)
async def get_subscriber(
    subscriber_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific subscriber.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )


@router.get("/email/{email}", response_model=Subscriber)
async def get_subscriber_by_email(
    email: EmailStr,
    # current_user = Depends(get_current_user)
):
    """
    Get a subscriber by email address.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )


@router.patch("/{subscriber_id}", response_model=Subscriber)
async def update_subscriber(
    subscriber_id: UUID,
    update: SubscriberUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update a subscriber.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )


@router.delete("/{subscriber_id}")
async def delete_subscriber(
    subscriber_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete a subscriber permanently.
    """
    return {"message": "Subscriber deleted successfully"}


@router.post("/{subscriber_id}/unsubscribe")
async def unsubscribe(
    subscriber_id: UUID,
    request: UnsubscribeRequest,
    # current_user = Depends(get_current_user)
):
    """
    Unsubscribe a subscriber from specified channels.
    """
    return {
        "message": "Unsubscribed successfully",
        "channels": request.channels or ["all"]
    }


@router.post("/{subscriber_id}/resubscribe", response_model=Subscriber)
async def resubscribe(
    subscriber_id: UUID,
    channels: List[ChannelTypeEnum],
    # current_user = Depends(get_current_user)
):
    """
    Resubscribe a previously unsubscribed subscriber.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )


@router.post("/confirm/{token}")
async def confirm_subscription(
    token: str,
):
    """
    Confirm a subscription (double opt-in).

    Public endpoint - no authentication required.
    """
    return {
        "message": "Subscription confirmed",
        "status": "active"
    }


@router.get("/{subscriber_id}/engagement", response_model=EngagementStats)
async def get_subscriber_engagement(
    subscriber_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get engagement statistics for a subscriber.
    """
    return EngagementStats(
        subscriber_id=subscriber_id,
        total_emails_sent=0,
        total_opens=0,
        total_clicks=0,
        open_rate=0.0,
        click_rate=0.0,
        last_open=None,
        last_click=None,
        engagement_score=0.0,
        engagement_trend="stable"
    )


# ---- Lists ----

@router.post("/lists", response_model=SubscriberList)
async def create_list(
    list_data: SubscriberListCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new subscriber list.
    """
    return SubscriberList(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=list_data.name,
        description=list_data.description,
        subscriber_count=0,
        active_count=0,
        unsubscribed_count=0,
        double_opt_in=list_data.double_opt_in,
        welcome_email_id=list_data.welcome_email_id,
        tags=list_data.tags or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/lists", response_model=List[SubscriberList])
async def list_subscriber_lists(
    tags: Optional[List[str]] = Query(default=None),
    # current_user = Depends(get_current_user)
):
    """
    List all subscriber lists.
    """
    return []


@router.get("/lists/{list_id}", response_model=SubscriberList)
async def get_list(
    list_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific list.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="List not found"
    )


@router.patch("/lists/{list_id}", response_model=SubscriberList)
async def update_list(
    list_id: UUID,
    update: SubscriberListUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update a subscriber list.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="List not found"
    )


@router.delete("/lists/{list_id}")
async def delete_list(
    list_id: UUID,
    delete_subscribers: bool = False,
    # current_user = Depends(get_current_user)
):
    """
    Delete a subscriber list.
    """
    return {
        "message": "List deleted successfully",
        "subscribers_deleted": delete_subscribers
    }


@router.post("/lists/{list_id}/subscribers/{subscriber_id}")
async def add_to_list(
    list_id: UUID,
    subscriber_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Add a subscriber to a list.
    """
    return {"message": "Subscriber added to list"}


@router.delete("/lists/{list_id}/subscribers/{subscriber_id}")
async def remove_from_list(
    list_id: UUID,
    subscriber_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Remove a subscriber from a list.
    """
    return {"message": "Subscriber removed from list"}


@router.get("/lists/{list_id}/growth", response_model=ListGrowthStats)
async def get_list_growth(
    list_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get growth statistics for a list.
    """
    return ListGrowthStats(
        list_id=list_id,
        total_subscribers=0,
        active_subscribers=0,
        growth_rate=0.0,
        net_growth_30d=0,
        new_subscribers_30d=0,
        unsubscribes_30d=0,
        growth_by_source={},
        growth_trend=[]
    )


# ---- Segments ----

@router.post("/segments", response_model=Segment)
async def create_segment(
    segment: SegmentCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new segment.
    """
    return Segment(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=segment.name,
        description=segment.description,
        conditions=[c.model_dump() for c in segment.conditions],
        match_type=segment.match_type,
        list_id=segment.list_id,
        subscriber_count=0,
        last_calculated=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/segments", response_model=List[Segment])
async def list_segments(
    list_id: Optional[UUID] = None,
    # current_user = Depends(get_current_user)
):
    """
    List all segments.
    """
    return []


@router.get("/segments/{segment_id}", response_model=Segment)
async def get_segment(
    segment_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific segment.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Segment not found"
    )


@router.patch("/segments/{segment_id}", response_model=Segment)
async def update_segment(
    segment_id: UUID,
    update: SegmentUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update a segment.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Segment not found"
    )


@router.delete("/segments/{segment_id}")
async def delete_segment(
    segment_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete a segment.
    """
    return {"message": "Segment deleted successfully"}


@router.get("/segments/{segment_id}/subscribers", response_model=List[Subscriber])
async def get_segment_subscribers(
    segment_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    # current_user = Depends(get_current_user)
):
    """
    Get subscribers in a segment.
    """
    return []


@router.post("/segments/{segment_id}/refresh")
async def refresh_segment(
    segment_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Refresh segment membership calculation.
    """
    return {
        "message": "Segment refresh started",
        "subscriber_count": 0
    }


# ---- Bulk Operations ----

@router.post("/bulk/add-to-list")
async def bulk_add_to_list(
    request: BulkAddRequest,
    # current_user = Depends(get_current_user)
):
    """
    Add multiple subscribers to a list.
    """
    return {
        "message": "Subscribers added to list",
        "added": len(request.subscriber_ids)
    }


@router.post("/bulk/tag")
async def bulk_tag(
    request: BulkTagRequest,
    # current_user = Depends(get_current_user)
):
    """
    Add or remove tags from multiple subscribers.
    """
    return {
        "message": f"Tags {request.action}ed",
        "affected": len(request.subscriber_ids)
    }


@router.post("/bulk/delete")
async def bulk_delete(
    subscriber_ids: List[UUID],
    # current_user = Depends(get_current_user)
):
    """
    Delete multiple subscribers.
    """
    return {
        "message": "Subscribers deleted",
        "deleted": len(subscriber_ids)
    }


# ---- Import/Export ----

@router.post("/import", response_model=ImportResult)
async def import_subscribers(
    file: UploadFile = File(...),
    list_id: UUID = None,
    update_existing: bool = True,
    send_confirmation: bool = True,
    # current_user = Depends(get_current_user)
):
    """
    Import subscribers from a CSV file.

    Expected columns: email, first_name, last_name, phone, tags
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    return ImportResult(
        total_rows=0,
        imported=0,
        updated=0,
        skipped=0,
        errors=[]
    )


@router.get("/export")
async def export_subscribers(
    list_id: Optional[UUID] = None,
    segment_id: Optional[UUID] = None,
    status: Optional[SubscriberStatusEnum] = None,
    format: str = Query(default="csv", regex="^(csv|json)$"),
    # current_user = Depends(get_current_user)
):
    """
    Export subscribers to CSV or JSON.
    """
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["email", "first_name", "last_name", "phone", "status", "created_at"])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=subscribers_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


# ---- Tags ----

@router.get("/tags")
async def list_tags(
    # current_user = Depends(get_current_user)
):
    """
    List all subscriber tags.
    """
    return {
        "tags": [],
        "total": 0
    }


@router.get("/tags/{tag}/subscribers", response_model=List[Subscriber])
async def get_subscribers_by_tag(
    tag: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    # current_user = Depends(get_current_user)
):
    """
    Get all subscribers with a specific tag.
    """
    return []
