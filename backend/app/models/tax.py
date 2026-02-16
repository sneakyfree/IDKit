"""
Tax Documentation Models

Database models for tax profile and document management.
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

if TYPE_CHECKING:
    from app.models.user import User


class TaxProfile(Base, UUIDMixin, TimestampMixin):
    """
    User's tax information profile.

    Tax IDs are stored encrypted at rest.
    """

    __tablename__ = "tax_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    business_type: Mapped[str] = mapped_column(
        String(50), default="individual", nullable=False,
    )  # individual, sole_proprietor, llc, corporation, partnership

    legal_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )

    # Encrypted tax ID (EIN or SSN)
    tax_id_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    # Last 4 digits for display (unencrypted)
    tax_id_last4: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True,
    )

    address: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # {street, city, state, zip, country}

    w9_submitted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    w9_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="tax_profile")

    def __repr__(self) -> str:
        return f"<TaxProfile {self.business_type} - ****{self.tax_id_last4}>"


class TaxDocument(Base, UUIDMixin, TimestampMixin):
    """
    Tax document (1099, W-9, etc.).
    """

    __tablename__ = "tax_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # 1099-NEC, 1099-K, W-9

    year: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, generated, sent, filed

    file_path: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )  # S3 path to document

    total_amount_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="tax_documents")

    def __repr__(self) -> str:
        return f"<TaxDocument {self.type} {self.year} - {self.status}>"
