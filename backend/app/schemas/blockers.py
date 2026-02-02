"""
Blockers/Unlockers Schemas

Schema definitions for the Blockers Engine.
Identifies issues and generates actionable fix plans.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.source_labeling import EvidenceItem


class BlockerCategory(str, Enum):
    """Categories of blockers."""
    CONTENT = "content"          # Quality, frequency, format issues
    ENGAGEMENT = "engagement"    # Low interaction, declining metrics
    MONETIZATION = "monetization"  # Revenue gaps, missed opportunities
    GROWTH = "growth"            # Follower stagnation, reach limits
    TECHNICAL = "technical"      # Platform issues, API problems
    COMPLIANCE = "compliance"    # FTC, copyright, TOS issues
    PROFILE = "profile"          # Bio, links, branding issues


class BlockerSeverity(str, Enum):
    """Severity levels for blockers."""
    CRITICAL = "critical"   # Blocking major opportunities
    HIGH = "high"           # Significant impact
    MEDIUM = "medium"       # Moderate impact
    LOW = "low"             # Minor issue


class UnlockerTimeframe(str, Enum):
    """Timeframes for action plans."""
    QUICK_WIN = "quick_win"  # < 1 hour
    THIRTY_DAYS = "30_days"  # 1-30 days
    NINETY_DAYS = "90_days"  # 30-90 days


class UnlockerEffort(str, Enum):
    """Effort levels for actions."""
    LOW = "low"       # Easy, minimal effort
    MEDIUM = "medium"  # Moderate effort
    HIGH = "high"     # Significant effort required


class BlockerAnalysis(BaseModel):
    """
    A detected issue blocking creator success.
    
    Every blocker has evidence - we never accuse without proof.
    """
    blocker_id: UUID
    category: BlockerCategory
    severity: BlockerSeverity
    
    # Description
    title: str
    why_not: str  # Plain language explanation
    impact_description: str  # What this is costing you
    
    # Evidence
    evidence: List[EvidenceItem] = Field(default_factory=list)
    
    # Quantified impact
    confidence_impact: float = Field(
        ge=0.0,
        le=1.0,
        description="How much this affects success probability"
    )
    estimated_revenue_impact: Optional[float] = None  # Monthly $ impact
    estimated_reach_impact: Optional[float] = None  # % reach reduction
    
    # Related scenarios
    blocks_scenarios: List[str] = Field(
        default_factory=list,
        description="Scenario IDs this blocker is preventing"
    )
    
    # Status
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class UnlockerAction(BaseModel):
    """
    An actionable fix for a blocker.
    
    Every unlocker has clear success criteria and proof requirements.
    """
    action_id: UUID
    blocker_id: UUID  # Which blocker this fixes
    
    # Description
    title: str
    what_to_do: str  # Step-by-step instructions
    why_it_helps: str  # Why this will work
    
    # Timeline and effort
    timeframe: UnlockerTimeframe
    effort_level: UnlockerEffort
    estimated_time: str  # e.g., "30 minutes", "2 hours"
    
    # Prerequisites
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Blocker IDs that must be cleared first"
    )
    
    # Success criteria
    proof_required: List[str] = Field(
        default_factory=list,
        description="Evidence needed to verify completion"
    )
    success_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected metric improvements"
    )
    
    # Priority
    priority_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Effort/impact ratio score"
    )
    
    # Progress
    is_started: bool = False
    is_completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resources
    helpful_links: List[str] = Field(default_factory=list)
    related_content: List[str] = Field(default_factory=list)


class FixList(BaseModel):
    """
    Prioritized fix list organized by timeframe.
    """
    user_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Quick wins (< 1 hour)
    quick_wins: List[UnlockerAction] = Field(default_factory=list)
    
    # 30-day sprints
    thirty_day_actions: List[UnlockerAction] = Field(default_factory=list)
    
    # 90-day transformations
    ninety_day_actions: List[UnlockerAction] = Field(default_factory=list)
    
    # Summary
    total_actions: int = 0
    total_blockers_addressed: int = 0
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)


class BlockerScanRequest(BaseModel):
    """Request to scan for blockers."""
    categories: Optional[List[BlockerCategory]] = None
    min_severity: Optional[BlockerSeverity] = None
    include_resolved: bool = False


class BlockerScanResponse(BaseModel):
    """Response with detected blockers."""
    blockers: List[BlockerAnalysis]
    total_count: int
    critical_count: int
    estimated_total_impact: Optional[float] = None
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)


class UnlockerCompleteRequest(BaseModel):
    """Request to mark an unlocker as complete."""
    action_id: UUID
    proof: Optional[str] = None
    notes: Optional[str] = None


# ============== Simulation Schemas ==============

class SimulationScenario(BaseModel):
    """A what-if scenario to simulate."""
    name: str
    description: str
    
    # Actions to simulate
    actions: List[str] = Field(
        default_factory=list,
        description="Action IDs or descriptions"
    )
    
    # Assumptions
    assumptions: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    """Result of a what-if simulation."""
    simulation_id: UUID
    scenario: SimulationScenario
    
    # Projected outcomes
    projected_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Confidence interval
    confidence_low: Dict[str, Any] = Field(default_factory=dict)
    confidence_high: Dict[str, Any] = Field(default_factory=dict)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    
    # Comparison to baseline
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict)
    improvement_vs_baseline: Dict[str, float] = Field(default_factory=dict)
    
    # Caveats
    warnings: List[str] = Field(default_factory=list)
    assumptions_made: List[str] = Field(default_factory=list)
    
    simulated_at: datetime = Field(default_factory=datetime.utcnow)


class SimulateRequest(BaseModel):
    """Request to run a what-if simulation."""
    scenarios: List[SimulationScenario]
    baseline_period_days: int = Field(default=30, ge=7, le=90)


class SimulateResponse(BaseModel):
    """Response with simulation results."""
    results: List[SimulationResult]
    comparison_summary: Dict[str, Any] = Field(default_factory=dict)
