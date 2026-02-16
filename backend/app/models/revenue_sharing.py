"""
Revenue Sharing Models

Database models for revenue sharing agreements and distributions.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class RevenueAgreement(Base, UUIDMixin, TimestampMixin):
    """
    Revenue sharing agreement between two parties.
    """

    __tablename__ = "revenue_agreements"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
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

    split_percentage: Mapped[float] = mapped_column(
        Float, nullable=False,
    )  # Partner's percentage (e.g., 30.0 means 30%)

    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True,
    )  # active, paused, completed, cancelled

    total_earned_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    total_paid_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="usd", nullable=False,
    )

    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    terms: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], backref="revenue_agreements_owned",
    )
    partner: Mapped["User"] = relationship(
        "User", foreign_keys=[partner_id], backref="revenue_agreements_partner",
    )
    distributions: Mapped[List["RevenueDistribution"]] = relationship(
        "RevenueDistribution", back_populates="agreement",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RevenueAgreement {self.name} - {self.split_percentage}%>"


class RevenueDistribution(Base, UUIDMixin, TimestampMixin):
    """
    Individual revenue distribution payment.
    """

    __tablename__ = "revenue_distributions"

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_agreements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount_cents: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, processing, paid, failed

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    stripe_transfer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )

    # Relationships
    agreement: Mapped["RevenueAgreement"] = relationship(
        "RevenueAgreement", back_populates="distributions",
    )

    def __repr__(self) -> str:
        return f"<RevenueDistribution ${self.amount_cents/100:.2f} - {self.status}>"
