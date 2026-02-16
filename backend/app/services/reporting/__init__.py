"""
Reporting Service

Business logic for custom report generation and scheduling.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


class ReportingService:
    """Service for custom report management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        metrics: list[str],
        platforms: list[str],
        description: Optional[str] = None,
        date_range: Optional[dict] = None,
        export_format: str = "pdf",
    ) -> Report:
        """Create a new custom report."""
        report = Report(
            user_id=user_id,
            name=name,
            description=description,
            metrics=metrics,
            platforms=platforms,
            date_range=date_range or {},
            export_format=export_format,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def list_reports(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Report]:
        """List all reports for a user."""
        query = (
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, report_id: uuid.UUID) -> Optional[Report]:
        """Get a report by ID."""
        query = select(Report).where(Report.id == report_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_report(self, report_id: uuid.UUID) -> Optional[Report]:
        """Generate/refresh a report's data."""
        report = await self.get(report_id)
        if not report:
            return None

        # Generate data based on selected metrics
        generated_data = {}
        for metric in (report.metrics or []):
            generated_data[metric] = self._generate_metric_data(metric)

        report.last_generated_data = generated_data
        report.last_generated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def schedule_report(
        self,
        report_id: uuid.UUID,
        schedule: dict,
    ) -> Optional[Report]:
        """Set up a schedule for a report."""
        report = await self.get(report_id)
        if not report:
            return None
        report.schedule = schedule
        report.is_scheduled = True
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def delete(self, report_id: uuid.UUID) -> bool:
        """Delete a report."""
        report = await self.get(report_id)
        if not report:
            return False
        await self.db.delete(report)
        await self.db.commit()
        return True

    def _generate_metric_data(self, metric: str) -> dict:
        """Generate data for a single metric.
        In production, this aggregates real data from analytics tables.
        """
        # Placeholder that will be wired to actual analytics queries
        return {
            "metric": metric,
            "value": 0,
            "trend": "stable",
            "data_points": [],
        }
