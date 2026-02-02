"""
Brand Deal Schemas

Schema definitions for Brand Deal CRM: pipeline tracking,
contract templates, and negotiation history.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DealStage(str, Enum):
    """Brand deal pipeline stages."""
    LEAD = "lead"               # Initial outreach/inquiry
    QUALIFIED = "qualified"     # Good fit, discussing
    NEGOTIATING = "negotiating" # Terms being discussed
    CONTRACT = "contract"       # Contract sent/signing
    ACTIVE = "active"           # Deal in progress
    COMPLETED = "completed"     # Deliverables done
    LOST = "lost"               # Did not close
    ON_HOLD = "on_hold"         # Paused


class DealType(str, Enum):
    """Types of brand deals."""
    SPONSORED_POST = "sponsored_post"
    SPONSORED_VIDEO = "sponsored_video"
    AMBASSADOR = "ambassador"
    AFFILIATE = "affiliate"
    PRODUCT_REVIEW = "product_review"
    EVENT = "event"
    LICENSING = "licensing"
    OTHER = "other"


class PaymentTerms(str, Enum):
    """Payment timing options."""
    UPFRONT = "upfront"
    ON_DELIVERY = "on_delivery"
    NET_30 = "net_30"
    NET_60 = "net_60"
    SPLIT = "split"
    MILESTONE = "milestone"


class DeliverableType(str, Enum):
    """Types of content deliverables."""
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_SHORT = "youtube_short"
    TIKTOK_VIDEO = "tiktok_video"
    TWITTER_POST = "twitter_post"
    LINKEDIN_POST = "linkedin_post"
    BLOG_POST = "blog_post"
    PODCAST_MENTION = "podcast_mention"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class Deliverable(BaseModel):
    """A single deliverable in a deal."""
    deliverable_id: UUID
    type: DeliverableType
    description: str
    
    # Requirements
    due_date: Optional[datetime] = None
    requirements: List[str] = Field(default_factory=list)
    
    # Status
    status: str = "pending"  # pending, draft, review, approved, published
    content_url: Optional[str] = None
    published_at: Optional[datetime] = None
    
    # Metrics (post-publish)
    views: Optional[int] = None
    engagement: Optional[int] = None


class Contact(BaseModel):
    """Brand contact information."""
    name: str
    email: str
    phone: Optional[str] = None
    title: Optional[str] = None
    company: str
    linkedin_url: Optional[str] = None


class NegotiationNote(BaseModel):
    """Note from negotiation history."""
    note_id: UUID
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # user or contact name


class BrandDeal(BaseModel):
    """
    Brand deal with full pipeline tracking.
    
    Tracks from initial lead to completion.
    """
    deal_id: UUID
    user_id: UUID
    
    # Brand info
    brand_name: str
    brand_logo_url: Optional[str] = None
    brand_website: Optional[str] = None
    contacts: List[Contact] = Field(default_factory=list)
    
    # Deal details
    title: str
    description: Optional[str] = None
    deal_type: DealType
    
    # Value
    deal_value: float
    currency: str = "USD"
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    
    # Pipeline
    stage: DealStage = DealStage.LEAD
    stage_history: List[Dict[str, Any]] = Field(default_factory=list)
    probability: float = 0.0  # Win probability
    
    # Deliverables
    deliverables: List[Deliverable] = Field(default_factory=list)
    
    # Dates
    expected_close_date: Optional[datetime] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    
    # Notes
    notes: List[NegotiationNote] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None


class ContractClause(BaseModel):
    """A clause in a contract template."""
    clause_id: str
    title: str
    content: str
    is_required: bool = True
    is_negotiable: bool = False
    category: str  # scope, payment, exclusivity, rights, termination


class ContractTemplate(BaseModel):
    """Standard contract template."""
    template_id: UUID
    name: str
    description: str
    deal_type: DealType
    
    # Clauses
    clauses: List[ContractClause] = Field(default_factory=list)
    
    # Variables (to be filled)
    variables: List[str] = Field(default_factory=list)
    # e.g., ["brand_name", "deal_value", "deliverable_count"]
    
    # Metadata
    version: str = "1.0"
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DealPipelineMetrics(BaseModel):
    """Pipeline funnel metrics."""
    total_deals: int
    total_value: float
    
    # By stage
    by_stage: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # e.g., {"lead": {"count": 5, "value": 10000}}
    
    # Win rate
    win_rate: float = 0.0
    avg_deal_size: float = 0.0
    avg_sales_cycle_days: float = 0.0
    
    # Velocity
    deals_closed_this_month: int = 0
    revenue_this_month: float = 0.0


# ============== Request/Response Schemas ==============

class CreateDealRequest(BaseModel):
    """Request to create a brand deal."""
    brand_name: str
    title: str
    description: Optional[str] = None
    deal_type: DealType
    deal_value: float
    currency: str = "USD"
    expected_close_date: Optional[datetime] = None
    contacts: Optional[List[Contact]] = None


class CreateDealResponse(BaseModel):
    """Response after creating a deal."""
    deal: BrandDeal


class UpdateStageRequest(BaseModel):
    """Request to update deal stage."""
    new_stage: DealStage
    note: Optional[str] = None


class DealListResponse(BaseModel):
    """List of brand deals."""
    deals: List[BrandDeal]
    total_count: int


class PipelineResponse(BaseModel):
    """Pipeline metrics response."""
    metrics: DealPipelineMetrics
    deals_by_stage: Dict[str, List[BrandDeal]]


class AddDeliverableRequest(BaseModel):
    """Request to add a deliverable."""
    type: DeliverableType
    description: str
    due_date: Optional[datetime] = None
    requirements: Optional[List[str]] = None


class AddNoteRequest(BaseModel):
    """Request to add a negotiation note."""
    content: str
