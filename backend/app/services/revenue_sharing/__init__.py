"""
Revenue Sharing Service

Business logic for revenue sharing agreements and distributions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.revenue_sharing import RevenueAgreement, RevenueDistribution


class RevenueSharingService:
    """Service for revenue sharing agreement management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agreement(
        self,
        owner_id: uuid.UUID,
        partner_id: uuid.UUID,
        name: str,
        split_percentage: float,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        terms: Optional[dict] = None,
    ) -> RevenueAgreement:
        """Create a new revenue sharing agreement."""
        agreement = RevenueAgreement(
            owner_id=owner_id,
            partner_id=partner_id,
            name=name,
            split_percentage=split_percentage,
            description=description,
            start_date=start_date,
            end_date=end_date,
            terms=terms or {},
        )
        self.db.add(agreement)
        await self.db.commit()
        await self.db.refresh(agreement)
        return agreement

    async def list_agreements(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[RevenueAgreement]:
        """List agreements where user is owner or partner."""
        query = (
            select(RevenueAgreement)
            .where(
                (RevenueAgreement.owner_id == user_id)
                | (RevenueAgreement.partner_id == user_id)
            )
            .options(selectinload(RevenueAgreement.distributions))
            .order_by(RevenueAgreement.created_at.desc())
        )
        if status:
            query = query.where(RevenueAgreement.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get(self, agreement_id: uuid.UUID) -> Optional[RevenueAgreement]:
        """Get an agreement by ID."""
        query = (
            select(RevenueAgreement)
            .where(RevenueAgreement.id == agreement_id)
            .options(selectinload(RevenueAgreement.distributions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def record_revenue(
        self,
        agreement_id: uuid.UUID,
        amount_cents: int,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[RevenueDistribution]:
        """Record revenue and compute distribution."""
        agreement = await self.get(agreement_id)
        if not agreement:
            return None

        # Calculate partner share
        partner_share = int(amount_cents * (agreement.split_percentage / 100))

        distribution = RevenueDistribution(
            agreement_id=agreement_id,
            amount_cents=partner_share,
            period_start=period_start,
            period_end=period_end,
        )
        self.db.add(distribution)

        # Update totals
        agreement.total_earned_cents += amount_cents
        await self.db.commit()
        await self.db.refresh(distribution)
        return distribution

    async def pay_distribution(
        self,
        distribution_id: uuid.UUID,
        stripe_transfer_id: Optional[str] = None,
    ) -> Optional[RevenueDistribution]:
        """Mark a distribution as paid."""
        query = select(RevenueDistribution).where(
            RevenueDistribution.id == distribution_id
        )
        result = await self.db.execute(query)
        distribution = result.scalar_one_or_none()
        if not distribution:
            return None

        distribution.status = "paid"
        distribution.paid_at = datetime.utcnow()
        distribution.stripe_transfer_id = stripe_transfer_id

        # Update agreement total paid
        agreement = await self.get(distribution.agreement_id)
        if agreement:
            agreement.total_paid_cents += distribution.amount_cents

        await self.db.commit()
        await self.db.refresh(distribution)
        return distribution

    async def update_status(
        self, agreement_id: uuid.UUID, status: str
    ) -> Optional[RevenueAgreement]:
        """Update agreement status."""
        agreement = await self.get(agreement_id)
        if not agreement:
            return None
        agreement.status = status
        await self.db.commit()
        await self.db.refresh(agreement)
        return agreement
