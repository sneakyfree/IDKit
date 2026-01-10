"""
Automation Services

Auto-reply, scheduling, and workflow automation.
"""

from app.services.automation.auto_reply import (
    AutoReplyService,
    AutoReplyRule,
    ReplyResult,
    RuleMatch,
    TriggerType,
    ReplyMode,
)

__all__ = [
    "AutoReplyService",
    "AutoReplyRule",
    "ReplyResult",
    "RuleMatch",
    "TriggerType",
    "ReplyMode",
]
