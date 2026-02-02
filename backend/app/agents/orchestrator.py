"""
Orchestrator Agent

Central coordinator that routes tasks to specialist agents.
Manages priority, prevents infinite loops, and enforces approval gates.
"""

from typing import Dict, List, Optional, Type
from uuid import uuid4

from app.agents.base import (
    AgentContext,
    AgentResult,
    AgentTask,
    AgentType,
    AutonomyLevel,
    BaseAgent,
    ActionStatus,
    EvidenceItem,
)
from app.agents.guardrails import (
    check_action_allowed,
    requires_approval,
    get_approval_message,
    classify_action,
    ActionCategory,
)


class OrchestratorAgent(BaseAgent):
    """
    Central orchestrator that coordinates all specialist agents.
    
    Responsibilities:
    - Route incoming tasks to appropriate specialists
    - Manage task priority and execution order
    - Enforce safety guardrails and approval gates
    - Prevent infinite loops and priority starvation
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            autonomy_level=AutonomyLevel.MEDIUM,
        )
        self._agents: Dict[AgentType, BaseAgent] = {}
        self._max_delegation_depth = 3
        self._task_history: List[str] = []

    @property
    def name(self) -> str:
        return "Orchestrator"

    @property
    def description(self) -> str:
        return "Routes tasks to specialist agents and coordinates the AI crew"

    @property
    def capabilities(self) -> List[str]:
        return [
            "route_task",
            "delegate_task",
            "prioritize_tasks",
            "check_status",
            "coordinate_agents",
        ]

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a specialist agent with the orchestrator."""
        self._agents[agent.agent_type] = agent

    def get_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Get a registered agent by type."""
        return self._agents.get(agent_type)

    async def can_handle(self, task: AgentTask) -> bool:
        """Orchestrator can handle any task by routing it."""
        return True

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute a task by routing to the appropriate specialist.
        
        Flow:
        1. Determine which agent should handle the task
        2. Check if action is allowed (guardrails)
        3. Delegate to specialist agent
        4. Return result (possibly pending approval)
        """
        # Prevent infinite loops
        task_key = f"{task.task_type}:{task.task_id}"
        if task_key in self._task_history:
            return self._create_error_result(
                action_type="route_task",
                error="Infinite loop detected - task already in progress",
            )
        
        self._task_history.append(task_key)
        
        try:
            # Determine target agent
            target_agent = await self._select_agent(task)
            
            if not target_agent:
                return self._create_error_result(
                    action_type="route_task",
                    error=f"No agent available to handle task type: {task.task_type}",
                )
            
            # Check guardrails
            allowed, reason = check_action_allowed(
                action=task.task_type,
                agent_type=target_agent.agent_type,
                autonomy_level=target_agent.autonomy_level,
            )
            
            if not allowed:
                return self._create_error_result(
                    action_type="route_task",
                    error=reason or "Action not allowed",
                )
            
            # Delegate to specialist
            result = await target_agent.execute(task, context)
            
            # Check if approval is needed
            needs_approval, approval_reason = requires_approval(
                action=task.task_type,
                agent_type=target_agent.agent_type,
                autonomy_level=target_agent.autonomy_level,
            )
            
            if needs_approval:
                result.requires_approval = True
                result.approval_reason = approval_reason or get_approval_message(
                    task.task_type, target_agent.agent_type
                )
                result.status = ActionStatus.PENDING
            
            # Add routing evidence
            result.evidence.append(EvidenceItem(
                source_type="orchestration",
                source_name="OrchestratorAgent",
                data={
                    "routed_to": target_agent.agent_type.value,
                    "agent_confidence": await target_agent.get_confidence(task),
                },
                confidence=1.0,
            ))
            
            return result
            
        finally:
            # Clean up task history
            if task_key in self._task_history:
                self._task_history.remove(task_key)

    async def _select_agent(self, task: AgentTask) -> Optional[BaseAgent]:
        """
        Select the best agent to handle a task.
        
        Strategy:
        1. If task specifies target_agent, use that
        2. Otherwise, find agent with highest confidence
        """
        # Use specified target if provided
        if task.target_agent:
            return self._agents.get(task.target_agent)
        
        # Find best matching agent by task type
        task_type_mapping = {
            # Content tasks
            "generate_content": AgentType.CONTENT,
            "generate_draft": AgentType.CONTENT,
            "repurpose_content": AgentType.CONTENT,
            "suggest_improvements": AgentType.CONTENT,
            "generate_ideas": AgentType.CONTENT,
            
            # Analytics tasks
            "analyze_performance": AgentType.ANALYTICS,
            "get_insights": AgentType.ANALYTICS,
            "identify_trends": AgentType.ANALYTICS,
            "calculate_metrics": AgentType.ANALYTICS,
            
            # Publishing tasks
            "schedule_content": AgentType.PUBLISHING,
            "optimize_schedule": AgentType.PUBLISHING,
            "format_content": AgentType.PUBLISHING,
            
            # Discovery tasks
            "research_trends": AgentType.DISCOVERY,
            "analyze_competitors": AgentType.DISCOVERY,
            "find_collaborations": AgentType.DISCOVERY,
            "identify_niches": AgentType.DISCOVERY,
            "monitor_hashtags": AgentType.DISCOVERY,
            "discover": AgentType.DISCOVERY,
            
            # Engagement tasks
            "generate_dm_template": AgentType.ENGAGEMENT,
            "suggest_reply": AgentType.ENGAGEMENT,
            "analyze_sentiment": AgentType.ENGAGEMENT,
            "identify_top_fans": AgentType.ENGAGEMENT,
            "prioritize_inbox": AgentType.ENGAGEMENT,
            "engage": AgentType.ENGAGEMENT,
            
            # Revenue tasks
            "calculate_roi": AgentType.REVENUE,
            "analyze_deal": AgentType.REVENUE,
            "recommend_pricing": AgentType.REVENUE,
            "forecast_earnings": AgentType.REVENUE,
            "revenue": AgentType.REVENUE,
            
            # Moderation tasks
            "check_ftc_compliance": AgentType.MODERATION,
            "check_platform_compliance": AgentType.MODERATION,
            "assess_brand_safety": AgentType.MODERATION,
            "check_hashtags": AgentType.MODERATION,
            "compliance_check": AgentType.MODERATION,
            "moderate": AgentType.MODERATION,
        }
        
        target_type = task_type_mapping.get(task.task_type)
        if target_type and target_type in self._agents:
            return self._agents[target_type]
        
        # Fallback: find agent with highest confidence
        best_agent = None
        best_confidence = 0.0
        
        for agent in self._agents.values():
            if await agent.can_handle(task):
                confidence = await agent.get_confidence(task)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_agent = agent
        
        return best_agent

    async def get_available_agents(self) -> List[Dict]:
        """Get info about all registered agents."""
        return [
            {
                "type": agent.agent_type.value,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "autonomy_level": agent.autonomy_level.value,
            }
            for agent in self._agents.values()
        ]
