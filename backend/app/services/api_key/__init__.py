"""
API Key Service

Business logic for developer API key management.
"""

import uuid
import secrets
import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import APIKey


class ApiKeyService:
    """Service for API key creation, validation, and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_key(
        self,
        user_id: uuid.UUID,
        name: str,
        scopes: list[str],
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns (key_object, plaintext_key).
        The plaintext key is only returned once at creation time.
        """
        # Generate a random key
        plaintext_key = f"idkit_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        key_prefix = plaintext_key[:12]

        api_key = APIKey(
            name=name,
            key=key_hash,
            organization_id=None,  # Individual user key
        )
        # Store scopes and metadata
        api_key.key = key_hash  # Override the key field with hash

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key, plaintext_key

    async def list_keys(
        self, limit: int = 50
    ) -> list[APIKey]:
        """List all API keys."""
        query = (
            select(APIKey)
            .order_by(APIKey.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def revoke_key(self, key_id: uuid.UUID) -> bool:
        """Revoke an API key."""
        query = select(APIKey).where(APIKey.id == key_id)
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()
        if not api_key:
            return False
        api_key.is_active = False
        await self.db.commit()
        return True

    async def validate_key(self, plaintext_key: str) -> Optional[APIKey]:
        """Validate a key and return the associated APIKey."""
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        query = select(APIKey).where(
            APIKey.key == key_hash,
            APIKey.is_active == True,
        )
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            await self.db.commit()
        return api_key
