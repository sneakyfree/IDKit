"""
Payment Models

Database models for subscription and payment management.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class SubscriptionTier(str):
    """Subscription tier constants."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str):
    """Subscription status constants."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class PaymentStatus(str):
    """Payment status constants."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    CANCELED = "canceled"


class SubscriptionPlan(Base, UUIDMixin, TimestampMixin):
    """
    Available subscription plans.

    Stores plan configuration synced with Stripe Products/Prices.
    """

    __tablename__ = "subscription_plans"

    # Plan identification
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # free, starter, pro, business, enterprise

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Stripe integration
    stripe_product_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    stripe_price_id_monthly: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    stripe_price_id_yearly: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    # Pricing
    price_monthly: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )  # In cents

    price_yearly: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )  # In cents

    currency: Mapped[str] = mapped_column(
        String(3),
        default="usd",
        nullable=False,
    )

    # Features and limits
    features: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    # Example: {"ai_twins": 1, "monthly_videos": 10, "storage_gb": 5}

    limits: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    # Example: {"max_ai_twins": 1, "max_videos_per_month": 10}

    # Display
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_popular: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Trial
    trial_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SubscriptionPlan {self.name} ({self.tier})>"


class Subscription(Base, UUIDMixin, TimestampMixin):
    """
    User subscriptions.

    Tracks active subscription status synced with Stripe Subscriptions.
    """

    __tablename__ = "subscriptions"

    # User reference
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Plan reference
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id"),
        nullable=False,
    )

    # Stripe integration
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Billing period
    billing_interval: Mapped[str] = mapped_column(
        String(20),
        default="monthly",
        nullable=False,
    )  # monthly, yearly

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Trial
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="subscriptions",
    )

    plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan",
        backref="subscriptions",
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.user_id} - {self.status}>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        ]


class PaymentMethod(Base, UUIDMixin, TimestampMixin):
    """
    Stored payment methods.

    References Stripe PaymentMethod objects.
    """

    __tablename__ = "payment_methods"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe reference
    stripe_payment_method_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Type info
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # card, bank_account, etc.

    # Card details (if card)
    card_brand: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # visa, mastercard, etc.

    card_last4: Mapped[Optional[str]] = mapped_column(
        String(4),
        nullable=True,
    )

    card_exp_month: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    card_exp_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Status
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="payment_methods",
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod {self.type} ****{self.card_last4}>"


class Payment(Base, UUIDMixin, TimestampMixin):
    """
    Payment transactions.

    Records all payments made via Stripe.
    """

    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Stripe reference
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    stripe_charge_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    # Amount
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # In cents

    currency: Mapped[str] = mapped_column(
        String(3),
        default="usd",
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Refund tracking
    refunded_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Receipt
    receipt_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="payments",
    )

    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        backref="payments",
    )

    def __repr__(self) -> str:
        return f"<Payment {self.amount} {self.currency} - {self.status}>"


class UsageRecord(Base, UUIDMixin, TimestampMixin):
    """
    Usage tracking for metered billing.

    Tracks feature usage for usage-based billing.
    """

    __tablename__ = "usage_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Feature being tracked
    feature: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # ai_video_generation, voice_synthesis, etc.

    # Quantity used
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Billing period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Stripe metered billing
    stripe_usage_record_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    # Example: {"video_id": "...", "duration_seconds": 60}

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="usage_records",
    )

    def __repr__(self) -> str:
        return f"<UsageRecord {self.feature} x{self.quantity}>"


class Invoice(Base, UUIDMixin, TimestampMixin):
    """
    Invoice records.

    Mirrors Stripe Invoice objects.
    """

    __tablename__ = "invoices"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Stripe reference
    stripe_invoice_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Invoice details
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # draft, open, paid, void, uncollectible

    # Amounts
    amount_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount_paid: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    amount_remaining: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="usd",
        nullable=False,
    )

    # Dates
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # URLs
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    invoice_pdf: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        backref="invoices",
    )

    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        backref="invoices",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.status}>"
