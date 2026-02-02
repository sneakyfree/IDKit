"""
Agent Service

Orchestrates agent execution with logging and approval handling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import (
    AgentContext,
    AgentResult,
    AgentTask,
    AgentType,
    ActionStatus,
    create_crew,
)
from app.agents.action_log import (
    log_action,
    get_pending_approvals,
    update_approval_status,
    get_action_history,
)
from app.models.agent import AgentTask as AgentTaskModel, PendingApproval


class AgentService:
    """
    Service for managing agent task execution.
    
    Handles:
    - Task submission and routing
    - Action logging
    - Approval workflows
    - Result retrieval
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = create_crew()

    async def submit_task(
        self,
        user_id: UUID,
        task_type: str,
        description: str = "",
        inputs: Optional[Dict[str, Any]] = None,
        target_agent: Optional[AgentType] = None,
        priority: int = 5,
    ) -> AgentResult:
        """
        Submit a task for agent processing.
        
        Returns the result (possibly with requires_approval=True).
        """
        # Create task object
        task = AgentTask(
            task_id=uuid4(),
            task_type=task_type,
            description=description,
            inputs=inputs or {},
            target_agent=target_agent,
            priority=priority,
        )

        # Create context
        context = AgentContext(
            user_id=user_id,
            request_id=uuid4(),
        )

        # Store task in database
        db_task = AgentTaskModel(
            id=task.task_id,
            user_id=user_id,
            task_type=task_type,
            description=description,
            inputs=inputs,
            target_agent=target_agent.value if target_agent else None,
            priority=priority,
            status="executing",
            started_at=datetime.utcnow(),
        )
        self.db.add(db_task)
        await self.db.flush()

        try:
            # Execute via orchestrator
            result = await self.orchestrator.execute(task, context)

            # Log the action
            await log_action(
                db=self.db,
                user_id=user_id,
                agent_type=result.agent_type,
                action_type=task_type,
                task=task,
                result=result,
            )

            # If approval needed, create pending approval record
            if result.requires_approval:
                approval = PendingApproval(
                    user_id=user_id,
                    action_log_id=result.result_id,
                    agent_type=result.agent_type.value,
                    action_type=task_type,
                    title=f"{result.agent_type.value.title()} Agent: {task_type}",
                    description=result.approval_reason,
                    preview_content=result.output if not isinstance(result.output, bytes) else None,
                    priority="high" if result.confidence < 0.7 else "medium",
                )
                self.db.add(approval)

            # Update task status
            db_task.status = "pending_approval" if result.requires_approval else "completed"
            db_task.completed_at = datetime.utcnow() if not result.requires_approval else None
            db_task.result_id = result.result_id

            await self.db.flush()
            return result

        except Exception as e:
            db_task.status = "failed"
            db_task.error = str(e)
            db_task.completed_at = datetime.utcnow()
            await self.db.flush()
            raise

    async def get_pending_approvals_for_user(
        self,
        user_id: UUID,
    ) -> List[Dict]:
        """Get all pending approvals for a user."""
        result = await self.db.execute(
            select(PendingApproval).where(
                PendingApproval.user_id == user_id,
                PendingApproval.status == "pending",
            ).order_by(PendingApproval.created_at.desc())
        )
        approvals = result.scalars().all()

        return [
            {
                "approval_id": str(a.id),
                "agent_type": a.agent_type,
                "action_type": a.action_type,
                "title": a.title,
                "description": a.description,
                "preview": a.preview_content,
                "priority": a.priority,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in approvals
        ]

    async def approve_action(
        self,
        user_id: UUID,
        approval_id: UUID,
        notes: Optional[str] = None,
    ) -> bool:
        """Approve a pending action."""
        result = await self.db.execute(
            select(PendingApproval).where(
                PendingApproval.id == approval_id,
                PendingApproval.user_id == user_id,
            )
        )
        approval = result.scalar_one_or_none()

        if not approval:
            return False

        approval.status = "approved"
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = str(user_id)
        approval.resolution_notes = notes

        # Update the action log
        await update_approval_status(
            db=self.db,
            action_id=approval.action_log_id,
            status=ActionStatus.APPROVED,
            approved_by=str(user_id),
        )

        await self.db.flush()
        return True

    async def reject_action(
        self,
        user_id: UUID,
        approval_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """Reject a pending action."""
        result = await self.db.execute(
            select(PendingApproval).where(
                PendingApproval.id == approval_id,
                PendingApproval.user_id == user_id,
            )
        )
        approval = result.scalar_one_or_none()

        if not approval:
            return False

        approval.status = "rejected"
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = str(user_id)
        approval.resolution_notes = reason

        # Update the action log
        await update_approval_status(
            db=self.db,
            action_id=approval.action_log_id,
            status=ActionStatus.REJECTED,
            approved_by=str(user_id),
        )

        await self.db.flush()
        return True

    async def get_action_history_for_user(
        self,
        user_id: UUID,
        agent_type: Optional[AgentType] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get agent action history for a user."""
        actions = await get_action_history(
            db=self.db,
            user_id=user_id,
            agent_type=agent_type,
            limit=limit,
        )

        return [
            {
                "action_id": str(a.id),
                "agent_type": a.agent_type,
                "action_type": a.action_type,
                "confidence": a.confidence,
                "reasoning": a.reasoning,
                "approval_status": a.approval_status,
                "success": a.success,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ]
