"""
Source Labeling Schemas

Infrastructure for data provenance tracking. Every data point in IDKit
carries metadata about its origin, confidence, and evidence chain.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Origin of a data value."""
    USER_INPUT = "user_input"       # Self-reported by creator
    API_VERIFIED = "api_verified"   # Confirmed via platform API (OAuth)
    ESTIMATED = "estimated"         # Calculated/inferred by system
    UNKNOWN = "unknown"             # Source cannot be determined


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels."""
    HIGH = "high"           # >90% confidence
    MEDIUM = "medium"       # 60-90% confidence
    LOW = "low"             # 30-60% confidence
    UNCERTAIN = "uncertain" # <30% confidence


# Generic type for sourced values
T = TypeVar("T")


class SourceMetadata(BaseModel):
    """Provenance metadata attached to any value."""
    source: DataSourceType
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    api_source: Optional[str] = Field(
        None,
        description="API endpoint or platform if API-verified"
    )
    verified_by: Optional[str] = Field(
        None,
        description="User ID if manually verified"
    )
    notes: Optional[str] = None


class SourcedValue(BaseModel, Generic[T]):
    """
    Generic wrapper that attaches source metadata to any value.
    
    Usage:
        follower_count = SourcedValue[int](
            value=50000,
            source=DataSourceType.API_VERIFIED,
            confidence=0.99,
            api_source="instagram_graph_api"
        )
    """
    value: Any  # Will be T at runtime
    source: DataSourceType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    api_source: Optional[str] = None
    verified_by: Optional[str] = None


class EvidenceItem(BaseModel):
    """Reference to source material supporting a data point or decision."""
    evidence_id: UUID
    evidence_type: str = Field(
        ...,
        description="Type: api_response, document, user_attestation, calculation"
    )
    source_url: Optional[str] = None
    source_name: str
    timestamp: datetime
    raw_data: Optional[dict] = Field(
        None,
        description="Snapshot of source data at time of capture"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ContradictionAlert(BaseModel):
    """Alert when data sources conflict with each other."""
    contradiction_id: UUID
    field_name: str = Field(..., description="Which field has conflicting data")
    
    # Source 1 (typically user input)
    value_a: Any
    source_a: DataSourceType
    confidence_a: float
    
    # Source 2 (typically API verified)
    value_b: Any
    source_b: DataSourceType
    confidence_b: float
    
    # Analysis
    discrepancy_percent: Optional[float] = Field(
        None,
        description="Percentage difference for numeric values"
    )
    severity: str = Field(
        default="medium",
        description="low, medium, high based on impact"
    )
    suggested_resolution: str = Field(
        default="verify",
        description="Action: verify, accept_api, accept_user, investigate"
    )
    
    # Status
    is_resolved: bool = False
    resolved_value: Optional[Any] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VerificationRequest(BaseModel):
    """Request to verify an uncertain data point."""
    field_name: str
    current_value: Any
    current_source: DataSourceType
    current_confidence: float
    verification_method: str = Field(
        ...,
        description="How to verify: oauth_connect, document_upload, manual_confirm"
    )
    instructions: str
    priority: str = Field(default="medium")


class VerificationResult(BaseModel):
    """Result of a verification action."""
    field_name: str
    verified_value: Any
    new_source: DataSourceType
    new_confidence: float
    evidence: Optional[EvidenceItem] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
