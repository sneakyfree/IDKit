"""
Intake API Endpoints

REST API for the TurboTax-style intake/onboarding flow.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.intake import ContradictionRecord, IntakeProgress, VerificationTask
from app.models.user import User
from app.schemas.intake import (
    ContradictionDetail,
    ContradictionResolution,
    IntakeAnswer as IntakeAnswerSchema,
    IntakeFlow,
    IntakeProgressResponse,
    IntakeResponseSubmit,
    IntakeSection,
    VerificationTaskList,
)
from app.services.intake_service import IntakeService

router = APIRouter(prefix="/intake", tags=["intake"])


# ============== Response Schemas ==============

class FlowResponse(BaseModel):
    """Intake flow configuration response."""
    flow: IntakeFlow
    progress: Optional[dict] = None


class ProgressResponse(BaseModel):
    """Current progress response."""
    user_id: str
    flow_id: str
    current_section: str
    completed_sections: list[str]
    percent_complete: float
    pending_verifications: int
    has_contradictions: bool


class SubmitResponse(BaseModel):
    """Response after submitting section answers."""
    success: bool
    progress: ProgressResponse
    next_section: Optional[IntakeSection] = None
    contradictions_detected: int = 0


class ContradictionListResponse(BaseModel):
    """List of contradictions."""
    contradictions: list[ContradictionDetail]
    total: int
    unresolved: int


class VerificationListResponse(BaseModel):
    """List of verification tasks."""
    tasks: list[dict]
    total: int
    high_priority: int


# ============== Endpoints ==============

@router.get("/flow", response_model=FlowResponse)
async def get_intake_flow(
    flow_id: str = "creator_onboarding_v1",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get intake flow configuration.
    
    Returns the full flow definition with questions, sections,
    and any saved progress for the current user.
    """
    service = IntakeService(db)
    
    flow = await service.get_intake_flow(flow_id)
    progress = await service.get_or_create_progress(current_user.id, flow_id)
    
    return FlowResponse(
        flow=flow,
        progress={
            "current_section": progress.current_section,
            "completed_sections": progress.completed_sections or [],
            "percent_complete": progress.percent_complete,
        }
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current intake progress for the user."""
    service = IntakeService(db)
    
    progress = await service.get_or_create_progress(current_user.id)
    pending = await service.get_pending_verifications(current_user.id)
    contradictions = await service.contradiction_engine.get_unresolved_contradictions(
        current_user.id
    )
    
    return ProgressResponse(
        user_id=str(current_user.id),
        flow_id=progress.flow_id,
        current_section=progress.current_section,
        completed_sections=progress.completed_sections or [],
        percent_complete=progress.percent_complete,
        pending_verifications=len(pending),
        has_contradictions=len(contradictions) > 0,
    )


@router.post("/response", response_model=SubmitResponse)
async def submit_section_response(
    data: IntakeResponseSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit answers for a section.
    
    Validates answers, saves progress, and returns next section.
    """
    service = IntakeService(db)
    
    # Convert schema answers to dict format
    answers = [
        {
            "question_id": a.question_id,
            "value": a.value,
            "is_unsure": a.is_unsure,
            "source": a.source.value if hasattr(a.source, 'value') else a.source,
            "confidence": a.confidence,
        }
        for a in data.answers
    ]
    
    try:
        progress = await service.process_section_response(
            user_id=current_user.id,
            section_id=data.section_id,
            answers=answers,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Get next section
    flow = await service.get_intake_flow(progress.flow_id)
    next_section = None
    if progress.current_section:
        next_section = next(
            (s for s in flow.sections if s.id == progress.current_section),
            None
        )
    
    # Check for contradictions
    contradictions = await service.contradiction_engine.get_unresolved_contradictions(
        current_user.id
    )
    
    return SubmitResponse(
        success=True,
        progress=ProgressResponse(
            user_id=str(current_user.id),
            flow_id=progress.flow_id,
            current_section=progress.current_section,
            completed_sections=progress.completed_sections or [],
            percent_complete=progress.percent_complete,
            pending_verifications=0,  # Will be calculated async
            has_contradictions=len(contradictions) > 0,
        ),
        next_section=next_section,
        contradictions_detected=len(contradictions),
    )


@router.get("/section/{section_id}")
async def get_section_answers(
    section_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get previously saved answers for a section."""
    service = IntakeService(db)
    
    answers = await service.get_section_answers(current_user.id, section_id)
    
    return {
        "section_id": section_id,
        "answers": [
            {
                "question_id": a.question_id,
                "value": a.value,
                "source": a.source,
                "confidence": a.confidence,
                "is_unsure": a.is_unsure,
            }
            for a in answers
        ]
    }


@router.get("/contradictions", response_model=ContradictionListResponse)
async def get_contradictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all detected contradictions for the user."""
    service = IntakeService(db)
    
    contradictions = await service.contradiction_engine.get_unresolved_contradictions(
        current_user.id
    )
    
    return ContradictionListResponse(
        contradictions=[
            ContradictionDetail(
                contradiction_id=c.id,
                field_name=c.field_name,
                field_label=c.field_label,
                user_reported=c.value_a,
                api_verified=c.value_b,
                discrepancy_description=f"{c.discrepancy_percent:.1f}% discrepancy" if c.discrepancy_percent else "Values don't match",
                severity=c.severity,
                resolution_options=["accept_user", "accept_api", "provide_evidence"],
            )
            for c in contradictions
        ],
        total=len(contradictions),
        unresolved=len(contradictions),
    )


@router.post("/contradictions/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: UUID,
    resolution: ContradictionResolution,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve a detected contradiction."""
    service = IntakeService(db)
    
    # Determine resolved value based on resolution type
    if resolution.resolution == "accept_api":
        # Get the API value from the contradiction
        contradictions = await service.contradiction_engine.get_unresolved_contradictions(
            current_user.id
        )
        contradiction = next(
            (c for c in contradictions if c.id == contradiction_id),
            None
        )
        if not contradiction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contradiction not found",
            )
        resolved_value = contradiction.value_b
    else:
        contradictions = await service.contradiction_engine.get_unresolved_contradictions(
            current_user.id
        )
        contradiction = next(
            (c for c in contradictions if c.id == contradiction_id),
            None
        )
        if not contradiction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contradiction not found",
            )
        resolved_value = contradiction.value_a
    
    record = await service.contradiction_engine.resolve_contradiction(
        contradiction_id=contradiction_id,
        resolution=resolution.resolution,
        resolved_value=resolved_value,
        resolved_by=str(current_user.id),
        explanation=resolution.explanation,
    )
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contradiction not found",
        )
    
    await db.commit()
    
    return {
        "success": True,
        "contradiction_id": str(contradiction_id),
        "resolution": resolution.resolution,
        "resolved_value": resolved_value,
    }


@router.get("/verifications", response_model=VerificationListResponse)
async def get_pending_verifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending verification tasks."""
    service = IntakeService(db)
    
    tasks = await service.get_pending_verifications(current_user.id)
    
    return VerificationListResponse(
        tasks=[
            {
                "task_id": str(t.id),
                "question_id": t.question_id,
                "question_label": t.question_label,
                "current_value": t.current_value,
                "verification_method": t.verification_method,
                "instructions": t.instructions,
                "priority": t.priority,
            }
            for t in tasks
        ],
        total=len(tasks),
        high_priority=sum(1 for t in tasks if t.priority == "high"),
    )


@router.post("/complete")
async def complete_intake(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark intake as complete."""
    service = IntakeService(db)
    
    progress = await service.complete_intake(current_user.id)
    await db.commit()
    
    return {
        "success": True,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        "percent_complete": progress.percent_complete,
    }


@router.post("/reset")
async def reset_intake(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset intake progress (for testing or re-onboarding)."""
    service = IntakeService(db)
    
    progress = await service.reset_intake(current_user.id)
    await db.commit()
    
    return {
        "success": True,
        "message": "Intake progress reset",
        "current_section": progress.current_section,
    }
