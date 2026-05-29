"""
Agent API Endpoints

REST API for interacting with the IDKit agent crew.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.agents import AgentType
from app.models.user import User
from app.services.agent_service import AgentService

router = APIRouter(tags=["agents"])


# ============== Request/Response Schemas ==============

class TaskSubmitRequest(BaseModel):
    """Request to submit a task to the agent crew."""
    task_type: str = Field(..., description="Type of task (generate_draft, analyze_performance, etc.)")
    description: str = Field(default="", description="Human-readable task description")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Task input parameters")
    target_agent: Optional[str] = Field(None, description="Specific agent to handle task")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1=highest, 10=lowest)")


class TaskResultResponse(BaseModel):
    """Response from task execution."""
    result_id: str
    agent_type: str
    action_type: str
    success: bool
    output: Any
    confidence: float
    reasoning: str
    requires_approval: bool
    approval_reason: Optional[str] = None


class PendingApprovalResponse(BaseModel):
    """A pending approval item."""
    approval_id: str
    agent_type: str
    action_type: str
    title: str
    description: Optional[str]
    preview: Any
    priority: str
    created_at: Optional[str]


class ApprovalRequest(BaseModel):
    """Request to approve or reject an action."""
    notes: Optional[str] = None
    reason: Optional[str] = None


class ActionHistoryItem(BaseModel):
    """An item from action history."""
    action_id: str
    agent_type: str
    action_type: str
    confidence: float
    reasoning: Optional[str]
    approval_status: str
    success: bool
    created_at: Optional[str]


# ============== Endpoints ==============

@router.post("/task", response_model=TaskResultResponse)
async def submit_task(
    request: TaskSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a task to the AI agent crew.
    
    The task will be routed to the appropriate specialist agent
    based on the task_type or target_agent specified.
    
    Returns the result immediately. If requires_approval is True,
    the action is pending and needs human confirmation.
    """
    service = AgentService(db)
    
    # Parse target agent if specified
    target_agent = None
    if request.target_agent:
        try:
            target_agent = AgentType(request.target_agent.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {request.target_agent}",
            )
    
    try:
        result = await service.submit_task(
            user_id=current_user.id,
            task_type=request.task_type,
            description=request.description,
            inputs=request.inputs,
            target_agent=target_agent,
            priority=request.priority,
        )
        await db.commit()
        
        return TaskResultResponse(
            result_id=str(result.result_id),
            agent_type=result.agent_type.value,
            action_type=result.action_type,
            success=result.success,
            output=result.output,
            confidence=result.confidence,
            reasoning=result.reasoning,
            requires_approval=result.requires_approval,
            approval_reason=result.approval_reason,
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}",
        )


@router.get("/pending", response_model=List[PendingApprovalResponse])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all pending actions awaiting approval.
    
    Returns a list of actions that require human confirmation
    before they can be executed.
    """
    service = AgentService(db)
    approvals = await service.get_pending_approvals_for_user(current_user.id)
    
    return [
        PendingApprovalResponse(**a)
        for a in approvals
    ]


@router.post("/approve/{approval_id}")
async def approve_action(
    approval_id: UUID,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a pending action.
    
    This allows the agent to proceed with the action.
    """
    service = AgentService(db)
    
    success = await service.approve_action(
        user_id=current_user.id,
        approval_id=approval_id,
        notes=request.notes,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending approval not found",
        )
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Action approved",
        "approval_id": str(approval_id),
    }


@router.post("/reject/{approval_id}")
async def reject_action(
    approval_id: UUID,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a pending action.
    
    This prevents the agent from proceeding with the action.
    """
    service = AgentService(db)
    
    success = await service.reject_action(
        user_id=current_user.id,
        approval_id=approval_id,
        reason=request.reason,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending approval not found",
        )
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Action rejected",
        "approval_id": str(approval_id),
    }


@router.get("/history", response_model=List[ActionHistoryItem])
async def get_action_history(
    agent_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get agent action history.
    
    Returns a log of all agent actions, which serves as
    an audit trail for compliance and debugging.
    """
    service = AgentService(db)
    
    # Parse agent type filter
    agent_filter = None
    if agent_type:
        try:
            agent_filter = AgentType(agent_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {agent_type}",
            )
    
    history = await service.get_action_history_for_user(
        user_id=current_user.id,
        agent_type=agent_filter,
        limit=min(limit, 100),
    )
    
    return [
        ActionHistoryItem(**h)
        for h in history
    ]


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user: User = Depends(get_current_user),
):
    """
    Get available agents and their capabilities.
    
    Returns information about what tasks each agent can handle.
    """
    service = AgentService(None)  # Don't need DB for this
    agents = await service.orchestrator.get_available_agents()
    
    return {
        "agents": agents,
        "task_types": [
            # Content Agent
            {"type": "generate_draft", "agent": "content", "description": "Generate content draft"},
            {"type": "generate_ideas", "agent": "content", "description": "Generate content ideas"},
            {"type": "repurpose_content", "agent": "content", "description": "Repurpose for different platform"},
            {"type": "suggest_improvements", "agent": "content", "description": "Suggest content improvements"},
            # Analytics Agent
            {"type": "analyze_performance", "agent": "analytics", "description": "Analyze content performance"},
            {"type": "identify_trends", "agent": "analytics", "description": "Identify trends"},
            {"type": "generate_insights", "agent": "analytics", "description": "Generate actionable insights"},
            {"type": "calculate_metrics", "agent": "analytics", "description": "Calculate specific metrics"},
            # Publishing Agent
            {"type": "schedule_content", "agent": "publishing", "description": "Schedule content for publishing"},
            {"type": "format_content", "agent": "publishing", "description": "Format for platform"},
            {"type": "optimize_schedule", "agent": "publishing", "description": "Optimize posting schedule"},
        ],
    }
