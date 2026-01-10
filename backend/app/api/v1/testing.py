"""
A/B Testing API Endpoints

Content testing and experimentation framework.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.testing import (
    ABTestingService,
    TestType,
    TestStatus,
    WinnerCriteria,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class VariantCreate(BaseModel):
    """Variant creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    content: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, gt=0, le=100)


class CreateTestRequest(BaseModel):
    """Request to create an A/B test."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    test_type: str = Field(..., description="caption, hashtag, thumbnail, posting_time, content_format")
    variants: List[VariantCreate] = Field(..., min_items=2, max_items=10)
    winner_criteria: str = Field(default="engagement_rate", description="engagement_rate, clicks, conversions, impressions")
    min_sample_size: int = Field(default=100, ge=10, le=100000)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    auto_end_on_significance: bool = True
    platforms: Optional[List[str]] = None


class UpdateTestRequest(BaseModel):
    """Request to update an A/B test."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    min_sample_size: Optional[int] = Field(None, ge=10, le=100000)
    confidence_level: Optional[float] = Field(None, ge=0.8, le=0.99)
    auto_end_on_significance: Optional[bool] = None


class VariantResponse(BaseModel):
    """Variant response schema."""
    id: str
    name: str
    content: Dict[str, Any]
    weight: float
    impressions: int
    engagements: int
    clicks: int
    conversions: int
    engagement_rate: float
    click_rate: float
    conversion_rate: float


class TestResponse(BaseModel):
    """A/B test response schema."""
    id: str
    name: str
    description: Optional[str]
    test_type: str
    status: str
    variants: List[VariantResponse]
    winner_criteria: str
    winner_variant_id: Optional[str]
    min_sample_size: int
    confidence_level: float
    statistical_significance: Optional[float]
    auto_end_on_significance: bool
    platforms: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class TestResultResponse(BaseModel):
    """Test result analysis response."""
    test_id: str
    test_name: str
    status: str
    variants: List[VariantResponse]
    winner: Optional[VariantResponse]
    statistical_significance: float
    confidence_level: float
    is_significant: bool
    recommendation: str
    insights: Dict[str, Any]


class RecordEngagementRequest(BaseModel):
    """Request to record engagement for a variant."""
    variant_id: str
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    impressions: int = Field(default=1, ge=1)


class GetVariantRequest(BaseModel):
    """Request to get variant for a user."""
    user_identifier: str = Field(..., description="User or session ID for consistent assignment")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=TestResponse)
async def create_test(
    request: CreateTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new A/B test.

    Tests allow comparing different content variations to determine
    which performs best based on engagement metrics.
    """
    try:
        test_type = TestType(request.test_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test_type. Valid options: {[t.value for t in TestType]}"
        )

    try:
        winner_criteria = WinnerCriteria(request.winner_criteria)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid winner_criteria. Valid options: {[c.value for c in WinnerCriteria]}"
        )

    service = ABTestingService(db)

    # Convert variant requests to dict format
    variants = [
        {
            "name": v.name,
            "content": v.content,
            "weight": v.weight,
        }
        for v in request.variants
    ]

    test = await service.create_test(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        test_type=test_type,
        variants=variants,
        winner_criteria=winner_criteria,
        min_sample_size=request.min_sample_size,
        confidence_level=request.confidence_level,
        auto_end_on_significance=request.auto_end_on_significance,
        platforms=request.platforms,
    )

    return _test_to_response(test)


@router.get("", response_model=List[TestResponse])
async def list_tests(
    status: Optional[str] = Query(None, description="Filter by status"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all A/B tests for the current user.
    """
    service = ABTestingService(db)

    status_filter = None
    if status:
        try:
            status_filter = TestStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    type_filter = None
    if test_type:
        try:
            type_filter = TestType(test_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid test_type")

    tests = await service.get_tests(
        user_id=current_user.id,
        status=status_filter,
        test_type=type_filter,
        limit=limit,
        offset=offset,
    )

    return [_test_to_response(test) for test in tests]


@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific A/B test.
    """
    service = ABTestingService(db)

    test = await service.get_test(
        user_id=current_user.id,
        test_id=test_id,
    )

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return _test_to_response(test)


@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: str,
    request: UpdateTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an A/B test.

    Only draft tests can be fully updated. Running tests have limited
    editable fields.
    """
    service = ABTestingService(db)

    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.description is not None:
        updates["description"] = request.description
    if request.min_sample_size is not None:
        updates["min_sample_size"] = request.min_sample_size
    if request.confidence_level is not None:
        updates["confidence_level"] = request.confidence_level
    if request.auto_end_on_significance is not None:
        updates["auto_end_on_significance"] = request.auto_end_on_significance

    test = await service.update_test(
        user_id=current_user.id,
        test_id=test_id,
        **updates,
    )

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return _test_to_response(test)


@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an A/B test.

    Running tests cannot be deleted - they must be ended first.
    """
    service = ABTestingService(db)

    success = await service.delete_test(
        user_id=current_user.id,
        test_id=test_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Test not found")

    return {"message": "Test deleted successfully"}


@router.post("/{test_id}/start", response_model=TestResponse)
async def start_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a draft A/B test.
    """
    service = ABTestingService(db)

    test = await service.start_test(
        user_id=current_user.id,
        test_id=test_id,
    )

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return _test_to_response(test)


@router.post("/{test_id}/end", response_model=TestResponse)
async def end_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    End a running A/B test.
    """
    service = ABTestingService(db)

    test = await service.end_test(
        user_id=current_user.id,
        test_id=test_id,
    )

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return _test_to_response(test)


@router.post("/{test_id}/variant")
async def get_variant_for_user(
    test_id: str,
    request: GetVariantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the assigned variant for a user.

    Uses consistent hashing to ensure the same user always gets
    the same variant within a test.
    """
    service = ABTestingService(db)

    variant = await service.get_variant_for_user(
        test_id=test_id,
        user_identifier=request.user_identifier,
    )

    if not variant:
        raise HTTPException(status_code=404, detail="Test not found or not running")

    return {
        "variant_id": variant.id,
        "variant_name": variant.name,
        "content": variant.content,
    }


@router.post("/{test_id}/record", response_model=TestResponse)
async def record_engagement(
    test_id: str,
    request: RecordEngagementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record engagement metrics for a variant.
    """
    service = ABTestingService(db)

    test = await service.record_engagement(
        test_id=test_id,
        variant_id=request.variant_id,
        likes=request.likes,
        comments=request.comments,
        shares=request.shares,
        saves=request.saves,
        clicks=request.clicks,
        conversions=request.conversions,
        impressions=request.impressions,
    )

    if not test:
        raise HTTPException(status_code=404, detail="Test or variant not found")

    return _test_to_response(test)


@router.get("/{test_id}/analyze", response_model=TestResultResponse)
async def analyze_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a test and get detailed results.

    Returns statistical analysis, winner determination, and recommendations.
    """
    service = ABTestingService(db)

    result = await service.analyze_test(
        user_id=current_user.id,
        test_id=test_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Test not found")

    return TestResultResponse(
        test_id=result.test_id,
        test_name=result.test_name,
        status=result.status.value,
        variants=[_variant_to_response(v) for v in result.variants],
        winner=_variant_to_response(result.winner) if result.winner else None,
        statistical_significance=result.statistical_significance,
        confidence_level=result.confidence_level,
        is_significant=result.is_significant,
        recommendation=result.recommendation,
        insights=result.insights,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _test_to_response(test) -> TestResponse:
    """Convert ABTest to response schema."""
    return TestResponse(
        id=test.id,
        name=test.name,
        description=test.description,
        test_type=test.test_type.value,
        status=test.status.value,
        variants=[_variant_to_response(v) for v in test.variants],
        winner_criteria=test.winner_criteria.value,
        winner_variant_id=test.winner_variant_id,
        min_sample_size=test.min_sample_size,
        confidence_level=test.confidence_level,
        statistical_significance=test.statistical_significance,
        auto_end_on_significance=test.auto_end_on_significance,
        platforms=test.platforms,
        created_at=test.created_at,
        started_at=test.started_at,
        ended_at=test.ended_at,
    )


def _variant_to_response(variant) -> VariantResponse:
    """Convert TestVariant to response schema."""
    return VariantResponse(
        id=variant.id,
        name=variant.name,
        content=variant.content,
        weight=variant.weight,
        impressions=variant.impressions,
        engagements=variant.engagements,
        clicks=variant.clicks,
        conversions=variant.conversions,
        engagement_rate=variant.engagement_rate,
        click_rate=variant.click_rate,
        conversion_rate=variant.conversion_rate,
    )
