"""
Developer API Keys API

Real endpoints replacing stubs for FEAT-083.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.api_key import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# ---- Schemas ----

class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(min_length=1)


# ---- Routes ----

@router.get("")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys."""
    service = ApiKeyService(db)
    keys = await service.list_keys()
    return {"keys": [k.to_dict() for k in keys], "total": len(keys)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. Returns the plaintext secret ONCE."""
    service = ApiKeyService(db)
    api_key, secret = await service.create_key(
        user_id=current_user.id, name=data.name, scopes=data.scopes
    )
    return {
        "key": api_key.to_dict(),
        "secret": secret,
        "warning": "Save this secret — it will not be shown again.",
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    service = ApiKeyService(db)
    if not await service.revoke_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
