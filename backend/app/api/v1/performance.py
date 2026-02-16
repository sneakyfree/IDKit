"""
Performance Monitoring API

Endpoints for collecting and analyzing frontend performance metrics.
Stores Web Vitals to the database for persistent, per-user analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.performance import PerformanceMetric
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class WebVitalMetric(BaseModel):
    """A single Web Vital metric."""

    name: str = Field(..., description="Metric name (LCP, FID, CLS, etc.)")
    value: float = Field(..., description="Metric value")
    rating: str = Field(..., description="Rating: good, needs-improvement, poor")
    delta: float = Field(0, description="Delta from previous value")
    id: str = Field(..., description="Unique metric instance ID")
    navigationType: str = Field("navigate", description="Navigation type")


class PerformanceReport(BaseModel):
    """Performance metrics report from frontend."""

    metrics: list[WebVitalMetric] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: str
    userAgent: Optional[str] = None
    sessionId: Optional[str] = None
    deviceType: Optional[str] = None


class PerformanceReportResponse(BaseModel):
    """Response for performance report submission."""

    success: bool
    metricsReceived: int
    message: str


class PerformanceSummary(BaseModel):
    """Aggregated performance summary."""

    averageLCP: Optional[float] = None
    averageFID: Optional[float] = None
    averageCLS: Optional[float] = None
    averageFCP: Optional[float] = None
    averageTTFB: Optional[float] = None
    averageINP: Optional[float] = None
    sampleCount: int = 0
    goodPercentage: float = 0.0
    periodStart: datetime
    periodEnd: datetime


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/report", response_model=PerformanceReportResponse)
async def report_performance(
    report: PerformanceReport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit frontend performance metrics.

    Collects Web Vitals data and persists to the database.
    """
    try:
        for metric in report.metrics:
            record = PerformanceMetric(
                user_id=current_user.id,
                name=metric.name,
                value=metric.value,
                rating=metric.rating,
                delta=metric.delta,
                metric_id=metric.id,
                navigation_type=metric.navigationType,
                url=report.url,
                user_agent=report.userAgent,
                session_id=report.sessionId,
                device_type=report.deviceType,
                recorded_at=report.timestamp,
            )
            db.add(record)

        await db.commit()

        logger.info(
            f"Stored {len(report.metrics)} metrics from user {current_user.id} "
            f"for URL {report.url}"
        )

        return PerformanceReportResponse(
            success=True,
            metricsReceived=len(report.metrics),
            message="Metrics recorded successfully",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to store performance metrics: {e}")
        return PerformanceReportResponse(
            success=False,
            metricsReceived=0,
            message=f"Failed to store metrics: {str(e)}",
        )


@router.get("/summary", response_model=PerformanceSummary)
async def get_performance_summary(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated performance summary for the current user.

    Returns average values for each Web Vital and overall quality metrics
    over the specified period (default: 30 days).
    """
    now = datetime.utcnow()
    period_start = now - timedelta(days=days)

    # Build averages per metric name
    avg_query = (
        select(
            PerformanceMetric.name,
            func.avg(PerformanceMetric.value).label("avg_value"),
        )
        .where(
            PerformanceMetric.user_id == current_user.id,
            PerformanceMetric.recorded_at >= period_start,
        )
        .group_by(PerformanceMetric.name)
    )
    result = await db.execute(avg_query)
    averages = {row.name: float(row.avg_value) for row in result}

    # Total sample count
    count_query = (
        select(func.count())
        .select_from(PerformanceMetric)
        .where(
            PerformanceMetric.user_id == current_user.id,
            PerformanceMetric.recorded_at >= period_start,
        )
    )
    total = (await db.execute(count_query)).scalar() or 0

    # Good percentage
    good_query = (
        select(func.count())
        .select_from(PerformanceMetric)
        .where(
            PerformanceMetric.user_id == current_user.id,
            PerformanceMetric.recorded_at >= period_start,
            PerformanceMetric.rating == "good",
        )
    )
    good_count = (await db.execute(good_query)).scalar() or 0
    good_pct = (good_count / total * 100) if total > 0 else 0.0

    return PerformanceSummary(
        averageLCP=averages.get("LCP"),
        averageFID=averages.get("FID"),
        averageCLS=averages.get("CLS"),
        averageFCP=averages.get("FCP"),
        averageTTFB=averages.get("TTFB"),
        averageINP=averages.get("INP"),
        sampleCount=total,
        goodPercentage=round(good_pct, 1),
        periodStart=period_start,
        periodEnd=now,
    )


@router.get("/health")
async def performance_health(
    db: AsyncSession = Depends(get_db),
):
    """
    Health check for performance monitoring service.
    """
    count_query = select(func.count()).select_from(PerformanceMetric)
    total = (await db.execute(count_query)).scalar() or 0

    return {
        "status": "healthy",
        "metricsStored": total,
    }
