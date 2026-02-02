"""
Performance Monitoring API

Endpoints for collecting and analyzing frontend performance metrics.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
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
    sampleCount: int = 0
    goodPercentage: float = 0.0
    periodStart: datetime
    periodEnd: datetime


# =============================================================================
# In-Memory Store (for demo - use Redis/DB in production)
# =============================================================================


# Simple in-memory store for metrics (replace with database in production)
_metrics_store: list[dict] = []
MAX_STORED_METRICS = 10000


def store_metrics(user_id: UUID, report: PerformanceReport) -> None:
    """Store metrics (in-memory for demo)."""
    global _metrics_store
    
    for metric in report.metrics:
        _metrics_store.append({
            "user_id": str(user_id),
            "name": metric.name,
            "value": metric.value,
            "rating": metric.rating,
            "url": report.url,
            "timestamp": report.timestamp,
        })
    
    # Keep store bounded
    if len(_metrics_store) > MAX_STORED_METRICS:
        _metrics_store = _metrics_store[-MAX_STORED_METRICS:]


def get_metrics_summary(user_id: UUID) -> dict:
    """Get aggregated metrics for a user."""
    user_metrics = [m for m in _metrics_store if m["user_id"] == str(user_id)]
    
    if not user_metrics:
        return {
            "averageLCP": None,
            "averageFID": None,
            "averageCLS": None,
            "sampleCount": 0,
            "goodPercentage": 0.0,
        }
    
    # Calculate averages
    metrics_by_name: dict[str, list[float]] = {}
    good_count = 0
    
    for m in user_metrics:
        name = m["name"]
        if name not in metrics_by_name:
            metrics_by_name[name] = []
        metrics_by_name[name].append(m["value"])
        if m["rating"] == "good":
            good_count += 1
    
    return {
        "averageLCP": sum(metrics_by_name.get("LCP", [0])) / max(len(metrics_by_name.get("LCP", [1])), 1),
        "averageFID": sum(metrics_by_name.get("FID", [0])) / max(len(metrics_by_name.get("FID", [1])), 1),
        "averageCLS": sum(metrics_by_name.get("CLS", [0])) / max(len(metrics_by_name.get("CLS", [1])), 1),
        "averageFCP": sum(metrics_by_name.get("FCP", [0])) / max(len(metrics_by_name.get("FCP", [1])), 1),
        "averageTTFB": sum(metrics_by_name.get("TTFB", [0])) / max(len(metrics_by_name.get("TTFB", [1])), 1),
        "sampleCount": len(user_metrics),
        "goodPercentage": (good_count / len(user_metrics)) * 100 if user_metrics else 0,
    }


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
    
    Collects Web Vitals data for performance monitoring and analysis.
    """
    try:
        store_metrics(current_user.id, report)
        
        logger.info(
            f"Received {len(report.metrics)} metrics from user {current_user.id} "
            f"for URL {report.url}"
        )
        
        return PerformanceReportResponse(
            success=True,
            metricsReceived=len(report.metrics),
            message="Metrics recorded successfully",
        )
    except Exception as e:
        logger.error(f"Failed to store performance metrics: {e}")
        return PerformanceReportResponse(
            success=False,
            metricsReceived=0,
            message=f"Failed to store metrics: {str(e)}",
        )


@router.get("/summary", response_model=PerformanceSummary)
async def get_performance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated performance summary for the current user.
    
    Returns average values for each Web Vital and overall quality metrics.
    """
    summary = get_metrics_summary(current_user.id)
    
    now = datetime.utcnow()
    return PerformanceSummary(
        averageLCP=summary.get("averageLCP"),
        averageFID=summary.get("averageFID"),
        averageCLS=summary.get("averageCLS"),
        averageFCP=summary.get("averageFCP"),
        averageTTFB=summary.get("averageTTFB"),
        sampleCount=summary.get("sampleCount", 0),
        goodPercentage=summary.get("goodPercentage", 0.0),
        periodStart=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        periodEnd=now,
    )


@router.get("/health")
async def performance_health():
    """
    Health check for performance monitoring service.
    """
    return {
        "status": "healthy",
        "metricsStored": len(_metrics_store),
        "maxCapacity": MAX_STORED_METRICS,
    }
