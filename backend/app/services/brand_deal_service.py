"""
Brand Deal Service

CRM functionality for tracking brand deals through the pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brand_deals import (
    BrandDeal,
    Contact,
    ContractClause,
    ContractTemplate,
    DealPipelineMetrics,
    DealStage,
    DealType,
    Deliverable,
    DeliverableType,
    NegotiationNote,
    PaymentTerms,
)


# Stage probabilities for forecasting
STAGE_PROBABILITIES = {
    DealStage.LEAD: 0.10,
    DealStage.QUALIFIED: 0.25,
    DealStage.NEGOTIATING: 0.50,
    DealStage.CONTRACT: 0.75,
    DealStage.ACTIVE: 0.90,
    DealStage.COMPLETED: 1.0,
    DealStage.LOST: 0.0,
    DealStage.ON_HOLD: 0.25,
}


class BrandDealService:
    """
    Brand Deal CRM service.
    
    Tracks deals from lead to completion with full pipeline visibility.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deal(
        self,
        user_id: UUID,
        brand_name: str,
        title: str,
        deal_type: DealType,
        deal_value: float,
        description: Optional[str] = None,
        currency: str = "USD",
        expected_close_date: Optional[datetime] = None,
        contacts: Optional[List[Contact]] = None,
    ) -> BrandDeal:
        """Create a new brand deal."""
        deal = BrandDeal(
            deal_id=uuid4(),
            user_id=user_id,
            brand_name=brand_name,
            title=title,
            description=description,
            deal_type=deal_type,
            deal_value=deal_value,
            currency=currency,
            stage=DealStage.LEAD,
            probability=STAGE_PROBABILITIES[DealStage.LEAD],
            expected_close_date=expected_close_date,
            contacts=contacts or [],
            stage_history=[{
                "stage": DealStage.LEAD.value,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Deal created",
            }],
        )

        await self._save_deal(deal)
        return deal

    async def get_deal(
        self,
        deal_id: UUID,
        user_id: UUID,
    ) -> Optional[BrandDeal]:
        """Get a deal by ID."""
        from app.models.revenue import BrandDealRecord

        result = await self.db.execute(
            select(BrandDealRecord).where(
                BrandDealRecord.id == deal_id,
                BrandDealRecord.user_id == user_id,
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._record_to_deal(record)

    async def get_deals_for_user(
        self,
        user_id: UUID,
        stage: Optional[DealStage] = None,
        limit: int = 50,
    ) -> List[BrandDeal]:
        """Get all deals for a user."""
        from app.models.revenue import BrandDealRecord

        query = select(BrandDealRecord).where(
            BrandDealRecord.user_id == user_id
        )

        if stage:
            query = query.where(BrandDealRecord.stage == stage.value)

        query = query.order_by(BrandDealRecord.updated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        records = result.scalars().all()

        return [self._record_to_deal(r) for r in records]

    async def update_stage(
        self,
        deal_id: UUID,
        user_id: UUID,
        new_stage: DealStage,
        note: Optional[str] = None,
    ) -> BrandDeal:
        """Update deal pipeline stage."""
        deal = await self.get_deal(deal_id, user_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        old_stage = deal.stage
        deal.stage = new_stage
        deal.probability = STAGE_PROBABILITIES.get(new_stage, 0.0)
        deal.updated_at = datetime.utcnow()

        # Track stage history
        deal.stage_history.append({
            "stage": new_stage.value,
            "timestamp": datetime.utcnow().isoformat(),
            "previous_stage": old_stage.value,
            "note": note,
        })

        # Mark closed dates
        if new_stage in (DealStage.COMPLETED, DealStage.LOST):
            deal.closed_at = datetime.utcnow()

        await self._update_deal(deal)
        return deal

    async def add_deliverable(
        self,
        deal_id: UUID,
        user_id: UUID,
        deliverable_type: DeliverableType,
        description: str,
        due_date: Optional[datetime] = None,
        requirements: Optional[List[str]] = None,
    ) -> BrandDeal:
        """Add a deliverable to a deal."""
        deal = await self.get_deal(deal_id, user_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        deliverable = Deliverable(
            deliverable_id=uuid4(),
            type=deliverable_type,
            description=description,
            due_date=due_date,
            requirements=requirements or [],
        )

        deal.deliverables.append(deliverable)
        deal.updated_at = datetime.utcnow()

        await self._update_deal(deal)
        return deal

    async def add_note(
        self,
        deal_id: UUID,
        user_id: UUID,
        content: str,
    ) -> BrandDeal:
        """Add a negotiation note to a deal."""
        deal = await self.get_deal(deal_id, user_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        note = NegotiationNote(
            note_id=uuid4(),
            content=content,
            created_by="creator",  # Would get from user
        )

        deal.notes.append(note)
        deal.updated_at = datetime.utcnow()

        await self._update_deal(deal)
        return deal

    async def get_pipeline(
        self,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Get pipeline metrics and deals by stage."""
        deals = await self.get_deals_for_user(user_id)

        # Group by stage
        deals_by_stage: Dict[str, List[BrandDeal]] = {}
        for stage in DealStage:
            deals_by_stage[stage.value] = []

        for deal in deals:
            deals_by_stage[deal.stage.value].append(deal)

        # Calculate metrics
        metrics = self._calculate_metrics(deals)

        return {
            "metrics": metrics,
            "deals_by_stage": deals_by_stage,
        }

    def _calculate_metrics(
        self,
        deals: List[BrandDeal],
    ) -> DealPipelineMetrics:
        """Calculate pipeline metrics."""
        total_value = sum(d.deal_value for d in deals)
        
        # By stage
        by_stage = {}
        for stage in DealStage:
            stage_deals = [d for d in deals if d.stage == stage]
            by_stage[stage.value] = {
                "count": len(stage_deals),
                "value": sum(d.deal_value for d in stage_deals),
                "weighted_value": sum(d.deal_value * d.probability for d in stage_deals),
            }

        # Win rate
        completed = [d for d in deals if d.stage == DealStage.COMPLETED]
        lost = [d for d in deals if d.stage == DealStage.LOST]
        closed = len(completed) + len(lost)
        win_rate = len(completed) / closed if closed > 0 else 0.0

        # Average deal size
        avg_deal_size = total_value / len(deals) if deals else 0.0

        # This month's activity
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        closed_this_month = [
            d for d in completed
            if d.closed_at and d.closed_at >= month_start
        ]

        return DealPipelineMetrics(
            total_deals=len(deals),
            total_value=total_value,
            by_stage=by_stage,
            win_rate=win_rate,
            avg_deal_size=avg_deal_size,
            avg_sales_cycle_days=14.0,  # Would calculate from actual data
            deals_closed_this_month=len(closed_this_month),
            revenue_this_month=sum(d.deal_value for d in closed_this_month),
        )

    async def get_contract_templates(
        self,
        deal_type: Optional[DealType] = None,
    ) -> List[ContractTemplate]:
        """Get available contract templates."""
        templates = [
            ContractTemplate(
                template_id=uuid4(),
                name="Standard Sponsored Post Agreement",
                description="Basic terms for a single sponsored post",
                deal_type=DealType.SPONSORED_POST,
                clauses=[
                    ContractClause(
                        clause_id="scope",
                        title="Scope of Work",
                        content="Creator agrees to produce [DELIVERABLE_COUNT] sponsored [CONTENT_TYPE](s)...",
                        category="scope",
                    ),
                    ContractClause(
                        clause_id="payment",
                        title="Payment Terms",
                        content="Brand agrees to pay Creator $[DEAL_VALUE] per the following schedule...",
                        category="payment",
                    ),
                    ContractClause(
                        clause_id="rights",
                        title="Usage Rights",
                        content="Brand receives a [LICENSE_PERIOD] license to use the content...",
                        category="rights",
                        is_negotiable=True,
                    ),
                ],
                variables=["brand_name", "deal_value", "deliverable_count", "content_type", "license_period"],
                is_default=True,
            ),
        ]

        if deal_type:
            return [t for t in templates if t.deal_type == deal_type]

        return templates

    async def _save_deal(self, deal: BrandDeal) -> None:
        """Save a new deal to database."""
        from app.models.revenue import BrandDealRecord

        record = BrandDealRecord(
            id=deal.deal_id,
            user_id=deal.user_id,
            brand_name=deal.brand_name,
            brand_logo_url=deal.brand_logo_url,
            brand_website=deal.brand_website,
            title=deal.title,
            description=deal.description,
            deal_type=deal.deal_type.value,
            deal_value=deal.deal_value,
            currency=deal.currency,
            payment_terms=deal.payment_terms.value,
            stage=deal.stage.value,
            probability=deal.probability,
            expected_close_date=deal.expected_close_date,
            contacts=[c.model_dump() for c in deal.contacts],
            deliverables=[d.model_dump() for d in deal.deliverables],
            notes=[n.model_dump() for n in deal.notes],
            stage_history=deal.stage_history,
            tags=deal.tags,
        )

        self.db.add(record)
        await self.db.flush()

    async def _update_deal(self, deal: BrandDeal) -> None:
        """Update existing deal in database."""
        from app.models.revenue import BrandDealRecord

        result = await self.db.execute(
            select(BrandDealRecord).where(
                BrandDealRecord.id == deal.deal_id
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.brand_name = deal.brand_name
            record.title = deal.title
            record.description = deal.description
            record.deal_value = deal.deal_value
            record.stage = deal.stage.value
            record.probability = deal.probability
            record.contacts = [c.model_dump() for c in deal.contacts]
            record.deliverables = [d.model_dump() for d in deal.deliverables]
            record.notes = [n.model_dump() for n in deal.notes]
            record.stage_history = deal.stage_history
            record.closed_at = deal.closed_at
            record.updated_at = datetime.utcnow()

            await self.db.flush()

    def _record_to_deal(self, record: Any) -> BrandDeal:
        """Convert database record to BrandDeal."""
        return BrandDeal(
            deal_id=record.id,
            user_id=record.user_id,
            brand_name=record.brand_name,
            brand_logo_url=record.brand_logo_url,
            brand_website=record.brand_website,
            title=record.title,
            description=record.description,
            deal_type=DealType(record.deal_type),
            deal_value=record.deal_value,
            currency=record.currency,
            payment_terms=PaymentTerms(record.payment_terms) if record.payment_terms else PaymentTerms.NET_30,
            stage=DealStage(record.stage),
            probability=record.probability or 0.0,
            expected_close_date=record.expected_close_date,
            contacts=[Contact(**c) for c in (record.contacts or [])],
            deliverables=[Deliverable(**d) for d in (record.deliverables or [])],
            notes=[NegotiationNote(**n) for n in (record.notes or [])],
            stage_history=record.stage_history or [],
            tags=record.tags or [],
            created_at=record.created_at,
            updated_at=record.updated_at,
            closed_at=record.closed_at,
        )
