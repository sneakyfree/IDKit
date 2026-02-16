"""
Custom Reporting API

Real endpoints replacing stubs for FEAT-067.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.reporting import ReportingService

router = APIRouter(prefix="/reports", tags=["Reports"])


# ---- Schemas ----

class ReportCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    metrics: list[str] = Field(min_length=1)
    platforms: list[str] = Field(min_length=1)
    date_range: Optional[dict] = None
    export_format: str = "pdf"


class ReportSchedule(BaseModel):
    frequency: str = "weekly"
    day: Optional[str] = None
    time: Optional[str] = "09:00"


# ---- Routes ----

@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's reports."""
    service = ReportingService(db)
    reports = await service.list_reports(current_user.id)
    return {"reports": [r.to_dict() for r in reports], "total": len(reports)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom report."""
    service = ReportingService(db)
    report = await service.create(user_id=current_user.id, **data.model_dump())
    return report.to_dict()


@router.get("/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a report by ID."""
    service = ReportingService(db)
    report = await service.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return report.to_dict()


@router.post("/{report_id}/generate")
async def generate_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate/refresh report data."""
    service = ReportingService(db)
    report = await service.generate_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_dict()


@router.post("/{report_id}/schedule")
async def schedule_report(
    report_id: uuid.UUID,
    data: ReportSchedule,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a report for recurring generation."""
    service = ReportingService(db)
    report = await service.schedule_report(report_id, data.model_dump())
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_dict()


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report."""
    service = ReportingService(db)
    if not await service.delete(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
