"""
Contract Management API

Real endpoints replacing stubs for FEAT-058/078.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.contract import ContractService

router = APIRouter(prefix="/contracts", tags=["Contracts"])


# ---- Schemas ----

class ContractCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    brand_name: str = Field(min_length=1, max_length=255)
    value_cents: int = Field(default=0, ge=0)
    terms_text: Optional[str] = None
    expires_at: Optional[datetime] = None
    template_id: Optional[uuid.UUID] = None
    variables: Optional[dict] = None


class ContractFromTemplate(BaseModel):
    template_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    brand_name: str = Field(min_length=1, max_length=255)
    variables: dict
    value_cents: int = Field(default=0, ge=0)


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    value_cents: Optional[int] = None
    terms_text: Optional[str] = None
    expires_at: Optional[datetime] = None


class DeliverableCreate(BaseModel):
    description: str = Field(min_length=1)
    due_date: Optional[datetime] = None


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    content_template: str = Field(min_length=1)
    category: str = "general"
    description: Optional[str] = None
    variables_schema: Optional[dict] = None


# ---- Contract Routes ----

@router.get("")
async def list_contracts(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's contracts."""
    service = ContractService(db)
    contracts = await service.list_contracts(current_user.id, status=status)
    return {"contracts": [c.to_dict() for c in contracts], "total": len(contracts)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
    service = ContractService(db)
    contract = await service.create(user_id=current_user.id, **data.model_dump())
    return contract.to_dict()


@router.post("/from-template", status_code=status.HTTP_201_CREATED)
async def create_from_template(
    data: ContractFromTemplate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a contract from a template."""
    service = ContractService(db)
    try:
        contract = await service.from_template(
            user_id=current_user.id, **data.model_dump()
        )
        return contract.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{contract_id}")
async def get_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a contract by ID."""
    service = ContractService(db)
    contract = await service.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return contract.to_dict()


@router.patch("/{contract_id}")
async def update_contract(
    contract_id: uuid.UUID,
    data: ContractUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a contract."""
    service = ContractService(db)
    existing = await service.get(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = await service.update(contract_id, **data.model_dump(exclude_unset=True))
    return updated.to_dict()


@router.post("/{contract_id}/sign")
async def sign_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sign/activate a contract."""
    service = ContractService(db)
    existing = await service.get(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    contract = await service.sign(contract_id)
    return contract.to_dict()


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a contract."""
    service = ContractService(db)
    existing = await service.get(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await service.delete(contract_id)


# ---- Deliverable Routes ----

@router.post("/{contract_id}/deliverables", status_code=status.HTTP_201_CREATED)
async def add_deliverable(
    contract_id: uuid.UUID,
    data: DeliverableCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a deliverable to a contract."""
    service = ContractService(db)
    existing = await service.get(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    deliverable = await service.add_deliverable(contract_id, **data.model_dump())
    return deliverable.to_dict()


# ---- Template Routes ----

@router.get("/templates/list")
async def list_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available contract templates."""
    service = ContractService(db)
    templates = await service.list_templates(category=category)
    return {"templates": [t.to_dict() for t in templates], "total": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID."""
    service = ContractService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a contract template."""
    service = ContractService(db)
    template = await service.create_template(
        created_by=current_user.id, **data.model_dump()
    )
    return template.to_dict()
