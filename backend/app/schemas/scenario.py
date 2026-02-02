"""
Scenario Schemas

Schema definitions for the Scenario Universe Builder.
Generates ranked opportunities from connected data sources.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.source_labeling import DataSourceType, EvidenceItem


class ScenarioType(str, Enum):
    """Types of opportunity scenarios."""
    CONTENT = "content"           # Content creation opportunities
    COLLABORATION = "collaboration"  # Partnership/collab opportunities
    MONETIZATION = "monetization"  # Revenue opportunities
    GROWTH = "growth"             # Audience growth opportunities
    BRAND_DEAL = "brand_deal"     # Sponsorship opportunities
    PLATFORM = "platform"         # New platform expansion


class ScenarioStatus(str, Enum):
    """Status of a scenario opportunity."""
    AVAILABLE = "available"       # Can be pursued now
    BLOCKED = "blocked"           # Has prerequisites
    IN_PROGRESS = "in_progress"   # Currently being worked on
    COMPLETED = "completed"       # Successfully completed
    EXPIRED = "expired"           # No longer available


class ContentScenario(BaseModel):
    """
    A single opportunity scenario with confidence scoring.
    
    Every scenario has evidence chain - we never invent data.
    """
    scenario_id: UUID
    scenario_type: ScenarioType
    
    # Description
    title: str
    description: str
    opportunity_summary: str  # Plain language "what this means for you"
    
    # Confidence and sources
    source_label: DataSourceType
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence_chain: List[EvidenceItem] = Field(default_factory=list)
    
    # Impact estimation
    estimated_impact: Dict[str, Any] = Field(
        default_factory=dict,
        description="Projected metrics: followers, engagement, revenue, etc."
    )
    impact_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence in impact estimates"
    )
    
    # Effort and timeline
    effort_level: str = "medium"  # low, medium, high
    time_to_complete: Optional[str] = None  # e.g., "2 hours", "1 week"
    
    # Prerequisites
    blockers: List[str] = Field(
        default_factory=list,
        description="Blocker IDs that must be resolved first"
    )
    
    # Timing
    best_timing: Optional[str] = None  # When to pursue
    expiry: Optional[datetime] = None  # When opportunity expires
    
    # Ranking
    priority_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Composite score for ranking"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UnknownFactor(BaseModel):
    """
    Represents a gap in data that we explicitly don't know.
    
    We NEVER invent data - we label unknowns honestly.
    """
    factor_id: UUID
    category: str  # pricing, eligibility, terms, metrics
    description: str
    
    # What we'd need to fill this gap
    required_action: str  # connect_api, user_input, research
    importance: str = "medium"  # low, medium, high
    
    # What assumptions we're making (if any)
    current_assumption: Optional[str] = None
    assumption_source: Optional[str] = None


class ScenarioUniverse(BaseModel):
    """
    Complete ranked opportunity list for a creator.
    
    Exhaustive within connected sources - clearly labels unknowns.
    """
    user_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Data sources used
    data_sources: List[str] = Field(default_factory=list)
    source_freshness: Dict[str, datetime] = Field(default_factory=dict)
    
    # Scenarios by type
    scenarios: List[ContentScenario] = Field(default_factory=list)
    
    # Summary stats
    total_scenarios: int = 0
    high_priority_count: int = 0
    blocked_count: int = 0
    
    # Honest unknowns
    unknown_factors: List[UnknownFactor] = Field(default_factory=list)
    
    # Confidence in completeness
    coverage_confidence: float = Field(
        default=0.7,
        description="How confident we are that we've found all opportunities"
    )


class ScenarioFilter(BaseModel):
    """Filter and sort options for scenarios."""
    scenario_types: Optional[List[ScenarioType]] = None
    min_confidence: float = 0.0
    max_effort: Optional[str] = None
    exclude_blocked: bool = False
    sort_by: str = "priority_score"  # priority_score, confidence, impact
    sort_desc: bool = True
    limit: int = 50


class ScenarioGenerateRequest(BaseModel):
    """Request to generate scenario universe."""
    include_types: Optional[List[ScenarioType]] = None
    time_horizon_days: int = Field(default=30, ge=7, le=365)
    include_low_confidence: bool = False


class ScenarioGenerateResponse(BaseModel):
    """Response with generated scenarios."""
    universe: ScenarioUniverse
    generation_time_ms: int
    warnings: List[str] = Field(default_factory=list)
