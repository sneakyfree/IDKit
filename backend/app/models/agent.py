"""
Agent Database Models

SQLAlchemy models for agent tasks, action logs, and pending approvals.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentTask(Base, UUIDMixin, TimestampMixin):
    """A task submitted to the agent system."""

    __tablename__ = "agent_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Task definition
    task_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    inputs: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # Routing
    target_agent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Result reference
    result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AgentTask {self.task_type} status={self.status}>"


class AgentActionLog(Base, UUIDMixin, TimestampMixin):
    """Immutable audit log of all agent actions."""

    __tablename__ = "agent_action_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Agent info
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    trigger: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="user_request",
    )

    # Task reference
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    task_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    task_inputs: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Result
    result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    output: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    output_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Confidence and reasoning
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Evidence chain
    evidence: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Approval tracking
    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    approval_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="auto_approved",
        index=True,
    )

    approval_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    approval_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Execution status
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AgentActionLog {self.agent_type}:{self.action_type}>"


class PendingApproval(Base, UUIDMixin, TimestampMixin):
    """Actions awaiting human approval."""

    __tablename__ = "pending_approvals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_action_logs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Action info
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Display
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Preview data
    preview_content: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Priority
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Expiry
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<PendingApproval {self.action_type} status={self.status}>"
