"""
Email & SMS Campaign API Endpoints

Create and manage email and SMS marketing campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

router = APIRouter()


# ============== Enums ==============

class CampaignStatusEnum(str, Enum):
    """Campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignTypeEnum(str, Enum):
    """Campaign type."""
    EMAIL = "email"
    SMS = "sms"


class EmailTypeEnum(str, Enum):
    """Email types."""
    NEWSLETTER = "newsletter"
    PROMOTIONAL = "promotional"
    ANNOUNCEMENT = "announcement"
    WELCOME = "welcome"
    FOLLOWUP = "followup"
    TRANSACTIONAL = "transactional"


# ============== Request Models ==============

class EmailTemplateCreate(BaseModel):
    """Create an email template."""
    name: str = Field(min_length=2, max_length=200)
    subject: str = Field(min_length=2, max_length=500)
    html_content: str
    text_content: Optional[str] = None
    email_type: EmailTypeEnum = EmailTypeEnum.NEWSLETTER
    tags: Optional[List[str]] = None


class EmailTemplateUpdate(BaseModel):
    """Update an email template."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    subject: Optional[str] = Field(default=None, min_length=2, max_length=500)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    tags: Optional[List[str]] = None


class EmailCampaignCreate(BaseModel):
    """Create an email campaign."""
    name: str = Field(min_length=2, max_length=200)
    subject: str = Field(min_length=2, max_length=500)
    preview_text: Optional[str] = Field(default=None, max_length=200)
    from_name: str
    from_email: EmailStr
    reply_to: Optional[EmailStr] = None
    template_id: Optional[UUID] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    list_ids: List[UUID]
    segment_ids: Optional[List[UUID]] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class SMSCampaignCreate(BaseModel):
    """Create an SMS campaign."""
    name: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=1, max_length=1600)
    sender_id: Optional[str] = Field(default=None, max_length=11)
    list_ids: List[UUID]
    segment_ids: Optional[List[UUID]] = None
    scheduled_at: Optional[datetime] = None
    include_opt_out: bool = True
    shorten_links: bool = True
    tags: Optional[List[str]] = None


class CampaignUpdate(BaseModel):
    """Update a campaign."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class SubjectLineRequest(BaseModel):
    """Request for AI subject line generation."""
    topic: str
    tone: str = "engaging"
    include_emoji: bool = True
    count: int = Field(default=5, ge=1, le=10)


class EmailContentRequest(BaseModel):
    """Request for AI email content generation."""
    topic: str
    email_type: EmailTypeEnum
    key_points: Optional[List[str]] = None
    tone: str = "professional"
    cta_text: Optional[str] = None
    personalization: bool = True


class SMSContentRequest(BaseModel):
    """Request for AI SMS content generation."""
    topic: str
    include_link: bool = True
    link_url: Optional[str] = None
    character_limit: int = Field(default=160, ge=50, le=1600)


class ABTestCreate(BaseModel):
    """Create an A/B test for email campaigns."""
    campaign_id: UUID
    test_type: str = "subject"  # subject, content, send_time
    variants: List[Dict[str, Any]]
    test_size_percent: int = Field(default=20, ge=5, le=50)
    winning_metric: str = "open_rate"  # open_rate, click_rate, conversion_rate
    auto_send_winner: bool = True


# ============== Response Models ==============

class EmailTemplate(BaseModel):
    """An email template."""
    id: UUID
    user_id: UUID
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    email_type: EmailTypeEnum
    tags: List[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime


class Campaign(BaseModel):
    """A campaign (email or SMS)."""
    id: UUID
    user_id: UUID
    name: str
    campaign_type: CampaignTypeEnum
    status: CampaignStatusEnum

    # Email specific
    subject: Optional[str] = None
    preview_text: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    html_content: Optional[str] = None

    # SMS specific
    message: Optional[str] = None
    sender_id: Optional[str] = None

    # Common
    list_ids: List[UUID]
    segment_ids: List[UUID]
    recipient_count: int
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    tags: List[str]

    # Stats
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    bounced_count: int = 0
    unsubscribed_count: int = 0

    created_at: datetime
    updated_at: datetime


class CampaignStats(BaseModel):
    """Campaign statistics."""
    campaign_id: UUID
    sent: int
    delivered: int
    delivery_rate: float
    opened: int
    open_rate: float
    clicked: int
    click_rate: float
    bounced: int
    bounce_rate: float
    unsubscribed: int
    unsubscribe_rate: float
    complaints: int
    complaint_rate: float
    # Time-based metrics
    opens_by_hour: Dict[str, int]
    clicks_by_link: Dict[str, int]
    opens_by_device: Dict[str, int]
    opens_by_location: Dict[str, int]


class ABTest(BaseModel):
    """An A/B test."""
    id: UUID
    campaign_id: UUID
    test_type: str
    variants: List[Dict[str, Any]]
    status: str
    test_size_percent: int
    winning_metric: str
    winner_variant: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    created_at: datetime


class SubjectLineSuggestion(BaseModel):
    """A subject line suggestion."""
    subject: str
    predicted_open_rate: float
    emoji_used: bool
    character_count: int


class SMSPreview(BaseModel):
    """SMS preview with segment info."""
    message: str
    character_count: int
    segment_count: int
    encoding: str
    shortened_links: List[Dict[str, str]]


# ============== Endpoints ==============

# ---- Email Templates ----

@router.post("/email/templates", response_model=EmailTemplate)
async def create_email_template(
    template: EmailTemplateCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new email template.
    """
    return EmailTemplate(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=template.name,
        subject=template.subject,
        html_content=template.html_content,
        text_content=template.text_content,
        email_type=template.email_type,
        tags=template.tags or [],
        usage_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/email/templates", response_model=List[EmailTemplate])
async def list_email_templates(
    email_type: Optional[EmailTypeEnum] = None,
    tags: Optional[List[str]] = Query(default=None),
    # current_user = Depends(get_current_user)
):
    """
    List all email templates.
    """
    return []


@router.get("/email/templates/{template_id}", response_model=EmailTemplate)
async def get_email_template(
    template_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get a specific email template.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Template not found"
    )


@router.patch("/email/templates/{template_id}", response_model=EmailTemplate)
async def update_email_template(
    template_id: UUID,
    update: EmailTemplateUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update an email template.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Template not found"
    )


@router.delete("/email/templates/{template_id}")
async def delete_email_template(
    template_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete an email template.
    """
    return {"message": "Template deleted successfully"}


# ---- Email Campaigns ----

@router.post("/email", response_model=Campaign)
async def create_email_campaign(
    campaign: EmailCampaignCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new email campaign.
    """
    return Campaign(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=campaign.name,
        campaign_type=CampaignTypeEnum.EMAIL,
        status=CampaignStatusEnum.DRAFT,
        subject=campaign.subject,
        preview_text=campaign.preview_text,
        from_name=campaign.from_name,
        from_email=campaign.from_email,
        html_content=campaign.html_content,
        list_ids=campaign.list_ids,
        segment_ids=campaign.segment_ids or [],
        recipient_count=0,
        scheduled_at=campaign.scheduled_at,
        tags=campaign.tags or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.post("/email/{campaign_id}/send")
async def send_email_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    # current_user = Depends(get_current_user)
):
    """
    Send an email campaign immediately.
    """
    # In production, this would queue the campaign for sending
    return {
        "message": "Campaign queued for sending",
        "campaign_id": str(campaign_id),
        "status": "sending"
    }


@router.post("/email/{campaign_id}/schedule")
async def schedule_email_campaign(
    campaign_id: UUID,
    scheduled_at: datetime,
    # current_user = Depends(get_current_user)
):
    """
    Schedule an email campaign for later.
    """
    return {
        "message": "Campaign scheduled",
        "campaign_id": str(campaign_id),
        "scheduled_at": scheduled_at.isoformat()
    }


@router.post("/email/{campaign_id}/test")
async def send_test_email(
    campaign_id: UUID,
    test_emails: List[EmailStr],
    # current_user = Depends(get_current_user)
):
    """
    Send a test email to specified addresses.
    """
    return {
        "message": "Test emails sent",
        "sent_to": test_emails
    }


# ---- SMS Campaigns ----

@router.post("/sms", response_model=Campaign)
async def create_sms_campaign(
    campaign: SMSCampaignCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create a new SMS campaign.
    """
    return Campaign(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        name=campaign.name,
        campaign_type=CampaignTypeEnum.SMS,
        status=CampaignStatusEnum.DRAFT,
        message=campaign.message,
        sender_id=campaign.sender_id,
        list_ids=campaign.list_ids,
        segment_ids=campaign.segment_ids or [],
        recipient_count=0,
        scheduled_at=campaign.scheduled_at,
        tags=campaign.tags or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.post("/sms/{campaign_id}/send")
async def send_sms_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    # current_user = Depends(get_current_user)
):
    """
    Send an SMS campaign immediately.
    """
    return {
        "message": "SMS campaign queued for sending",
        "campaign_id": str(campaign_id),
        "status": "sending"
    }


@router.post("/sms/preview", response_model=SMSPreview)
async def preview_sms(
    message: str,
    shorten_links: bool = True,
    # current_user = Depends(get_current_user)
):
    """
    Preview an SMS with character count and segment info.
    """
    # Check for non-GSM characters
    gsm_chars = set('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà')
    is_gsm = all(c in gsm_chars for c in message)

    encoding = "GSM-7" if is_gsm else "Unicode"
    chars_per_segment = 160 if is_gsm else 70

    char_count = len(message)
    segment_count = (char_count + chars_per_segment - 1) // chars_per_segment

    return SMSPreview(
        message=message,
        character_count=char_count,
        segment_count=segment_count,
        encoding=encoding,
        shortened_links=[]
    )


# ---- Common Campaign Operations ----

@router.get("/", response_model=List[Campaign])
async def list_campaigns(
    campaign_type: Optional[CampaignTypeEnum] = None,
    status: Optional[CampaignStatusEnum] = None,
    tags: Optional[List[str]] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    # current_user = Depends(get_current_user)
):
    """
    List all campaigns (email and SMS).
    """
    return []


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get details of a specific campaign.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Campaign not found"
    )


@router.patch("/{campaign_id}", response_model=Campaign)
async def update_campaign(
    campaign_id: UUID,
    update: CampaignUpdate,
    # current_user = Depends(get_current_user)
):
    """
    Update a campaign.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Campaign not found"
    )


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Delete a campaign.
    """
    return {"message": "Campaign deleted successfully"}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Pause a sending campaign.
    """
    return {"message": "Campaign paused", "status": "paused"}


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Resume a paused campaign.
    """
    return {"message": "Campaign resumed", "status": "sending"}


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get detailed statistics for a campaign.
    """
    return CampaignStats(
        campaign_id=campaign_id,
        sent=0,
        delivered=0,
        delivery_rate=0.0,
        opened=0,
        open_rate=0.0,
        clicked=0,
        click_rate=0.0,
        bounced=0,
        bounce_rate=0.0,
        unsubscribed=0,
        unsubscribe_rate=0.0,
        complaints=0,
        complaint_rate=0.0,
        opens_by_hour={},
        clicks_by_link={},
        opens_by_device={},
        opens_by_location={}
    )


@router.post("/{campaign_id}/duplicate", response_model=Campaign)
async def duplicate_campaign(
    campaign_id: UUID,
    new_name: str,
    # current_user = Depends(get_current_user)
):
    """
    Duplicate an existing campaign.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Campaign not found"
    )


# ---- AI Content Generation ----

@router.post("/ai/subject-lines", response_model=List[SubjectLineSuggestion])
async def generate_subject_lines(
    request: SubjectLineRequest,
    # current_user = Depends(get_current_user)
):
    """
    Generate AI-powered email subject line suggestions.
    """
    suggestions = [
        SubjectLineSuggestion(
            subject=f"🚀 {request.topic} - Don't Miss Out!",
            predicted_open_rate=0.32,
            emoji_used=True,
            character_count=35
        ),
        SubjectLineSuggestion(
            subject=f"Your Guide to {request.topic}",
            predicted_open_rate=0.28,
            emoji_used=False,
            character_count=25
        ),
        SubjectLineSuggestion(
            subject=f"[New] Everything about {request.topic}",
            predicted_open_rate=0.30,
            emoji_used=False,
            character_count=32
        )
    ]
    return suggestions[:request.count]


@router.post("/ai/email-content")
async def generate_email_content(
    request: EmailContentRequest,
    # current_user = Depends(get_current_user)
):
    """
    Generate AI-powered email content.
    """
    return {
        "subject": f"Discover {request.topic}",
        "preview_text": f"Your guide to {request.topic} is here",
        "html_content": f"""
        <h1>Welcome!</h1>
        <p>We're excited to share our latest insights on {request.topic}.</p>
        <p>{request.cta_text or 'Learn More'}</p>
        """,
        "text_content": f"Welcome! We're excited to share our latest insights on {request.topic}."
    }


@router.post("/ai/sms-content")
async def generate_sms_content(
    request: SMSContentRequest,
    # current_user = Depends(get_current_user)
):
    """
    Generate AI-powered SMS content.
    """
    message = f"Check out our latest on {request.topic}!"
    if request.include_link and request.link_url:
        message += f" {request.link_url}"

    return {
        "message": message,
        "character_count": len(message),
        "segment_count": 1
    }


# ---- A/B Testing ----

@router.post("/ab-tests", response_model=ABTest)
async def create_ab_test(
    test: ABTestCreate,
    # current_user = Depends(get_current_user)
):
    """
    Create an A/B test for a campaign.
    """
    return ABTest(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        campaign_id=test.campaign_id,
        test_type=test.test_type,
        variants=test.variants,
        status="active",
        test_size_percent=test.test_size_percent,
        winning_metric=test.winning_metric,
        winner_variant=None,
        results=None,
        created_at=datetime.utcnow()
    )


@router.get("/ab-tests/{test_id}", response_model=ABTest)
async def get_ab_test(
    test_id: UUID,
    # current_user = Depends(get_current_user)
):
    """
    Get A/B test details and results.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="A/B test not found"
    )


@router.post("/ab-tests/{test_id}/pick-winner")
async def pick_ab_test_winner(
    test_id: UUID,
    variant_id: str,
    # current_user = Depends(get_current_user)
):
    """
    Manually pick the winner for an A/B test.
    """
    return {
        "message": "Winner selected",
        "variant_id": variant_id,
        "status": "winner_selected"
    }
