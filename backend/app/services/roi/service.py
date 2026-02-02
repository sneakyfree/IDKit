"""
ROI Calculation Service

Service for calculating creator ROI metrics including revenue aggregation,
cost tracking, historical trends, and projections.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roi import ROIReport, CostEntry
from app.models.payout import Transfer

logger = logging.getLogger(__name__)


class ROIService:
    """
    Service for calculating and storing ROI metrics.
    
    Aggregates revenue from various sources (brand deals, affiliates,
    royalties, etc.) and costs to calculate comprehensive ROI metrics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_roi(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        save_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate ROI for a given time period.
        
        Args:
            user_id: The user's ID
            start_date: Start of the period
            end_date: End of the period
            save_report: Whether to save the report to the database
            
        Returns:
            Complete ROI report data
        """
        # Convert dates to datetime for queries
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Aggregate revenue from transfers
        revenue = await self._aggregate_revenue(user_id, start_dt, end_dt)

        # Aggregate costs from cost entries
        costs = await self._aggregate_costs(user_id, start_dt, end_dt)

        # Get engagement metrics (placeholder - would integrate with analytics)
        engagement = await self._get_engagement_metrics(user_id, start_dt, end_dt)

        # Calculate derived metrics
        metrics = self._calculate_metrics(revenue, costs, engagement)

        # Build report data
        report_data = {
            "user_id": user_id,
            "period_start": start_dt,
            "period_end": end_dt,
            "period_type": self._determine_period_type(start_date, end_date),
            "revenue": revenue,
            "costs": costs,
            "engagement": engagement,
            "metrics": metrics,
        }

        if save_report:
            report = await self._save_report(report_data)
            report_data["id"] = report.id
            report_data["created_at"] = report.created_at

        return report_data

    async def _aggregate_revenue(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> Dict[str, int]:
        """Aggregate revenue from transfers and other sources."""
        # Query transfers to user's connect account
        # In a real implementation, this would also query brand_deals, affiliates, etc.
        
        brand_deal_revenue = 0
        affiliate_revenue = 0
        subscription_revenue = 0
        royalty_revenue = 0
        other_revenue = 0

        # Get transfers for this user
        # Note: In production, you'd join with connect_accounts to get user's account
        # For now, we'll use a simplified approach
        
        total = (
            brand_deal_revenue +
            affiliate_revenue +
            subscription_revenue +
            royalty_revenue +
            other_revenue
        )

        return {
            "brand_deals": brand_deal_revenue,
            "affiliate": affiliate_revenue,
            "subscriptions": subscription_revenue,
            "royalties": royalty_revenue,
            "other": other_revenue,
            "total": total,
        }

    async def _aggregate_costs(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> Dict[str, int]:
        """Aggregate costs from cost entries."""
        result = await self.db.execute(
            select(CostEntry).where(
                and_(
                    CostEntry.user_id == user_id,
                    CostEntry.expense_date >= start_dt,
                    CostEntry.expense_date <= end_dt,
                )
            )
        )
        entries = result.scalars().all()

        # Group by category
        costs_by_category = {
            "platform_fees": 0,
            "content_creation": 0,
            "advertising": 0,
            "software": 0,
            "equipment": 0,
            "labor": 0,
            "other": 0,
        }

        for entry in entries:
            category = entry.category.lower()
            if category in costs_by_category:
                costs_by_category[category] += entry.amount_cents
            else:
                costs_by_category["other"] += entry.amount_cents

        costs_by_category["total"] = sum(costs_by_category.values())

        return costs_by_category

    async def _get_engagement_metrics(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> Dict[str, int]:
        """
        Get engagement metrics for the period.
        
        In a real implementation, this would query analytics data.
        """
        # Placeholder - would integrate with real analytics
        return {
            "total_views": 0,
            "total_engagements": 0,
            "new_followers": 0,
            "content_pieces": 0,
        }

    def _calculate_metrics(
        self,
        revenue: Dict[str, int],
        costs: Dict[str, int],
        engagement: Dict[str, int],
    ) -> Dict[str, float]:
        """Calculate derived ROI metrics."""
        total_revenue = revenue["total"]
        total_costs = costs["total"]
        net_profit = total_revenue - total_costs

        # ROI = (Net Profit / Total Costs) * 100
        roi_percentage = (
            (net_profit / total_costs * 100) if total_costs > 0 else 0.0
        )

        # Profit Margin = (Net Profit / Total Revenue) * 100
        profit_margin = (
            (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        )

        # Revenue per content
        content_pieces = engagement["content_pieces"]
        revenue_per_content = (
            total_revenue / content_pieces if content_pieces > 0 else 0.0
        )

        # Revenue per view
        total_views = engagement["total_views"]
        revenue_per_view = (
            total_revenue / total_views if total_views > 0 else 0.0
        )

        # Revenue per new follower
        new_followers = engagement["new_followers"]
        revenue_per_follower = (
            total_revenue / new_followers if new_followers > 0 else 0.0
        )

        # Engagement rate
        engagement_rate = (
            (engagement["total_engagements"] / total_views * 100)
            if total_views > 0 else 0.0
        )

        return {
            "net_profit_cents": net_profit,
            "roi_percentage": round(roi_percentage, 2),
            "profit_margin": round(profit_margin, 2),
            "revenue_per_content": round(revenue_per_content, 2),
            "revenue_per_view": round(revenue_per_view, 4),
            "revenue_per_follower": round(revenue_per_follower, 2),
            "engagement_rate": round(engagement_rate, 2),
        }

    def _determine_period_type(self, start_date: date, end_date: date) -> str:
        """Determine the period type based on date range."""
        delta = (end_date - start_date).days

        if delta <= 1:
            return "daily"
        elif delta <= 7:
            return "weekly"
        elif delta <= 31:
            return "monthly"
        else:
            return "yearly"

    async def _save_report(self, report_data: Dict[str, Any]) -> ROIReport:
        """Save ROI report to database."""
        report = ROIReport(
            id=str(uuid4()),
            user_id=report_data["user_id"],
            period_start=report_data["period_start"],
            period_end=report_data["period_end"],
            period_type=report_data["period_type"],
            # Revenue
            total_revenue_cents=report_data["revenue"]["total"],
            brand_deal_revenue_cents=report_data["revenue"]["brand_deals"],
            affiliate_revenue_cents=report_data["revenue"]["affiliate"],
            subscription_revenue_cents=report_data["revenue"]["subscriptions"],
            royalty_revenue_cents=report_data["revenue"]["royalties"],
            other_revenue_cents=report_data["revenue"]["other"],
            # Costs
            total_costs_cents=report_data["costs"]["total"],
            platform_fees_cents=report_data["costs"]["platform_fees"],
            content_creation_costs_cents=report_data["costs"]["content_creation"],
            advertising_costs_cents=report_data["costs"]["advertising"],
            software_costs_cents=report_data["costs"]["software"],
            other_costs_cents=report_data["costs"]["other"],
            # Metrics
            net_profit_cents=report_data["metrics"]["net_profit_cents"],
            roi_percentage=report_data["metrics"]["roi_percentage"],
            profit_margin=report_data["metrics"]["profit_margin"],
            # Engagement
            total_views=report_data["engagement"]["total_views"],
            total_engagements=report_data["engagement"]["total_engagements"],
            new_followers=report_data["engagement"]["new_followers"],
            content_pieces=report_data["engagement"]["content_pieces"],
            # Derived
            revenue_per_content=report_data["metrics"]["revenue_per_content"],
            revenue_per_view=report_data["metrics"]["revenue_per_view"],
            revenue_per_follower=report_data["metrics"]["revenue_per_follower"],
            engagement_rate=report_data["metrics"]["engagement_rate"],
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        return report

    async def get_historical_reports(
        self,
        user_id: str,
        limit: int = 12,
    ) -> List[ROIReport]:
        """Get historical ROI reports for a user."""
        result = await self.db.execute(
            select(ROIReport)
            .where(ROIReport.user_id == user_id)
            .order_by(ROIReport.period_end.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def generate_projections(
        self,
        user_id: str,
        months_ahead: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Generate ROI projections based on historical data.
        
        Uses simple moving average for projections.
        """
        # Get last 12 months of reports
        reports = await self.get_historical_reports(user_id, limit=12)

        if not reports:
            return []

        # Calculate averages
        total_revenue = sum(r.total_revenue_cents for r in reports)
        total_costs = sum(r.total_costs_cents for r in reports)
        count = len(reports)

        avg_revenue = total_revenue / count if count > 0 else 0
        avg_costs = total_costs / count if count > 0 else 0
        avg_profit = avg_revenue - avg_costs

        # Generate projections
        projections = []
        base_date = date.today()

        for i in range(1, months_ahead + 1):
            projection_date = base_date + timedelta(days=30 * i)
            # Add some variance based on trend (placeholder for more sophisticated analysis)
            confidence = max(0.5, 1.0 - (i * 0.08))

            projections.append({
                "date": projection_date,
                "projected_revenue_cents": int(avg_revenue),
                "projected_costs_cents": int(avg_costs),
                "projected_profit_cents": int(avg_profit),
                "confidence": round(confidence, 2),
            })

        return projections

    # ========== Cost Entry Management ==========

    async def add_cost_entry(
        self,
        user_id: str,
        amount_cents: int,
        category: str,
        expense_date: date,
        description: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_period: Optional[str] = None,
    ) -> CostEntry:
        """Add a cost entry for a user."""
        entry = CostEntry(
            id=str(uuid4()),
            user_id=user_id,
            amount_cents=amount_cents,
            category=category,
            description=description,
            expense_date=datetime.combine(expense_date, datetime.min.time()),
            is_recurring=1 if is_recurring else 0,
            recurrence_period=recurrence_period,
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def get_cost_entries(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
    ) -> List[CostEntry]:
        """Get cost entries for a user with optional filters."""
        query = select(CostEntry).where(CostEntry.user_id == user_id)

        if start_date:
            query = query.where(
                CostEntry.expense_date >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            query = query.where(
                CostEntry.expense_date <= datetime.combine(end_date, datetime.max.time())
            )
        if category:
            query = query.where(CostEntry.category == category)

        query = query.order_by(CostEntry.expense_date.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_cost_entry(self, user_id: str, entry_id: str) -> bool:
        """Delete a cost entry."""
        result = await self.db.execute(
            select(CostEntry).where(
                and_(
                    CostEntry.id == entry_id,
                    CostEntry.user_id == user_id,
                )
            )
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return False

        await self.db.delete(entry)
        await self.db.commit()
        return True
