"""
Agent Guardrails

Safety boundaries and action classification for IDKit agents.
Enforces strict rules about what agents can and cannot do.
"""

from enum import Enum
from typing import List, Optional, Set

from app.agents.base import AgentType, AutonomyLevel


class ActionCategory(str, Enum):
    """Categories of agent actions."""
    PROHIBITED = "prohibited"   # Never allowed
    GATED = "gated"            # Requires human approval
    AUTONOMOUS = "autonomous"   # Allowed without approval


# =============================================================================
# ACTION DEFINITIONS
# =============================================================================

# Actions that are NEVER allowed regardless of context or permissions
PROHIBITED_ACTIONS: Set[str] = {
    # Publishing/Communication
    "publish_without_approval",
    "send_message_without_approval",
    "send_dm_without_approval",
    "post_comment_without_approval",
    
    # Financial
    "authorize_payment",
    "initiate_transfer",
    "sign_contract",
    "accept_deal",
    "modify_pricing",
    
    # Account Management
    "delete_content",
    "delete_account",
    "modify_account_settings",
    "change_password",
    "revoke_oauth",
    
    # Security
    "access_financial_credentials",
    "export_sensitive_data",
    "modify_permissions",
}

# Actions that require explicit human confirmation
GATED_ACTIONS: Set[str] = {
    # Publishing
    "schedule_publish",
    "queue_content",
    "update_scheduled_post",
    
    # Deals & Contracts
    "draft_contract",
    "suggest_price",
    "send_proposal",
    "negotiate_terms",
    
    # Content
    "repurpose_for_publish",
    "generate_final_draft",
    
    # Engagement
    "suggest_reply",
    "draft_dm",
    
    # Settings
    "update_preferences",
    "modify_schedule_rules",
}

# Actions allowed autonomously (no side effects or read-only)
AUTONOMOUS_ACTIONS: Set[str] = {
    # Analysis
    "analyze_data",
    "analyze_performance",
    "calculate_metrics",
    "identify_trends",
    "generate_insights",
    "benchmark_comparison",
    
    # Content Generation (drafts only)
    "generate_draft",
    "generate_ideas",
    "suggest_improvements",
    "check_grammar",
    "optimize_seo",
    
    # Research
    "research_trends",
    "research_competitors",
    "research_hashtags",
    "find_opportunities",
    
    # Compliance
    "check_compliance",
    "check_ftc_disclosure",
    "validate_content",
    "scan_for_issues",
    
    # Formatting
    "format_content",
    "resize_media",
    "generate_thumbnail_suggestions",
    
    # Read-only queries
    "get_analytics",
    "get_schedule",
    "get_history",
    "get_recommendations",
}


# =============================================================================
# GUARDRAIL FUNCTIONS
# =============================================================================

def classify_action(action: str) -> ActionCategory:
    """
    Classify an action into its category.
    
    Returns:
        ActionCategory.PROHIBITED - Action is never allowed
        ActionCategory.GATED - Action requires human approval
        ActionCategory.AUTONOMOUS - Action can proceed automatically
    """
    action_lower = action.lower().strip()
    
    if action_lower in PROHIBITED_ACTIONS:
        return ActionCategory.PROHIBITED
    
    if action_lower in GATED_ACTIONS:
        return ActionCategory.GATED
    
    if action_lower in AUTONOMOUS_ACTIONS:
        return ActionCategory.AUTONOMOUS
    
    # Unknown actions default to GATED for safety
    return ActionCategory.GATED


def check_action_allowed(
    action: str,
    agent_type: AgentType,
    autonomy_level: AutonomyLevel,
) -> tuple[bool, Optional[str]]:
    """
    Check if an action is allowed for a given agent.
    
    Returns:
        (allowed: bool, reason: Optional[str])
        - If allowed is False, reason explains why
        - If allowed is True but requires approval, reason is None
    """
    category = classify_action(action)
    
    # Prohibited actions are never allowed
    if category == ActionCategory.PROHIBITED:
        return False, f"Action '{action}' is prohibited and cannot be executed"
    
    # Autonomous actions are always allowed
    if category == ActionCategory.AUTONOMOUS:
        return True, None
    
    # Gated actions depend on autonomy level
    if category == ActionCategory.GATED:
        if autonomy_level == AutonomyLevel.HIGH:
            # High autonomy agents can do gated actions
            # But still log them for audit
            return True, None
        else:
            # Medium/Low autonomy requires approval
            return True, None  # Allowed but will need approval
    
    return True, None


def requires_approval(
    action: str,
    agent_type: AgentType,
    autonomy_level: AutonomyLevel,
) -> tuple[bool, Optional[str]]:
    """
    Check if an action requires human approval before execution.
    
    Returns:
        (requires: bool, reason: Optional[str])
    """
    category = classify_action(action)
    
    # Prohibited actions should never reach this point
    if category == ActionCategory.PROHIBITED:
        return True, f"Prohibited action: {action}"
    
    # Autonomous actions never need approval
    if category == ActionCategory.AUTONOMOUS:
        return False, None
    
    # Gated actions need approval based on autonomy level
    if category == ActionCategory.GATED:
        if autonomy_level == AutonomyLevel.HIGH:
            return False, None  # High autonomy can auto-approve
        elif autonomy_level == AutonomyLevel.MEDIUM:
            return True, f"Action '{action}' requires confirmation"
        else:  # LOW
            return True, f"Action '{action}' requires approval (low autonomy agent)"
    
    # Default to requiring approval for safety
    return True, "Unknown action type - defaulting to require approval"


def get_approval_message(action: str, agent_type: AgentType) -> str:
    """Generate a human-readable approval request message."""
    messages = {
        "schedule_publish": "The AI wants to schedule content for publishing. Please review and confirm.",
        "draft_contract": "A contract draft has been generated. Please review before sending.",
        "suggest_price": "A pricing recommendation has been generated. Please confirm before sharing.",
        "send_proposal": "A proposal is ready to send. Please review and approve.",
        "generate_final_draft": "Final content is ready. Please review before use.",
    }
    
    return messages.get(
        action,
        f"The {agent_type.value} agent is requesting approval for: {action}"
    )


# =============================================================================
# AGENT-SPECIFIC RULES
# =============================================================================

# Actions each agent type is allowed to perform
AGENT_ALLOWED_ACTIONS: dict[AgentType, Set[str]] = {
    AgentType.ORCHESTRATOR: {
        "route_task",
        "prioritize_tasks",
        "delegate_task",
        "check_status",
    },
    AgentType.CONTENT: {
        "generate_draft",
        "generate_ideas",
        "suggest_improvements",
        "repurpose_for_publish",
        "check_grammar",
        "optimize_seo",
    },
    AgentType.ANALYTICS: {
        "analyze_data",
        "analyze_performance",
        "calculate_metrics",
        "identify_trends",
        "generate_insights",
        "benchmark_comparison",
        "get_analytics",
    },
    AgentType.PUBLISHING: {
        "schedule_publish",
        "queue_content",
        "format_content",
        "optimize_schedule",
        "get_schedule",
    },
    AgentType.REVENUE: {
        "analyze_data",
        "calculate_metrics",
        "suggest_price",
        "draft_contract",
        "negotiate_terms",
    },
    AgentType.ENGAGEMENT: {
        "suggest_reply",
        "draft_dm",
        "analyze_data",
        "identify_trends",
    },
    AgentType.DISCOVERY: {
        "research_trends",
        "research_competitors",
        "research_hashtags",
        "find_opportunities",
        "analyze_data",
    },
    AgentType.MODERATION: {
        "check_compliance",
        "check_ftc_disclosure",
        "validate_content",
        "scan_for_issues",
    },
}


def agent_can_perform(agent_type: AgentType, action: str) -> bool:
    """Check if a specific agent type is allowed to perform an action."""
    allowed = AGENT_ALLOWED_ACTIONS.get(agent_type, set())
    
    # Orchestrator can delegate any action
    if agent_type == AgentType.ORCHESTRATOR:
        return True
    
    return action.lower() in allowed


# Package init
__all__ = [
    "ActionCategory",
    "PROHIBITED_ACTIONS",
    "GATED_ACTIONS",
    "AUTONOMOUS_ACTIONS",
    "classify_action",
    "check_action_allowed",
    "requires_approval",
    "get_approval_message",
    "agent_can_perform",
]
