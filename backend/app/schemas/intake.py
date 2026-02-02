"""
Intake Schemas

Schema-driven intake flow for TurboTax-style onboarding.
Supports adaptive questioning, uncertainty handling, and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.source_labeling import DataSourceType, SourcedValue


class QuestionType(str, Enum):
    """Supported question input types."""
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    CURRENCY = "currency"
    PERCENT = "percent"
    DATE = "date"
    BOOLEAN = "boolean"
    FILE_UPLOAD = "file_upload"
    OAUTH_CONNECT = "oauth_connect"


class ValidationRule(BaseModel):
    """Validation constraints for a question."""
    min: Optional[float] = None
    max: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    allowed_values: Optional[List[str]] = None
    custom_error: Optional[str] = None


class ConditionalLogic(BaseModel):
    """Define when a question should be shown based on previous answers."""
    depends_on: str = Field(..., description="Question ID this depends on")
    show_when: Union[str, List[str], dict] = Field(
        ...,
        description="Value(s) or condition that triggers showing this question"
    )


class IntakeQuestion(BaseModel):
    """Definition of a single intake question."""
    id: str
    type: QuestionType
    label: str
    description: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    
    # Options for select/multi-select
    options: Optional[List[str]] = None
    
    # Validation
    validation: Optional[ValidationRule] = None
    
    # Uncertainty handling
    allow_unsure: bool = Field(
        default=True,
        description="Show 'I'm not sure' option"
    )
    uncertainty_path: Optional[str] = Field(
        None,
        description="Action when user is unsure: verify_via_oauth, upload_doc, skip"
    )
    
    # API verification
    can_verify_via_api: bool = False
    api_source: Optional[str] = Field(
        None,
        description="Which platform API can verify this (instagram, youtube, etc)"
    )
    
    # Conditional display
    condition: Optional[ConditionalLogic] = None
    
    # UI hints
    help_text: Optional[str] = None
    tooltip: Optional[str] = None


class IntakeSection(BaseModel):
    """Grouping of related questions."""
    id: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    questions: List[IntakeQuestion]
    
    # Section-level conditions
    condition: Optional[ConditionalLogic] = None


class IntakeFlow(BaseModel):
    """Complete intake workflow configuration."""
    flow_id: str
    version: str = "1.0"
    title: str
    description: Optional[str] = None
    
    sections: List[IntakeSection]
    
    # Flow metadata
    estimated_minutes: int = Field(default=5)
    can_save_progress: bool = True
    
    # Completion requirements
    required_sections: Optional[List[str]] = None


# ============== Response Schemas ==============

class IntakeAnswer(BaseModel):
    """A single answer to an intake question."""
    question_id: str
    value: Any
    
    # Source tracking
    source: DataSourceType = DataSourceType.USER_INPUT
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Uncertainty flags
    is_unsure: bool = False
    needs_verification: bool = False
    verification_method: Optional[str] = None


class IntakeResponseSubmit(BaseModel):
    """Request to submit intake answers."""
    section_id: str
    answers: List[IntakeAnswer]


class IntakeProgress(BaseModel):
    """Track user's progress through intake flow."""
    user_id: UUID
    flow_id: str
    
    # Progress tracking
    current_section: str
    completed_sections: List[str] = Field(default_factory=list)
    total_sections: int
    
    # Completion status
    percent_complete: float = 0.0
    started_at: datetime
    last_updated: datetime
    completed_at: Optional[datetime] = None
    
    # Pending verifications
    pending_verifications: int = 0


class IntakeProgressResponse(BaseModel):
    """Response with intake progress and next section."""
    progress: IntakeProgress
    next_section: Optional[IntakeSection] = None
    contradictions: List[str] = Field(
        default_factory=list,
        description="IDs of detected contradictions"
    )


# ============== Contradiction Handling ==============

class ContradictionDetail(BaseModel):
    """Details of a detected contradiction for display."""
    contradiction_id: UUID
    field_name: str
    field_label: str
    
    user_reported: Any
    api_verified: Any
    
    discrepancy_description: str
    severity: str
    
    resolution_options: List[str]


class ContradictionResolution(BaseModel):
    """Request to resolve a contradiction."""
    contradiction_id: UUID
    resolution: str = Field(
        ...,
        description="accept_user, accept_api, provide_evidence"
    )
    explanation: Optional[str] = None
    evidence_url: Optional[str] = None


# ============== Verification Tasks ==============

class VerificationTask(BaseModel):
    """A pending verification task for the user."""
    task_id: UUID
    question_id: str
    question_label: str
    
    current_value: Any
    current_confidence: float
    
    verification_method: str
    instructions: str
    
    priority: str = "medium"
    created_at: datetime
    due_by: Optional[datetime] = None


class VerificationTaskList(BaseModel):
    """List of pending verification tasks."""
    tasks: List[VerificationTask]
    total_count: int
    high_priority_count: int
