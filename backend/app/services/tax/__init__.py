"""
Tax Documentation Service

Business logic for tax profile management and document generation.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax import TaxProfile, TaxDocument


class TaxService:
    """Service for tax profile and document management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> Optional[TaxProfile]:
        """Get tax profile for a user."""
        query = select(TaxProfile).where(TaxProfile.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        user_id: uuid.UUID,
        business_type: Optional[str] = None,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        address: Optional[dict] = None,
    ) -> TaxProfile:
        """Create or update tax profile."""
        profile = await self.get_profile(user_id)

        if not profile:
            profile = TaxProfile(user_id=user_id)
            self.db.add(profile)

        if business_type is not None:
            profile.business_type = business_type
        if legal_name is not None:
            profile.legal_name = legal_name
        if tax_id is not None:
            # Encrypt tax ID — in production use Fernet, here we store hashed
            profile.tax_id_last4 = tax_id[-4:] if len(tax_id) >= 4 else tax_id
            # Simple encryption placeholder — replace with Fernet in production
            profile.tax_id_encrypted = hashlib.sha256(
                tax_id.encode()
            ).hexdigest()
        if address is not None:
            profile.address = address

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def submit_w9(self, user_id: uuid.UUID) -> TaxProfile:
        """Mark W-9 as submitted."""
        profile = await self.get_profile(user_id)
        if not profile:
            profile = TaxProfile(user_id=user_id)
            self.db.add(profile)
        profile.w9_submitted = True
        profile.w9_submitted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def list_documents(
        self,
        user_id: uuid.UUID,
        year: Optional[int] = None,
    ) -> list[TaxDocument]:
        """List tax documents for a user."""
        query = (
            select(TaxDocument)
            .where(TaxDocument.user_id == user_id)
            .order_by(TaxDocument.year.desc())
        )
        if year:
            query = query.where(TaxDocument.year == year)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def generate_document(
        self,
        user_id: uuid.UUID,
        type: str,
        year: int,
        total_amount_cents: int,
    ) -> TaxDocument:
        """Generate a tax document."""
        doc = TaxDocument(
            user_id=user_id,
            type=type,
            year=year,
            total_amount_cents=total_amount_cents,
            status="generated",
            generated_at=datetime.utcnow(),
            file_path=f"tax/{user_id}/{type}_{year}.pdf",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc
