"""
Explainability Schemas

Schema definitions for multi-view insight rendering.
Same data, 4 different presentations for different audiences.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.source_labeling import EvidenceItem


class ViewType(str, Enum):
    """Audience view types for insight rendering."""
    CREATOR = "creator"      # Plain language, actionable, mobile-friendly
    MANAGER = "manager"      # Talk tracks, client-ready, compliant
    TECHNICAL = "technical"  # Evidence chains, API sources, statistics
    AUDIT = "audit"          # Immutable logs, version history, provenance


class InsightType(str, Enum):
    """Types of insights that can be rendered."""
    PERFORMANCE = "performance"
    RECOMMENDATION = "recommendation"
    TREND = "trend"
    BLOCKER = "blocker"
    OPPORTUNITY = "opportunity"
    WARNING = "warning"
    METRIC = "metric"


class Insight(BaseModel):
    """
    Base insight data structure.
    
    Contains the raw data that will be rendered differently
    for each view type.
    """
    insight_id: UUID
    insight_type: InsightType
    
    # Core data
    title: str
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Statistical backing
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    sample_size: Optional[int] = None
    p_value: Optional[float] = None
    correlation: Optional[float] = None
    
    # Evidence
    evidence_chain: List[EvidenceItem] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    
    # Versioning
    model_version: Optional[str] = None
    rule_version: Optional[str] = None
    
    # Timing
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_as_of: Optional[datetime] = None


class RenderedInsight(BaseModel):
    """
    View-specific rendering of an insight.
    
    Same underlying data, different presentation:
    - creator: "Your engagement is 2x better when you post at 7 PM"
    - manager: "Recommend shifting client's posting schedule to 7 PM EST"
    - technical: "Engagement rate correlation r=0.73 (p<0.01) with 7 PM posting"
    - audit: "[timestamp] EngagementAnalysisJob completed. Source: Instagram Graph API"
    """
    insight_id: UUID
    view_type: ViewType
    
    # Rendered content
    headline: str
    body: str
    action_items: List[str] = Field(default_factory=list)
    
    # View-specific formatting
    formatted_data: Dict[str, Any] = Field(default_factory=dict)
    footnotes: List[str] = Field(default_factory=list)
    
    # For technical/audit views
    evidence_summary: Optional[str] = None
    statistical_notes: Optional[str] = None
    
    # For audit view
    audit_trail: Optional[str] = None
    version_info: Optional[str] = None
    
    # Metadata
    rendered_at: datetime = Field(default_factory=datetime.utcnow)


class ViewTemplate(BaseModel):
    """
    Template configuration for a view type.
    """
    view_type: ViewType
    name: str
    description: str
    
    # Template rules
    include_statistics: bool = False
    include_evidence: bool = False
    include_timestamps: bool = False
    include_versions: bool = False
    
    # Formatting
    max_headline_length: int = 100
    max_body_length: int = 500
    tone: str = "professional"  # casual, professional, technical, formal


class RenderRequest(BaseModel):
    """Request to render an insight."""
    insight: Insight
    view_type: ViewType
    include_action_items: bool = True


class RenderResponse(BaseModel):
    """Response with rendered insight."""
    rendered: RenderedInsight
    original_insight_id: UUID


class MultiViewRenderRequest(BaseModel):
    """Request to render an insight in multiple views."""
    insight: Insight
    view_types: List[ViewType] = Field(default_factory=lambda: list(ViewType))


class MultiViewRenderResponse(BaseModel):
    """Response with all view renderings."""
    renderings: Dict[str, RenderedInsight]
    insight_id: UUID
