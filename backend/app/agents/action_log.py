"""
Agent Action Logging

Immutable audit trail for all agent actions.
Every agent action is logged with full context for reproducibility.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentResult, AgentTask, AgentType, ActionStatus


async def log_action(
    db: AsyncSession,
    user_id: UUID,
    agent_type: AgentType,
    action_type: str,
    task: AgentTask,
    result: AgentResult,
    trigger: str = "user_request",
) -> "AgentActionLogRecord":
    """
    Log an agent action to the immutable audit trail.
    
    Creates a complete record of:
    - What action was taken
    - By which agent
    - With what inputs
    - What outputs were produced
    - The agent's reasoning
    - Approval status
    
    Returns the created log record.
    """
    from app.models.agent import AgentActionLog
    
    log_entry = AgentActionLog(
        user_id=user_id,
        agent_type=agent_type.value,
        action_type=action_type,
        trigger=trigger,
        
        # Task details
        task_id=task.task_id,
        task_type=task.task_type,
        task_inputs=task.inputs,
        
        # Result details
        result_id=result.result_id,
        output=result.output if not isinstance(result.output, bytes) else "[binary]",
        output_type=result.output_type,
        
        # Confidence and reasoning
        confidence=result.confidence,
        reasoning=result.reasoning,
        
        # Evidence chain
        evidence=[
            {
                "id": str(e.evidence_id),
                "source_type": e.source_type,
                "source_name": e.source_name,
                "confidence": e.confidence,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in result.evidence
        ],
        
        # Approval tracking
        approval_status=result.status.value,
        requires_approval=result.requires_approval,
        approval_reason=result.approval_reason,
        
        # Status
        success=result.success,
        error=result.error,
        error_details=result.error_details,
        
        # Timestamps
        started_at=result.started_at,
        completed_at=result.completed_at or datetime.utcnow(),
    )
    
    db.add(log_entry)
    await db.flush()
    
    return log_entry


async def get_action_history(
    db: AsyncSession,
    user_id: UUID,
    agent_type: Optional[AgentType] = None,
    action_type: Optional[str] = None,
    status: Optional[ActionStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List["AgentActionLogRecord"]:
    """
    Retrieve agent action history for a user.
    
    Supports filtering by:
    - agent_type: Only actions from a specific agent
    - action_type: Only specific action types
    - status: Only actions with a specific approval status
    """
    from app.models.agent import AgentActionLog
    
    query = select(AgentActionLog).where(
        AgentActionLog.user_id == user_id
    )
    
    if agent_type:
        query = query.where(AgentActionLog.agent_type == agent_type.value)
    
    if action_type:
        query = query.where(AgentActionLog.action_type == action_type)
    
    if status:
        query = query.where(AgentActionLog.approval_status == status.value)
    
    query = query.order_by(AgentActionLog.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_pending_approvals(
    db: AsyncSession,
    user_id: UUID,
) -> List["AgentActionLogRecord"]:
    """Get all actions pending human approval."""
    from app.models.agent import AgentActionLog
    
    result = await db.execute(
        select(AgentActionLog).where(
            AgentActionLog.user_id == user_id,
            AgentActionLog.approval_status == ActionStatus.PENDING.value,
            AgentActionLog.requires_approval == True,  # noqa: E712
        ).order_by(AgentActionLog.created_at.desc())
    )
    
    return list(result.scalars().all())


async def update_approval_status(
    db: AsyncSession,
    action_id: UUID,
    status: ActionStatus,
    approved_by: Optional[str] = None,
) -> Optional["AgentActionLogRecord"]:
    """Update the approval status of an action."""
    from app.models.agent import AgentActionLog
    
    result = await db.execute(
        select(AgentActionLog).where(AgentActionLog.id == action_id)
    )
    log_entry = result.scalar_one_or_none()
    
    if not log_entry:
        return None
    
    log_entry.approval_status = status.value
    log_entry.approved_by = approved_by
    log_entry.approval_timestamp = datetime.utcnow()
    
    await db.flush()
    return log_entry


async def get_action_by_id(
    db: AsyncSession,
    action_id: UUID,
) -> Optional["AgentActionLogRecord"]:
    """Get a specific action by ID."""
    from app.models.agent import AgentActionLog
    
    result = await db.execute(
        select(AgentActionLog).where(AgentActionLog.id == action_id)
    )
    return result.scalar_one_or_none()


# Type alias for external use
AgentActionLogRecord = Any  # Will be AgentActionLog model at runtime
