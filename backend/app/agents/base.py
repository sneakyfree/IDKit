"""
Base Agent Framework

Abstract base class and common patterns for all IDKit AI agents.
Implements bounded autonomy with confidence gating and evidence tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AgentType(str, Enum):
    """Types of agents in the IDKit crew."""
    ORCHESTRATOR = "orchestrator"
    CONTENT = "content"
    ANALYTICS = "analytics"
    PUBLISHING = "publishing"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    DISCOVERY = "discovery"
    MODERATION = "moderation"


class AutonomyLevel(str, Enum):
    """Level of autonomous action allowed."""
    HIGH = "high"       # Can act without approval (read-only operations)
    MEDIUM = "medium"   # Requires confirmation for some actions
    LOW = "low"         # Requires approval for most actions


class ActionStatus(str, Enum):
    """Status of an agent action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvidenceItem:
    """Evidence supporting an agent's decision or output."""
    evidence_id: UUID = field(default_factory=uuid4)
    source_type: str = ""  # api_data, user_input, calculation, research
    source_name: str = ""
    data: Any = None
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentContext:
    """Execution context passed to agents."""
    user_id: UUID
    request_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # User permissions and settings
    permissions: List[str] = field(default_factory=list)
    subscription_tier: str = "free"
    
    # Connected platforms for data access
    connected_platforms: List[str] = field(default_factory=list)
    
    # Additional context data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Standardized result from any agent action."""
    result_id: UUID = field(default_factory=uuid4)
    agent_type: AgentType = AgentType.ORCHESTRATOR
    action_type: str = ""
    
    # Execution status
    success: bool = True
    status: ActionStatus = ActionStatus.COMPLETED
    
    # Output
    output: Any = None
    output_type: str = ""  # draft, analysis, recommendation, schedule
    
    # Confidence and reasoning
    confidence: float = 1.0
    reasoning: str = ""
    
    # Evidence chain
    evidence: List[EvidenceItem] = field(default_factory=list)
    
    # Approval tracking
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    
    # Error handling
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class AgentTask:
    """A task submitted to an agent for processing."""
    task_id: UUID = field(default_factory=uuid4)
    task_type: str = ""
    description: str = ""
    
    # Input data
    inputs: Dict[str, Any] = field(default_factory=dict)
    
    # Routing
    target_agent: Optional[AgentType] = None
    priority: int = 5  # 1=highest, 10=lowest
    
    # Context
    context: Optional[AgentContext] = None
    
    # Status tracking
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """
    Abstract base class for all IDKit agents.
    
    All agents must implement:
    - can_handle(): Check if agent can process a task
    - execute(): Perform the agent's action
    - get_confidence(): Return confidence in ability to handle task
    """

    def __init__(
        self,
        agent_type: AgentType,
        autonomy_level: AutonomyLevel = AutonomyLevel.MEDIUM,
    ):
        self.agent_type = agent_type
        self.autonomy_level = autonomy_level
        self.agent_id = str(uuid4())

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this agent does."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List of task types this agent can handle."""
        pass

    @abstractmethod
    async def can_handle(self, task: AgentTask) -> bool:
        """
        Check if this agent can handle the given task.
        
        Returns True if the task type matches this agent's capabilities.
        """
        pass

    @abstractmethod
    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute the agent's action for the given task.
        
        Must return an AgentResult with:
        - output: The result of the action
        - confidence: How confident the agent is
        - reasoning: Explanation of the decision
        - evidence: Data sources used
        - requires_approval: Whether human approval needed
        """
        pass

    async def get_confidence(self, task: AgentTask) -> float:
        """
        Return confidence score (0-1) for handling this task.
        
        Default implementation returns 1.0 if can_handle() is True.
        Override for more nuanced confidence scoring.
        """
        if await self.can_handle(task):
            return 1.0
        return 0.0

    def _create_result(
        self,
        action_type: str,
        output: Any = None,
        confidence: float = 1.0,
        reasoning: str = "",
        requires_approval: bool = False,
        approval_reason: Optional[str] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResult:
        """Helper to create a standardized AgentResult."""
        return AgentResult(
            agent_type=self.agent_type,
            action_type=action_type,
            output=output,
            confidence=confidence,
            reasoning=reasoning,
            requires_approval=requires_approval,
            approval_reason=approval_reason,
            evidence=evidence or [],
            status=ActionStatus.PENDING if requires_approval else ActionStatus.COMPLETED,
        )

    def _create_error_result(
        self,
        action_type: str,
        error: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Helper to create an error result."""
        return AgentResult(
            agent_type=self.agent_type,
            action_type=action_type,
            success=False,
            status=ActionStatus.FAILED,
            error=error,
            error_details=error_details,
            confidence=0.0,
        )
