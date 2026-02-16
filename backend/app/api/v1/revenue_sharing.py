"""
Revenue Sharing API

Real endpoints replacing stubs for FEAT-076.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.revenue_sharing import RevenueSharingService

router = APIRouter(prefix="/revenue-sharing", tags=["Revenue Sharing"])


# ---- Schemas ----

class AgreementCreate(BaseModel):
    partner_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    split_percentage: float = Field(ge=0, le=100)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    terms: Optional[dict] = None


class RevenueRecord(BaseModel):
    amount_cents: int = Field(ge=0)
    period_start: datetime
    period_end: datetime


class StatusUpdate(BaseModel):
    status: str = Field(description="active, paused, completed, cancelled")


# ---- Routes ----

@router.get("")
async def list_agreements(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's revenue sharing agreements."""
    service = RevenueSharingService(db)
    agreements = await service.list_agreements(
        current_user.id, status=status_filter
    )
    return {"agreements": [a.to_dict() for a in agreements], "total": len(agreements)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agreement(
    data: AgreementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new revenue sharing agreement."""
    service = RevenueSharingService(db)
    agreement = await service.create_agreement(
        owner_id=current_user.id, **data.model_dump()
    )
    return agreement.to_dict()


@router.get("/{agreement_id}")
async def get_agreement(
    agreement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an agreement by ID."""
    service = RevenueSharingService(db)
    agreement = await service.get(agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return agreement.to_dict()


@router.post("/{agreement_id}/revenue")
async def record_revenue(
    agreement_id: uuid.UUID,
    data: RevenueRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record revenue and compute distribution."""
    service = RevenueSharingService(db)
    distribution = await service.record_revenue(
        agreement_id=agreement_id, **data.model_dump()
    )
    if not distribution:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return distribution.to_dict()


@router.post("/distributions/{distribution_id}/pay")
async def pay_distribution(
    distribution_id: uuid.UUID,
    stripe_transfer_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a distribution as paid."""
    service = RevenueSharingService(db)
    distribution = await service.pay_distribution(
        distribution_id, stripe_transfer_id=stripe_transfer_id
    )
    if not distribution:
        raise HTTPException(status_code=404, detail="Distribution not found")
    return distribution.to_dict()


@router.patch("/{agreement_id}/status")
async def update_agreement_status(
    agreement_id: uuid.UUID,
    data: StatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update agreement status."""
    service = RevenueSharingService(db)
    agreement = await service.update_status(agreement_id, data.status)
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return agreement.to_dict()
