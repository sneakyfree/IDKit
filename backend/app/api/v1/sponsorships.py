"""
Sponsorship Management API

Real endpoints replacing stubs for FEAT-052.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.sponsorship import SponsorshipService

router = APIRouter(prefix="/sponsorships", tags=["Sponsorships"])


# ---- Schemas ----

class SponsorshipCreate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=255)
    value_cents: int = Field(default=0, ge=0)
    brand_logo_url: Optional[str] = None
    brand_contact_email: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    terms: Optional[dict] = None
    podcast_id: Optional[uuid.UUID] = None


class SponsorshipUpdate(BaseModel):
    brand_name: Optional[str] = None
    status: Optional[str] = None
    value_cents: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    terms: Optional[dict] = None


class DeliverableCreate(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    platform: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class DeliverableStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=50)


class SponsorshipResponse(BaseModel):
    id: uuid.UUID
    brand_name: str
    status: str
    value_cents: int
    currency: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    deliverables: List[dict] = []

    class Config:
        from_attributes = True


# ---- Routes ----

@router.get("")
async def list_sponsorships(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's sponsorships."""
    service = SponsorshipService(db)
    sponsorships = await service.list_sponsorships(
        user_id=current_user.id, status=status, limit=limit, offset=offset
    )
    return {"sponsorships": [s.to_dict() for s in sponsorships], "total": len(sponsorships)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sponsorship(
    data: SponsorshipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sponsorship deal."""
    service = SponsorshipService(db)
    sponsorship = await service.create(
        user_id=current_user.id,
        **data.model_dump(),
    )
    return sponsorship.to_dict()


@router.get("/{sponsorship_id}")
async def get_sponsorship(
    sponsorship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a sponsorship by ID."""
    service = SponsorshipService(db)
    sponsorship = await service.get(sponsorship_id)
    if not sponsorship:
        raise HTTPException(status_code=404, detail="Sponsorship not found")
    if sponsorship.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return sponsorship.to_dict()


@router.patch("/{sponsorship_id}")
async def update_sponsorship(
    sponsorship_id: uuid.UUID,
    data: SponsorshipUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a sponsorship."""
    service = SponsorshipService(db)
    existing = await service.get(sponsorship_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsorship not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = await service.update(sponsorship_id, **data.model_dump(exclude_unset=True))
    return updated.to_dict()


@router.delete("/{sponsorship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sponsorship(
    sponsorship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a sponsorship."""
    service = SponsorshipService(db)
    existing = await service.get(sponsorship_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsorship not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await service.delete(sponsorship_id)


@router.post("/{sponsorship_id}/deliverables", status_code=status.HTTP_201_CREATED)
async def add_deliverable(
    sponsorship_id: uuid.UUID,
    data: DeliverableCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a deliverable to a sponsorship."""
    service = SponsorshipService(db)
    existing = await service.get(sponsorship_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Sponsorship not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    deliverable = await service.add_deliverable(sponsorship_id, **data.model_dump())
    return deliverable.to_dict()


@router.patch("/deliverables/{deliverable_id}/status")
async def update_deliverable_status(
    deliverable_id: uuid.UUID,
    data: DeliverableStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deliverable's status."""
    service = SponsorshipService(db)
    deliverable = await service.update_deliverable_status(deliverable_id, data.status)
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return deliverable.to_dict()


@router.get("/analytics/summary")
async def get_sponsorship_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sponsorship analytics summary."""
    service = SponsorshipService(db)
    return await service.get_analytics(current_user.id)
