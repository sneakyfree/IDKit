"""
Compliance & Backup Models

Database models for compliance reports, checks, and backup management.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ComplianceReport(Base, UUIDMixin, TimestampMixin):
    """
    Compliance audit report.
    """

    __tablename__ = "compliance_reports"

    type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )  # gdpr, ftc, coppa, ccpa

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, running, passed, failed, warning

    findings: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )  # List of findings with severity

    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    checks_passed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    checks_failed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    checks_warning: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )  # Admin user who triggered

    def __repr__(self) -> str:
        return f"<ComplianceReport {self.type} - {self.status}>"


class ComplianceCheck(Base, UUIDMixin, TimestampMixin):
    """
    Individual compliance check / rule.
    """

    __tablename__ = "compliance_checks"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )  # data_retention, consent, content_moderation, access_control

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="unchecked", nullable=False,
    )  # passed, failed, warning, unchecked

    details: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )

    is_automated: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ComplianceCheck {self.name} - {self.status}>"


class Backup(Base, UUIDMixin, TimestampMixin):
    """
    Database backup record.
    """

    __tablename__ = "backups"

    type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # full, incremental

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, running, completed, failed

    size_bytes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    storage_path: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )  # S3 path

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )  # Admin user or "system" for scheduled

    def __repr__(self) -> str:
        return f"<Backup {self.type} - {self.status}>"


class BackupSchedule(Base, UUIDMixin, TimestampMixin):
    """
    Automated backup schedule.
    """

    __tablename__ = "backup_schedules"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    frequency: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # daily, weekly, monthly

    backup_type: Mapped[str] = mapped_column(
        String(50), default="full", nullable=False,
    )

    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    retention_days: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BackupSchedule {self.name} - {'enabled' if self.enabled else 'disabled'}>"
