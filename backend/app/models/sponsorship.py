"""
Sponsorship Models

Database models for sponsorship and deliverable management.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    DateTime,
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


class Sponsorship(Base, UUIDMixin, TimestampMixin):
    """
    Brand sponsorship deal.

    Tracks sponsorship lifecycle from negotiation to completion.
    """

    __tablename__ = "sponsorships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    brand_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    brand_logo_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    brand_contact_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="negotiating", nullable=False, index=True,
    )  # negotiating, active, completed, cancelled

    value_cents: Mapped[int] = mapped_column(
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

    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    terms: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # Flexible terms storage

    # Optional link to a podcast
    podcast_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="sponsorships")
    deliverables: Mapped[List["SponsorshipDeliverable"]] = relationship(
        "SponsorshipDeliverable", back_populates="sponsorship",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Sponsorship {self.brand_name} - {self.status}>"


class SponsorshipDeliverable(Base, UUIDMixin, TimestampMixin):
    """
    Individual deliverable within a sponsorship deal.
    """

    __tablename__ = "sponsorship_deliverables"

    sponsorship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sponsorships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )  # post, story, video, mention, review

    platform: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # instagram, youtube, tiktok, etc.

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, in_progress, completed, overdue

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    content_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )  # Link to published content

    # Relationships
    sponsorship: Mapped["Sponsorship"] = relationship(
        "Sponsorship", back_populates="deliverables",
    )

    def __repr__(self) -> str:
        return f"<SponsorshipDeliverable {self.type} on {self.platform} - {self.status}>"
