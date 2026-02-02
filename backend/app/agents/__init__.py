"""
IDKit Agent Package

Exports all agent classes and utilities.
"""

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
    ActionCategory,
    PROHIBITED_ACTIONS,
    GATED_ACTIONS,
    AUTONOMOUS_ACTIONS,
    classify_action,
    check_action_allowed,
    requires_approval,
    agent_can_perform,
)

from app.agents.orchestrator import OrchestratorAgent
from app.agents.content_agent import ContentAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.publishing_agent import PublishingAgent


def create_crew() -> OrchestratorAgent:
    """
    Create and configure the full IDKit agent crew.
    
    Returns an orchestrator with all specialist agents registered.
    """
    orchestrator = OrchestratorAgent()
    
    # Register all specialist agents
    orchestrator.register_agent(ContentAgent())
    orchestrator.register_agent(AnalyticsAgent())
    orchestrator.register_agent(PublishingAgent())
    
    return orchestrator


__all__ = [
    # Base
    "AgentContext",
    "AgentResult",
    "AgentTask",
    "AgentType",
    "AutonomyLevel",
    "BaseAgent",
    "ActionStatus",
    "EvidenceItem",
    # Guardrails
    "ActionCategory",
    "PROHIBITED_ACTIONS",
    "GATED_ACTIONS",
    "AUTONOMOUS_ACTIONS",
    "classify_action",
    "check_action_allowed",
    "requires_approval",
    "agent_can_perform",
    # Agents
    "OrchestratorAgent",
    "ContentAgent",
    "AnalyticsAgent",
    "PublishingAgent",
    # Factory
    "create_crew",
]
