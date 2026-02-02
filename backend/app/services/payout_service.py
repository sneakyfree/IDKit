"""
Payout Service

Stripe Connect integration for multi-platform revenue aggregation.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.revenue import (
    PayoutSummary,
    Platform,
    RevenueEntry,
    RevenueSource,
    RevenueStream,
)


class PayoutService:
    """
    Payout service with Stripe Connect integration.
    
    Aggregates revenue from all platforms into unified dashboard.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY", "")

    async def get_payout_summary(
        self,
        user_id: UUID,
        period: str = "30d",
    ) -> PayoutSummary:
        """
        Get unified payout summary across all revenue streams.
        """
        # Parse period
        period_start, period_end = self._parse_period(period)

        # Get all revenue entries
        entries = await self._get_revenue_entries(user_id, period_start, period_end)

        # Aggregate by source
        by_source = self._aggregate_by_source(entries, period_start, period_end)
        by_platform = self._aggregate_by_platform(entries, period_start, period_end)

        # Calculate totals
        total_gross = sum(e.gross_amount for e in entries)
        total_net = sum(e.net_amount for e in entries)
        
        paid_entries = [e for e in entries if e.paid_at is not None]
        pending_entries = [e for e in entries if e.paid_at is None]
        
        total_paid = sum(e.net_amount for e in paid_entries)
        total_pending = sum(e.net_amount for e in pending_entries)

        # Get top deals
        top_deals = self._get_top_deals(entries)

        # Check Stripe status
        stripe_connected = await self._check_stripe_connected(user_id)
        next_payout = await self._get_next_payout(user_id)

        return PayoutSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            total_gross=total_gross,
            total_net=total_net,
            total_pending=total_pending,
            total_paid=total_paid,
            by_source=by_source,
            by_platform=by_platform,
            top_deals=top_deals,
            stripe_connected=stripe_connected,
            next_payout_date=next_payout.get("date"),
            next_payout_amount=next_payout.get("amount"),
        )

    async def record_revenue(
        self,
        user_id: UUID,
        source: RevenueSource,
        gross_amount: float,
        net_amount: float,
        description: str,
        platform: Optional[Platform] = None,
        earned_at: Optional[datetime] = None,
        external_id: Optional[str] = None,
        brand_deal_id: Optional[UUID] = None,
    ) -> RevenueEntry:
        """Record a new revenue entry."""
        entry = RevenueEntry(
            entry_id=uuid4(),
            user_id=user_id,
            source=source,
            platform=platform,
            description=description,
            gross_amount=gross_amount,
            net_amount=net_amount,
            earned_at=earned_at or datetime.utcnow(),
            external_id=external_id,
            brand_deal_id=brand_deal_id,
        )

        await self._save_entry(entry)
        return entry

    async def process_payout(
        self,
        user_id: UUID,
        amount: float,
        currency: str = "USD",
    ) -> Dict[str, Any]:
        """
        Process payout to creator via Stripe Connect.
        """
        if not self.stripe_api_key:
            return {
                "success": False,
                "error": "Stripe not configured",
            }

        try:
            # Get user's Stripe account
            stripe_account_id = await self._get_stripe_account(user_id)
            
            if not stripe_account_id:
                return {
                    "success": False,
                    "error": "Stripe account not connected",
                }

            # Create transfer (placeholder - would use Stripe SDK)
            transfer_id = f"tr_{uuid4().hex[:24]}"
            
            # Record the payout
            await self._record_payout(
                user_id=user_id,
                amount=amount,
                currency=currency,
                stripe_transfer_id=transfer_id,
            )

            return {
                "success": True,
                "transfer_id": transfer_id,
                "amount": amount,
                "currency": currency,
                "estimated_arrival": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def get_payout_history(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get payout transaction history."""
        from app.models.revenue import PayoutRecord

        result = await self.db.execute(
            select(PayoutRecord).where(
                PayoutRecord.user_id == user_id
            ).order_by(
                PayoutRecord.created_at.desc()
            ).limit(limit)
        )
        records = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "amount": r.amount,
                "currency": r.currency,
                "status": r.status,
                "stripe_transfer_id": r.stripe_transfer_id,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ]

    async def connect_stripe_account(
        self,
        user_id: UUID,
    ) -> Dict[str, str]:
        """
        Generate Stripe Connect onboarding URL.
        """
        # Would use Stripe SDK to create account link
        return {
            "url": f"https://connect.stripe.com/setup/s/test_onboarding_{user_id.hex[:8]}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

    def _parse_period(self, period: str) -> tuple[datetime, datetime]:
        """Parse period string to date range."""
        now = datetime.utcnow()
        end = now

        if period == "7d":
            start = now - timedelta(days=7)
        elif period == "30d":
            start = now - timedelta(days=30)
        elif period == "90d":
            start = now - timedelta(days=90)
        elif period == "ytd":
            start = datetime(now.year, 1, 1)
        elif period == "all":
            start = datetime(2020, 1, 1)
        else:
            start = now - timedelta(days=30)

        return start, end

    async def _get_revenue_entries(
        self,
        user_id: UUID,
        start: datetime,
        end: datetime,
    ) -> List[RevenueEntry]:
        """Get revenue entries for period."""
        from app.models.revenue import RevenueEntryRecord

        result = await self.db.execute(
            select(RevenueEntryRecord).where(
                RevenueEntryRecord.user_id == user_id,
                RevenueEntryRecord.earned_at >= start,
                RevenueEntryRecord.earned_at <= end,
            ).order_by(
                RevenueEntryRecord.earned_at.desc()
            )
        )
        records = result.scalars().all()

        return [
            RevenueEntry(
                entry_id=r.id,
                user_id=r.user_id,
                source=RevenueSource(r.source),
                platform=Platform(r.platform) if r.platform else None,
                description=r.description,
                gross_amount=r.gross_amount,
                net_amount=r.net_amount,
                earned_at=r.earned_at,
                paid_at=r.paid_at,
                external_id=r.external_id,
                brand_deal_id=r.brand_deal_id,
            )
            for r in records
        ]

    def _aggregate_by_source(
        self,
        entries: List[RevenueEntry],
        start: datetime,
        end: datetime,
    ) -> List[RevenueStream]:
        """Aggregate revenue by source."""
        aggregated: Dict[str, Dict] = {}

        for entry in entries:
            key = entry.source.value
            if key not in aggregated:
                aggregated[key] = {
                    "gross": 0,
                    "net": 0,
                    "count": 0,
                }
            aggregated[key]["gross"] += entry.gross_amount
            aggregated[key]["net"] += entry.net_amount
            aggregated[key]["count"] += 1

        return [
            RevenueStream(
                source=RevenueSource(source),
                total_gross=data["gross"],
                total_net=data["net"],
                count=data["count"],
                period_start=start,
                period_end=end,
            )
            for source, data in aggregated.items()
        ]

    def _aggregate_by_platform(
        self,
        entries: List[RevenueEntry],
        start: datetime,
        end: datetime,
    ) -> List[RevenueStream]:
        """Aggregate revenue by platform."""
        aggregated: Dict[str, Dict] = {}

        for entry in entries:
            if entry.platform:
                key = entry.platform.value
                if key not in aggregated:
                    aggregated[key] = {
                        "gross": 0,
                        "net": 0,
                        "count": 0,
                    }
                aggregated[key]["gross"] += entry.gross_amount
                aggregated[key]["net"] += entry.net_amount
                aggregated[key]["count"] += 1

        return [
            RevenueStream(
                source=RevenueSource.OTHER,  # Platform-based
                platform=Platform(platform),
                total_gross=data["gross"],
                total_net=data["net"],
                count=data["count"],
                period_start=start,
                period_end=end,
            )
            for platform, data in aggregated.items()
        ]

    def _get_top_deals(
        self,
        entries: List[RevenueEntry],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get top revenue-generating entries."""
        sorted_entries = sorted(
            entries,
            key=lambda e: e.net_amount,
            reverse=True,
        )[:limit]

        return [
            {
                "id": str(e.entry_id),
                "description": e.description,
                "source": e.source.value,
                "amount": e.net_amount,
                "earned_at": e.earned_at.isoformat(),
            }
            for e in sorted_entries
        ]

    async def _check_stripe_connected(self, user_id: UUID) -> bool:
        """Check if user has connected Stripe account."""
        # Would check database for Stripe account ID
        return True  # Placeholder

    async def _get_stripe_account(self, user_id: UUID) -> Optional[str]:
        """Get user's Stripe account ID."""
        # Would query database
        return f"acct_test_{user_id.hex[:16]}"

    async def _get_next_payout(self, user_id: UUID) -> Dict[str, Any]:
        """Get next scheduled payout."""
        return {
            "date": (datetime.utcnow() + timedelta(days=3)),
            "amount": 1500.00,  # Would calculate from pending
        }

    async def _save_entry(self, entry: RevenueEntry) -> None:
        """Save revenue entry to database."""
        from app.models.revenue import RevenueEntryRecord

        record = RevenueEntryRecord(
            id=entry.entry_id,
            user_id=entry.user_id,
            source=entry.source.value,
            platform=entry.platform.value if entry.platform else None,
            description=entry.description,
            gross_amount=entry.gross_amount,
            net_amount=entry.net_amount,
            earned_at=entry.earned_at,
            paid_at=entry.paid_at,
            external_id=entry.external_id,
            brand_deal_id=entry.brand_deal_id,
        )

        self.db.add(record)
        await self.db.flush()

    async def _record_payout(
        self,
        user_id: UUID,
        amount: float,
        currency: str,
        stripe_transfer_id: str,
    ) -> None:
        """Record payout in database."""
        from app.models.revenue import PayoutRecord

        record = PayoutRecord(
            id=uuid4(),
            user_id=user_id,
            amount=amount,
            currency=currency,
            status="pending",
            stripe_transfer_id=stripe_transfer_id,
        )

        self.db.add(record)
        await self.db.flush()
