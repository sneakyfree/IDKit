"""
Audit Schemas

Schema definitions for audit-grade reproducibility.
Immutable snapshots, version pinning, and delta reports.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SnapshotType(str, Enum):
    """Types of audit snapshots."""
    ANALYSIS = "analysis"       # Analysis run snapshot
    RECOMMENDATION = "recommendation"  # Recommendation generation
    DECISION = "decision"       # User decision point
    MODEL_UPDATE = "model_update"  # Model version change


class DataSourceSnapshot(BaseModel):
    """Snapshot of data from a specific source at a point in time."""
    source_name: str
    source_type: str  # api, database, user_input, calculated
    
    # Data captured
    data: Dict[str, Any] = Field(default_factory=dict)
    record_count: int = 0
    
    # Timing
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: Optional[datetime] = None  # When source data was last updated
    
    # API details (if applicable)
    api_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    response_hash: Optional[str] = None  # Hash of raw response


class ModelVersion(BaseModel):
    """Version information for an AI model or rule set."""
    model_name: str
    version: str
    
    # Details
    description: Optional[str] = None
    release_date: Optional[datetime] = None
    
    # Checksums for verification
    weights_hash: Optional[str] = None
    config_hash: Optional[str] = None
    
    # Status
    is_active: bool = True
    deprecated_at: Optional[datetime] = None


class ComputationStep(BaseModel):
    """A single step in the computation log."""
    step_id: UUID
    step_number: int
    
    # What happened
    operation: str
    description: str
    
    # Inputs/outputs
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing
    started_at: datetime
    completed_at: datetime
    duration_ms: int = 0
    
    # Model used (if any)
    model_version: Optional[str] = None


class AuditSnapshot(BaseModel):
    """
    Immutable snapshot capturing exact state at analysis time.
    
    Every decision can be replayed and explained at any future point.
    """
    snapshot_id: UUID
    snapshot_type: SnapshotType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Owner
    user_id: UUID
    
    # Context
    analysis_type: str
    description: Optional[str] = None
    
    # Input State - Captured at moment of analysis
    data_sources: Dict[str, DataSourceSnapshot] = Field(default_factory=dict)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    rule_versions: Dict[str, str] = Field(default_factory=dict)
    
    # Configuration at time of analysis
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    # Output State
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Provenance
    evidence_chain: List[Dict[str, Any]] = Field(default_factory=list)
    computation_log: List[ComputationStep] = Field(default_factory=list)
    
    # Integrity
    content_hash: Optional[str] = None  # Hash of entire snapshot for verification
    
    # Immutability flag
    is_sealed: bool = True  # Once created, cannot be modified


class DeltaChange(BaseModel):
    """A single change between two snapshots."""
    field_path: str  # e.g., "recommendations[0].confidence"
    change_type: str  # added, removed, modified
    
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Impact
    impact_level: str = "medium"  # low, medium, high
    impact_description: Optional[str] = None


class DeltaReport(BaseModel):
    """
    Comparison report between two snapshots.
    
    Shows what changed and the impact on recommendations.
    """
    report_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Snapshots compared
    snapshot_before_id: UUID
    snapshot_after_id: UUID
    time_delta: Optional[str] = None
    
    # Changes detected
    changes: List[DeltaChange] = Field(default_factory=list)
    
    # Summary
    total_changes: int = 0
    high_impact_changes: int = 0
    
    # Model/rule changes
    model_changes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    rule_changes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    
    # Recommendation impact
    recommendations_added: int = 0
    recommendations_removed: int = 0
    recommendations_modified: int = 0
    
    # Summary text
    summary: str = ""


# ============== Request/Response Schemas ==============

class CreateSnapshotRequest(BaseModel):
    """Request to create a new snapshot."""
    snapshot_type: SnapshotType
    analysis_type: str
    description: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class SnapshotResponse(BaseModel):
    """Response with snapshot details."""
    snapshot: AuditSnapshot


class SnapshotListResponse(BaseModel):
    """Response with list of snapshots."""
    snapshots: List[AuditSnapshot]
    total_count: int


class DeltaRequest(BaseModel):
    """Request to generate a delta report."""
    snapshot_id_before: UUID
    snapshot_id_after: UUID


class DeltaResponse(BaseModel):
    """Response with delta report."""
    report: DeltaReport


class VersionRegistryEntry(BaseModel):
    """Entry in the version registry."""
    name: str
    version: str
    type: str  # model, rule, config
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    hash: Optional[str] = None
    is_active: bool = True
