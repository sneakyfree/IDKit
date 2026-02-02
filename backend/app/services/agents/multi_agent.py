"""
Multi-Agent Orchestration Service

Enables parallel task execution, dependency resolution, and collaborative
workflows between multiple AI agents.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 20


class CollaborationPattern(str, Enum):
    """Multi-agent collaboration patterns."""
    SEQUENTIAL = "sequential"  # A -> B -> C
    PARALLEL = "parallel"      # A, B, C (all at once)
    PIPELINE = "pipeline"      # A outputs feed B, B feeds C
    VOTING = "voting"          # All agents vote on decision
    REVIEW = "review"          # Primary agent + reviewer agents


class AgentTask(BaseModel):
    """Represents a task to be executed by an agent."""
    
    task_id: UUID = Field(default_factory=uuid4)
    agent_type: str
    task_type: str
    description: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[UUID] = Field(default_factory=list)
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_collaboration_id: Optional[UUID] = None
    
    class Config:
        use_enum_values = True


class Collaboration(BaseModel):
    """Represents a multi-agent collaboration."""
    
    collaboration_id: UUID = Field(default_factory=uuid4)
    pattern: CollaborationPattern
    participating_agents: list[str]
    tasks: list[AgentTask] = Field(default_factory=list)
    current_phase: str = "initializing"
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    final_result: Optional[dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class MultiAgentOrchestrator:
    """
    Orchestrates parallel and collaborative task execution across multiple agents.
    
    Features:
    - Parallel task execution with dependency resolution
    - Multiple collaboration patterns (sequential, parallel, pipeline, voting)
    - Task priority queue
    - Result aggregation
    - WebSocket status broadcasting
    """
    
    def __init__(self):
        self._tasks: dict[UUID, AgentTask] = {}
        self._collaborations: dict[UUID, Collaboration] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._agent_registry: dict[str, Callable] = {}
        self._running_tasks: set[UUID] = set()
        self._max_concurrent_tasks = 5
        self._broadcaster: Optional[Any] = None
        
    def set_broadcaster(self, broadcaster: Any) -> None:
        """Set the WebSocket broadcaster for status updates."""
        self._broadcaster = broadcaster
    
    def register_agent(
        self,
        agent_type: str,
        executor: Callable[[AgentTask], Any],
    ) -> None:
        """Register an agent executor function."""
        self._agent_registry[agent_type] = executor
    
    async def submit_task(
        self,
        agent_type: str,
        task_type: str,
        description: str,
        input_data: dict[str, Any] = {},
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: list[UUID] = [],
    ) -> AgentTask:
        """Submit a single task for execution."""
        task = AgentTask(
            agent_type=agent_type,
            task_type=task_type,
            description=description,
            input_data=input_data,
            priority=priority,
            dependencies=dependencies,
        )
        
        self._tasks[task.task_id] = task
        
        # Check if ready to run
        if self._are_dependencies_met(task):
            task.status = TaskStatus.READY
            await self._enqueue_task(task)
        else:
            task.status = TaskStatus.BLOCKED
        
        return task
    
    async def submit_batch(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[AgentTask]:
        """Submit multiple tasks at once, respecting dependencies."""
        submitted = []
        for task_spec in tasks:
            task = await self.submit_task(**task_spec)
            submitted.append(task)
        return submitted
    
    async def start_collaboration(
        self,
        pattern: CollaborationPattern,
        agents: list[str],
        task_specs: list[dict[str, Any]],
    ) -> Collaboration:
        """Start a multi-agent collaboration."""
        
        collaboration = Collaboration(
            pattern=pattern,
            participating_agents=agents,
            current_phase="preparing",
        )
        
        # Create tasks based on pattern
        if pattern == CollaborationPattern.SEQUENTIAL:
            tasks = await self._create_sequential_tasks(
                collaboration.collaboration_id,
                task_specs,
            )
        elif pattern == CollaborationPattern.PARALLEL:
            tasks = await self._create_parallel_tasks(
                collaboration.collaboration_id,
                task_specs,
            )
        elif pattern == CollaborationPattern.PIPELINE:
            tasks = await self._create_pipeline_tasks(
                collaboration.collaboration_id,
                task_specs,
            )
        else:
            tasks = await self._create_parallel_tasks(
                collaboration.collaboration_id,
                task_specs,
            )
        
        collaboration.tasks = tasks
        collaboration.status = TaskStatus.RUNNING
        collaboration.current_phase = "executing"
        
        self._collaborations[collaboration.collaboration_id] = collaboration
        
        # Broadcast start
        if self._broadcaster:
            await self._broadcaster.start_collaboration(
                collaboration.collaboration_id,
                agents,
                "executing",
            )
        
        return collaboration
    
    async def _create_sequential_tasks(
        self,
        collaboration_id: UUID,
        task_specs: list[dict[str, Any]],
    ) -> list[AgentTask]:
        """Create tasks that execute one after another."""
        tasks = []
        prev_task_id: Optional[UUID] = None
        
        for spec in task_specs:
            dependencies = [prev_task_id] if prev_task_id else []
            task = await self.submit_task(
                **spec,
                dependencies=dependencies,
            )
            task.parent_collaboration_id = collaboration_id
            tasks.append(task)
            prev_task_id = task.task_id
        
        return tasks
    
    async def _create_parallel_tasks(
        self,
        collaboration_id: UUID,
        task_specs: list[dict[str, Any]],
    ) -> list[AgentTask]:
        """Create tasks that execute in parallel."""
        tasks = []
        for spec in task_specs:
            task = await self.submit_task(**spec, dependencies=[])
            task.parent_collaboration_id = collaboration_id
            tasks.append(task)
        return tasks
    
    async def _create_pipeline_tasks(
        self,
        collaboration_id: UUID,
        task_specs: list[dict[str, Any]],
    ) -> list[AgentTask]:
        """Create pipeline tasks where output feeds into next input."""
        tasks = []
        prev_task_id: Optional[UUID] = None
        
        for i, spec in enumerate(task_specs):
            dependencies = [prev_task_id] if prev_task_id else []
            # Mark as pipeline task to pass result to next
            spec["input_data"] = spec.get("input_data", {})
            spec["input_data"]["_pipeline_position"] = i
            
            task = await self.submit_task(**spec, dependencies=dependencies)
            task.parent_collaboration_id = collaboration_id
            tasks.append(task)
            prev_task_id = task.task_id
        
        return tasks
    
    def _are_dependencies_met(self, task: AgentTask) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def _enqueue_task(self, task: AgentTask) -> None:
        """Add task to priority queue."""
        # Lower priority number = higher priority in queue
        priority_value = -task.priority if isinstance(task.priority, int) else -task.priority.value
        await self._task_queue.put((priority_value, task.task_id))
    
    async def run_worker(self) -> None:
        """Run the task execution worker."""
        while True:
            try:
                # Wait for a task
                _, task_id = await self._task_queue.get()
                
                task = self._tasks.get(task_id)
                if not task or task.status != TaskStatus.READY:
                    continue
                
                # Check concurrency limit
                while len(self._running_tasks) >= self._max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                
                # Execute task
                asyncio.create_task(self._execute_task(task))
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: AgentTask) -> None:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self._running_tasks.add(task.task_id)
        
        # Broadcast start
        if self._broadcaster:
            await self._broadcaster.start_task(
                agent_id=task.agent_type,
                task_id=task.task_id,
                task_type=task.task_type,
                task_description=task.description,
            )
        
        try:
            executor = self._agent_registry.get(task.agent_type)
            if not executor:
                raise ValueError(f"No executor registered for agent: {task.agent_type}")
            
            # Get results from dependencies if pipeline
            if task.input_data.get("_pipeline_position", 0) > 0:
                for dep_id in task.dependencies:
                    dep_task = self._tasks.get(dep_id)
                    if dep_task and dep_task.result:
                        task.input_data["_previous_result"] = dep_task.result
            
            # Execute
            result = await executor(task)
            
            task.result = result if isinstance(result, dict) else {"result": result}
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            duration = (task.completed_at - task.started_at).total_seconds()
            
            # Broadcast completion
            if self._broadcaster:
                await self._broadcaster.complete_task(
                    agent_id=task.agent_type,
                    task_id=task.task_id,
                    result_summary=str(task.result)[:200],
                    duration_seconds=duration,
                    requires_approval=False,
                )
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
        
        finally:
            self._running_tasks.discard(task.task_id)
            
            # Unblock dependent tasks
            await self._check_blocked_tasks()
            
            # Update collaboration if part of one
            if task.parent_collaboration_id:
                await self._update_collaboration(task.parent_collaboration_id)
    
    async def _check_blocked_tasks(self) -> None:
        """Check blocked tasks to see if they can now run."""
        for task in self._tasks.values():
            if task.status == TaskStatus.BLOCKED:
                if self._are_dependencies_met(task):
                    task.status = TaskStatus.READY
                    await self._enqueue_task(task)
    
    async def _update_collaboration(self, collaboration_id: UUID) -> None:
        """Update collaboration status after task completion."""
        collab = self._collaborations.get(collaboration_id)
        if not collab:
            return
        
        # Check all tasks
        all_completed = all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for t in collab.tasks
        )
        any_failed = any(t.status == TaskStatus.FAILED for t in collab.tasks)
        
        if all_completed:
            collab.completed_at = datetime.utcnow()
            collab.current_phase = "completed"
            collab.status = TaskStatus.FAILED if any_failed else TaskStatus.COMPLETED
            
            # Aggregate results
            collab.final_result = {
                "tasks": [
                    {
                        "agent": t.agent_type,
                        "status": t.status,
                        "result": t.result,
                        "error": t.error,
                    }
                    for t in collab.tasks
                ],
                "success": not any_failed,
            }
        
        # Broadcast update
        if self._broadcaster:
            completed_agents = [
                t.agent_type for t in collab.tasks
                if t.status == TaskStatus.COMPLETED
            ]
            running_agents = [
                t.agent_type for t in collab.tasks
                if t.status == TaskStatus.RUNNING
            ]
            
            handoff_from = completed_agents[-1] if completed_agents else None
            handoff_to = running_agents[0] if running_agents else None
            
            await self._broadcaster.update_collaboration(
                collaboration_id=collaboration_id,
                current_phase=collab.current_phase,
                handoff_from=handoff_from,
                handoff_to=handoff_to,
            )
    
    def get_task_status(self, task_id: UUID) -> Optional[AgentTask]:
        """Get status of a specific task."""
        return self._tasks.get(task_id)
    
    def get_collaboration_status(
        self,
        collaboration_id: UUID,
    ) -> Optional[Collaboration]:
        """Get status of a collaboration."""
        return self._collaborations.get(collaboration_id)
    
    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a pending or blocked task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.BLOCKED, TaskStatus.READY]:
            task.status = TaskStatus.CANCELLED
            return True
        
        return False
    
    def get_queue_stats(self) -> dict:
        """Get current queue statistics."""
        status_counts = {}
        for task in self._tasks.values():
            status = task.status if isinstance(task.status, str) else task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self._tasks),
            "running_tasks": len(self._running_tasks),
            "queued_tasks": self._task_queue.qsize(),
            "status_breakdown": status_counts,
            "active_collaborations": len([
                c for c in self._collaborations.values()
                if c.status == TaskStatus.RUNNING
            ]),
        }


# Global orchestrator instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator
