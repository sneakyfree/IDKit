"""
Intake Models

Database models for TurboTax-style intake system.
Tracks onboarding progress, answers, contradictions, and verification tasks.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class IntakeProgress(Base, UUIDMixin, TimestampMixin):
    """Track user's progress through intake flow."""

    __tablename__ = "intake_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    flow_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="creator_onboarding_v1",
    )

    flow_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
    )

    # Progress tracking
    current_section: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="profile_basics",
    )

    completed_sections: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    total_sections: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    percent_complete: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    answers: Mapped[list["IntakeAnswer"]] = relationship(
        "IntakeAnswer",
        back_populates="progress",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<IntakeProgress user={self.user_id} {self.percent_complete}%>"


class IntakeAnswer(Base, UUIDMixin, TimestampMixin):
    """Store individual intake answers with source metadata."""

    __tablename__ = "intake_answers"

    progress_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_progress.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    section_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # The actual answer value (stored as JSON for flexibility)
    value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Source labeling (provenance tracking)
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user_input",
    )  # user_input, api_verified, estimated, unknown

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    api_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # Platform API if verified

    # Uncertainty flags
    is_unsure: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    needs_verification: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    progress: Mapped["IntakeProgress"] = relationship(
        "IntakeProgress",
        back_populates="answers",
    )

    def __repr__(self) -> str:
        return f"<IntakeAnswer q={self.question_id} source={self.source}>"


class ContradictionRecord(Base, UUIDMixin, TimestampMixin):
    """Log detected data contradictions between sources."""

    __tablename__ = "contradiction_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    field_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Source A (typically user input)
    value_a: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    source_a: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    confidence_a: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Source B (typically API verified)
    value_b: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    source_b: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    confidence_b: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Analysis
    discrepancy_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )  # low, medium, high

    # Resolution
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    resolution: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # accept_user, accept_api, provide_evidence

    resolved_value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    resolved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Contradiction field={self.field_name} resolved={self.is_resolved}>"


class VerificationTask(Base, UUIDMixin, TimestampMixin):
    """Pending verification tasks for uncertain data."""

    __tablename__ = "verification_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_answers.id", ondelete="SET NULL"),
        nullable=True,
    )

    question_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    question_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Current unverified value
    current_value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    current_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
    )

    # Verification instructions
    verification_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # oauth_connect, document_upload, manual_confirm

    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )  # low, medium, high

    due_by: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Completion
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    new_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<VerificationTask q={self.question_id} priority={self.priority}>"
