"""
Audit Database Models

Models for audit-grade reproducibility: snapshots, versions, deltas.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AuditSnapshotRecord(Base, UUIDMixin, TimestampMixin):
    """Immutable snapshot record - never modified after creation."""

    __tablename__ = "audit_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Type and description
    snapshot_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    analysis_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Input state
    data_sources: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    model_versions: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    rule_versions: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Output state
    recommendations: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    confidence_scores: Mapped[dict[str, float] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Provenance
    evidence_chain: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    computation_log: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Integrity
    content_hash: Mapped[str | None] = mapped_column(
        String(64),  # SHA-256 hex
        nullable=True,
    )

    is_sealed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        return f"<AuditSnapshot {self.snapshot_type}:{self.analysis_type}>"


class VersionRecord(Base, UUIDMixin, TimestampMixin):
    """Version registry record for models, rules, configs."""

    __tablename__ = "version_registry"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    version_type: Mapped[str] = mapped_column(
        String(20),  # model, rule, config
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    deprecated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Version {self.name}:{self.version}>"


class DeltaReportRecord(Base, UUIDMixin, TimestampMixin):
    """Delta report comparing two snapshots."""

    __tablename__ = "delta_reports"

    # Snapshots compared
    snapshot_before_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    snapshot_after_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    time_delta: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Changes
    changes: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    total_changes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    high_impact_changes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Version changes
    model_changes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    rule_changes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Recommendation impact
    recommendations_added: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    recommendations_removed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    recommendations_modified: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<DeltaReport {self.snapshot_before_id} -> {self.snapshot_after_id}>"
