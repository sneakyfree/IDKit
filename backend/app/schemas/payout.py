"""
Payout Schemas

Pydantic schemas for payout API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class ConnectAccountStatusEnum(str, Enum):
    """Status of a Stripe Connect account."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DISABLED = "disabled"


class AccountRequirements(BaseModel):
    """Stripe account requirements."""

    currently_due: List[str] = []
    eventually_due: List[str] = []
    pending_verification: List[str] = []


class ConnectAccountResponse(BaseModel):
    """Response for Connect account status."""

    id: str
    stripe_account_id: str
    status: ConnectAccountStatusEnum
    details_submitted: bool
    charges_enabled: bool
    payouts_enabled: bool
    country: str
    default_currency: str
    requirements: Optional[AccountRequirements] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingLinkResponse(BaseModel):
    """Response containing onboarding URL."""

    url: str
    expires_at: Optional[datetime] = None


class BalanceAmount(BaseModel):
    """Amount with currency."""

    amount_cents: int
    currency: str

    @property
    def amount_dollars(self) -> float:
        """Convert cents to dollars."""
        return self.amount_cents / 100


class BalanceResponse(BaseModel):
    """Response for account balance."""

    available: List[BalanceAmount]
    pending: List[BalanceAmount]
    total_available_cents: int
    total_pending_cents: int


class TransferResponse(BaseModel):
    """Response for a single transfer."""

    id: str
    stripe_transfer_id: str
    amount_cents: int
    currency: str
    status: str
    description: Optional[str] = None
    source_type: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayoutResponse(BaseModel):
    """Response for a single payout."""

    id: str
    stripe_payout_id: str
    amount_cents: int
    currency: str
    status: str
    arrival_date: Optional[datetime] = None
    failure_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PayoutHistoryResponse(BaseModel):
    """Response for payout history."""

    transfers: List[TransferResponse]
    payouts: List[PayoutResponse]
    total_transferred_cents: int
    total_paid_out_cents: int


class InitiatePayoutRequest(BaseModel):
    """Request to initiate a payout."""

    amount_cents: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", max_length=3)


class InitiatePayoutResponse(BaseModel):
    """Response after initiating a payout."""

    payout_id: str
    amount_cents: int
    currency: str
    status: str
    estimated_arrival: Optional[datetime] = None
