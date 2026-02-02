"""
Agent Memory API

REST endpoints for managing agent memory and context.
Enables users to view, clear, and configure agent memory.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.agents.memory import AgentMemoryService


router = APIRouter(prefix="/agent-memory", tags=["Agent Memory"])


# ==================== Schemas ====================

class MemorySummaryResponse(BaseModel):
    """Summary of user's agent memories."""
    total_memories: int
    by_agent: dict[str, list[dict[str, Any]]]


class MemoryItem(BaseModel):
    """Individual memory item."""
    id: str
    agent_type: str
    memory_type: str
    summary: str
    content: dict[str, Any]
    importance_score: float
    tags: list[str] | None
    created_at: str
    expires_at: str | None


class MemoryListResponse(BaseModel):
    """List of memories."""
    memories: list[MemoryItem]
    total: int


class AgentContextResponse(BaseModel):
    """Current agent context for user."""
    recent_interactions: list[dict[str, Any]]
    long_term_context: list[dict[str, Any]]
    learned_preferences: dict[str, Any]
    total_interactions: int


class ClearMemoryRequest(BaseModel):
    """Request to clear memories."""
    agent_type: str | None = Field(
        None,
        description="Clear only memories for this agent type"
    )


class ClearMemoryResponse(BaseModel):
    """Response from clearing memories."""
    cleared_count: int
    message: str


class GuardrailConfigResponse(BaseModel):
    """User's guardrail configuration."""
    action_permissions: dict[str, str]
    agent_autonomy: dict[str, str]
    auto_approve_thresholds: dict[str, float]
    risk_tolerance: str


class UpdateGuardrailRequest(BaseModel):
    """Request to update guardrail config."""
    action_permissions: dict[str, str] | None = None
    agent_autonomy: dict[str, str] | None = None
    auto_approve_thresholds: dict[str, float] | None = None
    risk_tolerance: str | None = Field(
        None,
        pattern="^(conservative|medium|aggressive)$"
    )


# ==================== Endpoints ====================

@router.get("/summary", response_model=MemorySummaryResponse)
async def get_memory_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemorySummaryResponse:
    """
    Get summary of all agent memories for the current user.
    
    Returns total count and breakdown by agent type.
    """
    service = AgentMemoryService(db)
    summary = await service.get_memory_summary(current_user.id)
    return MemorySummaryResponse(**summary)


@router.get("/list", response_model=MemoryListResponse)
async def list_memories(
    agent_type: str | None = None,
    memory_type: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryListResponse:
    """
    List memories with optional filtering.
    
    - **agent_type**: Filter by agent (content, analytics, etc.)
    - **memory_type**: Filter by type (short_term, long_term)
    - **limit**: Maximum number of memories to return
    """
    from app.models.agent_memory import MemoryType
    
    service = AgentMemoryService(db)
    
    memory_type_enum = None
    if memory_type:
        try:
            memory_type_enum = MemoryType(memory_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid memory type: {memory_type}"
            )
    
    memories = await service.get_relevant_memories(
        user_id=current_user.id,
        agent_type=agent_type,
        memory_type=memory_type_enum,
        limit=limit,
    )
    
    return MemoryListResponse(
        memories=[
            MemoryItem(
                id=str(m.id),
                agent_type=m.agent_type,
                memory_type=m.memory_type,
                summary=m.summary,
                content=m.content,
                importance_score=m.importance_score,
                tags=m.tags,
                created_at=m.created_at.isoformat(),
                expires_at=m.expires_at.isoformat() if m.expires_at else None,
            )
            for m in memories
        ],
        total=len(memories),
    )


@router.get("/context", response_model=AgentContextResponse)
async def get_current_context(
    agent_type: str = "orchestrator",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentContextResponse:
    """
    Get the current agent context for the user.
    
    This shows what context will be provided to agents
    for the next interaction.
    """
    service = AgentMemoryService(db)
    context = await service.build_agent_context(
        user_id=current_user.id,
        agent_type=agent_type,
    )
    await db.commit()
    return AgentContextResponse(**context)


@router.delete("/clear", response_model=ClearMemoryResponse)
async def clear_memories(
    request: ClearMemoryRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClearMemoryResponse:
    """
    Clear agent memories for the current user.
    
    Optionally filter by agent type to clear only specific agent memories.
    """
    service = AgentMemoryService(db)
    
    agent_type = request.agent_type if request else None
    cleared = await service.clear_user_memories(
        user_id=current_user.id,
        agent_type=agent_type,
    )
    await db.commit()
    
    agent_msg = f" for {agent_type} agent" if agent_type else ""
    return ClearMemoryResponse(
        cleared_count=cleared,
        message=f"Cleared {cleared} memories{agent_msg}",
    )


@router.get("/guardrails", response_model=GuardrailConfigResponse)
async def get_guardrails(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GuardrailConfigResponse:
    """
    Get the current guardrail configuration for agents.
    
    Shows permission levels, autonomy settings, and risk tolerance.
    """
    service = AgentMemoryService(db)
    config = await service.get_guardrail_config(current_user.id)
    await db.commit()
    
    return GuardrailConfigResponse(
        action_permissions=config.action_permissions,
        agent_autonomy=config.agent_autonomy,
        auto_approve_thresholds=config.auto_approve_thresholds,
        risk_tolerance=config.risk_tolerance,
    )


@router.put("/guardrails", response_model=GuardrailConfigResponse)
async def update_guardrails(
    request: UpdateGuardrailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GuardrailConfigResponse:
    """
    Update guardrail configuration for agents.
    
    - **action_permissions**: Set per-action permissions (prohibited/gated/autonomous)
    - **agent_autonomy**: Set per-agent autonomy levels (low/medium/high)
    - **auto_approve_thresholds**: Confidence thresholds for auto-approval
    - **risk_tolerance**: Overall risk tolerance (conservative/medium/aggressive)
    """
    service = AgentMemoryService(db)
    config = await service.update_guardrail_config(
        user_id=current_user.id,
        action_permissions=request.action_permissions,
        agent_autonomy=request.agent_autonomy,
        auto_approve_thresholds=request.auto_approve_thresholds,
        risk_tolerance=request.risk_tolerance,
    )
    await db.commit()
    
    return GuardrailConfigResponse(
        action_permissions=config.action_permissions,
        agent_autonomy=config.agent_autonomy,
        auto_approve_thresholds=config.auto_approve_thresholds,
        risk_tolerance=config.risk_tolerance,
    )
