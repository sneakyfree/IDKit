"""
Agent Memory Model

Persistent memory system for IDKit AI agents.
Enables context-aware interactions by storing and retrieving
agent interaction history and learned user patterns.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class MemoryType(str, Enum):
    """Types of agent memory."""
    SHORT_TERM = "short_term"  # Recent interactions, expires quickly
    LONG_TERM = "long_term"    # Summarized patterns, persists longer
    EPISODIC = "episodic"      # Specific interaction episodes
    SEMANTIC = "semantic"      # Learned facts about user


class AgentMemory(Base, UUIDMixin, TimestampMixin):
    """
    Persistent memory for AI agents.
    
    Stores interaction history, learned patterns, and context
    to enable continuity across agent conversations.
    """

    __tablename__ = "agent_memories"

    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Agent that created this memory
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Memory classification
    memory_type: Mapped[str] = mapped_column(
        String(20),
        default=MemoryType.SHORT_TERM.value,
        nullable=False,
    )

    # Memory content
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Summary for quick retrieval
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Tags for categorization
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Relevance scoring
    importance_score: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
    )

    # Access tracking
    access_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Expiration for short-term memories
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Task association (which task created this memory)
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("idx_agent_memory_user_agent", "user_id", "agent_type"),
        Index("idx_agent_memory_type", "memory_type"),
        Index("idx_agent_memory_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentMemory {self.agent_type}:{self.memory_type}>"


class AgentContext(Base, UUIDMixin, TimestampMixin):
    """
    Active context for an agent session.
    
    Aggregates relevant memories and provides current
    working context for agent interactions.
    """

    __tablename__ = "agent_contexts"

    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Current active context
    active_context: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Recently retrieved memory IDs
    active_memory_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # User preferences learned by agents
    learned_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Interaction stats
    total_interactions: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AgentContext user={self.user_id}>"


class GuardrailConfig(Base, UUIDMixin, TimestampMixin):
    """
    User-specific guardrail configuration for agents.
    
    Allows users to customize agent autonomy levels
    and permission settings per action category.
    """

    __tablename__ = "guardrail_configs"

    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Per-action category settings
    # Format: {"publishing": "gated", "financial": "prohibited", ...}
    action_permissions: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Per-agent autonomy overrides
    # Format: {"content": "high", "revenue": "low", ...}
    agent_autonomy: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Auto-approve thresholds by category
    # Format: {"analytics": 0.9, "content": 0.7}
    auto_approve_thresholds: Mapped[dict[str, float]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Risk tolerance setting
    risk_tolerance: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )  # 'conservative', 'medium', 'aggressive'

    def __repr__(self) -> str:
        return f"<GuardrailConfig user={self.user_id}>"
