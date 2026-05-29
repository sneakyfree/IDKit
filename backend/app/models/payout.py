"""
Payout Models

Database models for tracking creator payouts via Stripe Connect.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ConnectAccountStatus(str, Enum):
    """Status of a Stripe Connect account."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DISABLED = "disabled"


class TransferStatus(str, Enum):
    """Status of a transfer to Connect account."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class PayoutStatus(str, Enum):
    """Status of a payout to bank account."""

    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class ConnectAccount(Base):
    """Stripe Connect account for a creator."""

    __tablename__ = "connect_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_account_id = Column(String(255), nullable=False, unique=True, index=True)

    status = Column(
        String(20),
        default=ConnectAccountStatus.PENDING.value,
        nullable=False,
    )

    details_submitted = Column(Integer, default=0)  # Boolean as int
    charges_enabled = Column(Integer, default=0)
    payouts_enabled = Column(Integer, default=0)

    country = Column(String(2), default="US")
    default_currency = Column(String(3), default="usd")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="connect_account")
    transfers = relationship(
        "Transfer", back_populates="connect_account", cascade="all, delete-orphan"
    )
    payouts = relationship(
        "Payout", back_populates="connect_account", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_connect_accounts_user_id", "user_id"),)


class Transfer(Base):
    """Transfer from platform to creator's Connect account."""

    __tablename__ = "transfers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    connect_account_id = Column(
        String(36), ForeignKey("connect_accounts.id"), nullable=False
    )
    stripe_transfer_id = Column(String(255), nullable=False, unique=True, index=True)

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")

    status = Column(
        String(20),
        default=TransferStatus.PENDING.value,
        nullable=False,
    )

    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)  # e.g., "brand_deal", "affiliate"
    source_id = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    connect_account = relationship("ConnectAccount", back_populates="transfers")

    __table_args__ = (
        Index("ix_transfers_connect_account_id", "connect_account_id"),
        Index("ix_transfers_created_at", "created_at"),
    )


class Payout(Base):
    """Payout from Connect account to creator's bank."""

    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    connect_account_id = Column(
        String(36), ForeignKey("connect_accounts.id"), nullable=False
    )
    stripe_payout_id = Column(String(255), nullable=False, unique=True, index=True)

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")

    status = Column(
        String(20),
        default=PayoutStatus.PENDING.value,
        nullable=False,
    )

    arrival_date = Column(DateTime, nullable=True)
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    connect_account = relationship("ConnectAccount", back_populates="payouts")

    __table_args__ = (
        Index("ix_payouts_connect_account_id", "connect_account_id"),
        Index("ix_payouts_created_at", "created_at"),
    )
