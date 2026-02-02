"""
Scenario Database Models

Persistence models for scenarios, blockers, and simulations.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SavedScenario(Base, UUIDMixin, TimestampMixin):
    """User-saved opportunity scenario."""

    __tablename__ = "saved_scenarios"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scenario details
    scenario_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    opportunity_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Confidence
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.7,
    )

    source_label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="estimated",
    )

    # Impact
    estimated_impact: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="available",
        index=True,
    )

    # Priority
    priority_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
    )

    def __repr__(self) -> str:
        return f"<SavedScenario {self.title}>"


class BlockerRecord(Base, UUIDMixin, TimestampMixin):
    """Detected blocker with resolution status."""

    __tablename__ = "blocker_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Blocker details
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    why_not: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    impact_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Evidence
    evidence: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Impact scores
    confidence_impact: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
    )

    estimated_revenue_impact: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Status
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Detection
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<BlockerRecord {self.category}:{self.title}>"


class UnlockerProgress(Base, UUIDMixin, TimestampMixin):
    """Progress tracking for unlocker actions."""

    __tablename__ = "unlocker_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blocker_records.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Action details
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    what_to_do: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timeframe: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    effort_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Progress
    is_started: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Proof
    proof_submitted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<UnlockerProgress {self.title}>"


class SimulationRecord(Base, UUIDMixin, TimestampMixin):
    """Saved what-if simulation results."""

    __tablename__ = "simulation_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scenario
    scenario_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    scenario_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    actions: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    assumptions: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Results
    projected_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    baseline_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    improvement_vs_baseline: Mapped[dict[str, float] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Confidence
    overall_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.7,
    )

    confidence_low: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    confidence_high: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Warnings
    warnings: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    simulated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<SimulationRecord {self.scenario_name}>"
