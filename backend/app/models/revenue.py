"""
Revenue Database Models

Models for revenue intelligence: brand deals, pricing, payouts.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class BrandDealRecord(Base, UUIDMixin, TimestampMixin):
    """Brand deal CRM record."""

    __tablename__ = "brand_deals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Brand info
    brand_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    brand_logo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    brand_website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Deal details
    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Value
    deal_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    payment_terms: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Pipeline
    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="lead",
        index=True,
    )

    probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Dates
    expected_close_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    contract_start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    contract_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # JSON fields
    contacts: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    deliverables: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    notes: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    stage_history: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    tags: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<BrandDeal {self.brand_name}: {self.title}>"


class RevenueEntryRecord(Base, UUIDMixin, TimestampMixin):
    """Revenue entry from any source."""

    __tablename__ = "revenue_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    platform: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Amount
    gross_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    net_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Timing
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # References
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    brand_deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_deals.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<RevenueEntry {self.source}: ${self.net_amount}>"


class PayoutRecord(Base, UUIDMixin, TimestampMixin):
    """Payout transaction record."""

    __tablename__ = "payout_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Amount
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Stripe
    stripe_transfer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    stripe_payout_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Dates
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Payout {self.status}: ${self.amount}>"


class PricingBenchmarkRecord(Base, UUIDMixin, TimestampMixin):
    """Market pricing benchmark data."""

    __tablename__ = "pricing_benchmarks"

    # Context
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    niche: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Distribution
    p25: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    median: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    p75: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Metadata
    sample_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    data_period: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PricingBenchmark {self.platform}:{self.content_type}>"
