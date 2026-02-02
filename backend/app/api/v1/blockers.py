"""
Blockers API Endpoints

REST API for blocker detection and unlocker action plans.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.blockers import (
    BlockerAnalysis,
    BlockerCategory,
    BlockerScanRequest,
    BlockerSeverity,
    FixList,
    UnlockerAction,
    UnlockerCompleteRequest,
)
from app.services.blockers_engine import BlockersEngine

router = APIRouter(prefix="/blockers", tags=["blockers"])


# ============== Request/Response Schemas ==============

class BlockerListResponse(BaseModel):
    """List of detected blockers."""
    blockers: List[BlockerAnalysis]
    total_count: int
    critical_count: int
    high_count: int


class UnlockerListResponse(BaseModel):
    """List of unlocker actions."""
    unlockers: List[UnlockerAction]
    blocker_id: str


class FixListResponse(BaseModel):
    """Prioritized fix list."""
    fix_list: FixList


# ============== Endpoints ==============

@router.get("", response_model=BlockerListResponse)
async def get_blockers(
    category: Optional[BlockerCategory] = None,
    min_severity: Optional[BlockerSeverity] = None,
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current blockers for the creator.
    
    Returns issues that are limiting growth/monetization.
    """
    engine = BlockersEngine(db)

    # Get user profile data (placeholder)
    profile_data = {
        "bio": "Content creator",
        "bio_link": None,  # Missing link
        "category": "Lifestyle",
        "profile_picture": True,
        "revenue_streams": [],
        "has_sponsorships": True,
        "uses_ftc_disclosures": False,
    }

    # Get metrics (placeholder)
    metrics_data = {
        "posts_per_week": 2,
        "video_percentage": 10,
        "engagement_rate": 2.5,
        "niche_engagement_average": 3.5,
    }

    categories = [category] if category else None
    
    blockers = await engine.detect_blockers(
        user_id=current_user.id,
        profile_data=profile_data,
        metrics_data=metrics_data,
        categories=categories,
    )

    # Filter by severity if specified
    if min_severity:
        severity_order = ["low", "medium", "high", "critical"]
        min_idx = severity_order.index(min_severity.value)
        blockers = [
            b for b in blockers
            if severity_order.index(b.severity.value) >= min_idx
        ]

    # Filter resolved
    if not include_resolved:
        blockers = [b for b in blockers if not b.is_resolved]

    critical_count = sum(1 for b in blockers if b.severity == BlockerSeverity.CRITICAL)
    high_count = sum(1 for b in blockers if b.severity == BlockerSeverity.HIGH)

    return BlockerListResponse(
        blockers=blockers,
        total_count=len(blockers),
        critical_count=critical_count,
        high_count=high_count,
    )


@router.get("/{blocker_id}/unlockers", response_model=UnlockerListResponse)
async def get_unlockers(
    blocker_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get action plans for a specific blocker.
    """
    engine = BlockersEngine(db)

    # Get blockers to find the specific one
    profile_data = {"bio": "Content creator", "bio_link": None}
    blockers = await engine.detect_blockers(
        user_id=current_user.id,
        profile_data=profile_data,
    )

    # Find matching blocker
    matching = [b for b in blockers if b.blocker_id == blocker_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocker not found",
        )

    unlockers = await engine.generate_unlockers(matching)

    return UnlockerListResponse(
        unlockers=unlockers,
        blocker_id=str(blocker_id),
    )


@router.post("/{blocker_id}/complete")
async def complete_unlocker(
    blocker_id: UUID,
    request: UnlockerCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark an unlocker action as complete.
    """
    # In production, would update database
    return {
        "success": True,
        "message": "Unlocker marked as complete",
        "action_id": str(request.action_id),
        "proof_recorded": bool(request.proof),
    }


@router.get("/fix-list", response_model=FixListResponse)
async def get_fix_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get prioritized fix list organized by timeframe.
    
    Returns:
    - Quick wins (< 1 hour)
    - 30-day actions
    - 90-day transformations
    """
    engine = BlockersEngine(db)

    # Detect all blockers
    profile_data = {
        "bio": "Content creator",
        "bio_link": None,
        "category": "Lifestyle",
        "profile_picture": True,
        "revenue_streams": [],
        "has_sponsorships": True,
        "uses_ftc_disclosures": False,
    }

    metrics_data = {
        "posts_per_week": 2,
        "video_percentage": 10,
        "engagement_rate": 2.5,
        "niche_engagement_average": 3.5,
    }

    blockers = await engine.detect_blockers(
        user_id=current_user.id,
        profile_data=profile_data,
        metrics_data=metrics_data,
    )

    fix_list = await engine.generate_fix_list(
        user_id=current_user.id,
        blockers=blockers,
    )

    return FixListResponse(fix_list=fix_list)


@router.get("/categories")
async def get_blocker_categories(
    current_user: User = Depends(get_current_user),
):
    """
    Get available blocker categories.
    """
    return {
        "categories": [
            {
                "value": c.value,
                "label": c.value.replace("_", " ").title(),
                "description": _get_category_description(c),
            }
            for c in BlockerCategory
        ]
    }


def _get_category_description(category: BlockerCategory) -> str:
    """Get description for blocker category."""
    descriptions = {
        BlockerCategory.CONTENT: "Quality, frequency, and format issues",
        BlockerCategory.ENGAGEMENT: "Low interaction and declining metrics",
        BlockerCategory.MONETIZATION: "Revenue gaps and missed opportunities",
        BlockerCategory.GROWTH: "Follower stagnation and reach limits",
        BlockerCategory.TECHNICAL: "Platform issues and API problems",
        BlockerCategory.COMPLIANCE: "FTC, copyright, and TOS issues",
        BlockerCategory.PROFILE: "Bio, links, and branding issues",
    }
    return descriptions.get(category, "")


@router.get("/summary")
async def get_blockers_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary of blockers by category and severity.
    """
    engine = BlockersEngine(db)

    profile_data = {
        "bio": "Content creator",
        "bio_link": None,
        "revenue_streams": [],
        "has_sponsorships": True,
        "uses_ftc_disclosures": False,
    }

    metrics_data = {
        "posts_per_week": 2,
        "video_percentage": 10,
        "engagement_rate": 2.5,
        "niche_engagement_average": 3.5,
    }

    blockers = await engine.detect_blockers(
        user_id=current_user.id,
        profile_data=profile_data,
        metrics_data=metrics_data,
    )

    # Group by category
    by_category = {}
    for b in blockers:
        cat = b.category.value
        if cat not in by_category:
            by_category[cat] = 0
        by_category[cat] += 1

    # Group by severity
    by_severity = {}
    for b in blockers:
        sev = b.severity.value
        if sev not in by_severity:
            by_severity[sev] = 0
        by_severity[sev] += 1

    return {
        "total_blockers": len(blockers),
        "by_category": by_category,
        "by_severity": by_severity,
        "top_priority": blockers[0].title if blockers else None,
    }
