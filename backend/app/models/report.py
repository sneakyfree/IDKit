"""
Report Models

Database models for custom report generation and scheduling.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Report(Base, UUIDMixin, TimestampMixin):
    """
    Custom analytics report.

    Users can configure, generate, and schedule custom reports.
    """

    __tablename__ = "reports"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    # Configuration
    metrics: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )  # ["followers", "engagement_rate", "revenue"]

    platforms: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )  # ["instagram", "youtube"]

    date_range: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # {"start": "2026-01-01", "end": "2026-01-31"}

    # Scheduling
    schedule: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # {"frequency": "weekly", "day": "monday", "time": "09:00"}

    is_scheduled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    # Generated data
    last_generated_data: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )

    last_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    export_format: Mapped[str] = mapped_column(
        String(10), default="pdf", nullable=False,
    )  # pdf, csv, json

    # Relationships
    user: Mapped["User"] = relationship("User", backref="reports")

    def __repr__(self) -> str:
        return f"<Report {self.name}>"
