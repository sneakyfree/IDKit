"""
Performance Metrics Model

Stores Web Vital metrics for frontend performance monitoring.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PerformanceMetric(Base, UUIDMixin, TimestampMixin):
    """Individual Web Vital metric record."""

    __tablename__ = "performance_metrics"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # LCP, FID, CLS, FCP, TTFB, INP
    value: Mapped[float] = mapped_column(Float, nullable=False)
    rating: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # good, needs-improvement, poor
    delta: Mapped[float] = mapped_column(Float, default=0)
    metric_id: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # Unique per web-vitals instance
    navigation_type: Mapped[str] = mapped_column(String(30), default="navigate")
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
