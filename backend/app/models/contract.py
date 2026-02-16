"""
Contract Models

Database models for contract and template management.
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


class Contract(Base, UUIDMixin, TimestampMixin):
    """
    Creator contract / agreement.

    Full lifecycle: draft → sent → active → completed.
    """

    __tablename__ = "contracts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    brand_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    brand_contact_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False, index=True,
    )  # draft, sent, active, completed, cancelled

    value_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="usd", nullable=False,
    )

    terms_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contract_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    variables: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # Template variable values

    # Relationships
    user: Mapped["User"] = relationship("User", backref="contracts")
    deliverables: Mapped[List["ContractDeliverable"]] = relationship(
        "ContractDeliverable", back_populates="contract",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Contract {self.title} - {self.status}>"


class ContractTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Reusable contract template.
    """

    __tablename__ = "contract_templates"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(100), default="general", nullable=False, index=True,
    )  # sponsorship, collaboration, licensing, custom

    content_template: Mapped[str] = mapped_column(
        Text, nullable=False,
    )  # Template text with {{variable}} placeholders

    variables_schema: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )  # JSON schema of template variables

    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(
        default=True, nullable=False,
    )  # Available to all users

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ContractTemplate {self.name}>"


class ContractDeliverable(Base, UUIDMixin, TimestampMixin):
    """
    Deliverable linked to a contract.
    """

    __tablename__ = "contract_deliverables"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False,
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, in_progress, completed

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    contract: Mapped["Contract"] = relationship(
        "Contract", back_populates="deliverables",
    )

    def __repr__(self) -> str:
        return f"<ContractDeliverable {self.description[:30]} - {self.status}>"
