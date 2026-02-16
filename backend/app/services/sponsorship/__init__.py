"""
Sponsorship Service

Business logic for managing brand sponsorships and deliverables.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sponsorship import Sponsorship, SponsorshipDeliverable


class SponsorshipService:
    """Service for sponsorship CRUD and deliverable management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        brand_name: str,
        value_cents: int = 0,
        brand_logo_url: Optional[str] = None,
        brand_contact_email: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        terms: Optional[dict] = None,
        podcast_id: Optional[uuid.UUID] = None,
    ) -> Sponsorship:
        """Create a new sponsorship deal."""
        sponsorship = Sponsorship(
            user_id=user_id,
            brand_name=brand_name,
            value_cents=value_cents,
            brand_logo_url=brand_logo_url,
            brand_contact_email=brand_contact_email,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            terms=terms or {},
            podcast_id=podcast_id,
        )
        self.db.add(sponsorship)
        await self.db.commit()
        await self.db.refresh(sponsorship)
        return sponsorship

    async def list_sponsorships(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships for a user, with optional status filter."""
        query = (
            select(Sponsorship)
            .where(Sponsorship.user_id == user_id)
            .options(selectinload(Sponsorship.deliverables))
            .order_by(Sponsorship.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Sponsorship.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, sponsorship_id: uuid.UUID) -> Optional[Sponsorship]:
        """Get a sponsorship by ID."""
        query = (
            select(Sponsorship)
            .where(Sponsorship.id == sponsorship_id)
            .options(selectinload(Sponsorship.deliverables))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, sponsorship_id: uuid.UUID, **kwargs
    ) -> Optional[Sponsorship]:
        """Update a sponsorship."""
        sponsorship = await self.get(sponsorship_id)
        if not sponsorship:
            return None
        for key, value in kwargs.items():
            if hasattr(sponsorship, key) and value is not None:
                setattr(sponsorship, key, value)
        await self.db.commit()
        await self.db.refresh(sponsorship)
        return sponsorship

    async def delete(self, sponsorship_id: uuid.UUID) -> bool:
        """Delete a sponsorship."""
        sponsorship = await self.get(sponsorship_id)
        if not sponsorship:
            return False
        await self.db.delete(sponsorship)
        await self.db.commit()
        return True

    async def add_deliverable(
        self,
        sponsorship_id: uuid.UUID,
        type: str,
        platform: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> SponsorshipDeliverable:
        """Add a deliverable to a sponsorship."""
        deliverable = SponsorshipDeliverable(
            sponsorship_id=sponsorship_id,
            type=type,
            platform=platform,
            description=description,
            due_date=due_date,
        )
        self.db.add(deliverable)
        await self.db.commit()
        await self.db.refresh(deliverable)
        return deliverable

    async def update_deliverable_status(
        self,
        deliverable_id: uuid.UUID,
        status: str,
    ) -> Optional[SponsorshipDeliverable]:
        """Update a deliverable's status."""
        query = select(SponsorshipDeliverable).where(
            SponsorshipDeliverable.id == deliverable_id
        )
        result = await self.db.execute(query)
        deliverable = result.scalar_one_or_none()
        if not deliverable:
            return None
        deliverable.status = status
        if status == "completed":
            deliverable.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(deliverable)
        return deliverable

    async def get_analytics(self, user_id: uuid.UUID) -> dict:
        """Get sponsorship analytics for a user."""
        query = select(Sponsorship).where(Sponsorship.user_id == user_id)
        result = await self.db.execute(query)
        sponsorships = list(result.scalars().all())

        total_value = sum(s.value_cents for s in sponsorships)
        active_count = sum(1 for s in sponsorships if s.status == "active")
        completed_count = sum(1 for s in sponsorships if s.status == "completed")

        return {
            "total_sponsorships": len(sponsorships),
            "active_sponsorships": active_count,
            "completed_sponsorships": completed_count,
            "total_value_cents": total_value,
            "average_value_cents": total_value // max(len(sponsorships), 1),
        }
