"""
Tax Documentation API

Real endpoints replacing stubs for FEAT-057.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.tax import TaxService

router = APIRouter(prefix="/tax", tags=["Tax"])


# ---- Schemas ----

class TaxProfileUpdate(BaseModel):
    business_type: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[dict] = None


class TaxDocGenerate(BaseModel):
    type: str = Field(description="Document type: 1099-NEC, 1099-K, W-9")
    year: int = Field(ge=2020, le=2030)
    total_amount_cents: int = Field(ge=0)


# ---- Routes ----

@router.get("/profile")
async def get_tax_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's tax profile."""
    service = TaxService(db)
    profile = await service.get_profile(current_user.id)
    if not profile:
        return {"profile": None, "w9_submitted": False}
    return profile.to_dict()


@router.put("/profile")
async def update_tax_profile(
    data: TaxProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update tax profile."""
    service = TaxService(db)
    profile = await service.update_profile(
        user_id=current_user.id,
        **data.model_dump(exclude_unset=True),
    )
    return profile.to_dict()


@router.post("/profile/w9")
async def submit_w9(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark W-9 as submitted."""
    service = TaxService(db)
    profile = await service.submit_w9(current_user.id)
    return {"w9_submitted": True, "w9_submitted_at": profile.w9_submitted_at}


@router.get("/documents")
async def list_tax_documents(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tax documents."""
    service = TaxService(db)
    documents = await service.list_documents(current_user.id, year=year)
    return {"documents": [d.to_dict() for d in documents], "total": len(documents)}


@router.post("/documents/generate")
async def generate_tax_document(
    data: TaxDocGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a tax document."""
    service = TaxService(db)
    doc = await service.generate_document(
        user_id=current_user.id,
        type=data.type,
        year=data.year,
        total_amount_cents=data.total_amount_cents,
    )
    return doc.to_dict()
