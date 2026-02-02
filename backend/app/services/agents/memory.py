"""
Agent Memory Service

Provides persistent memory capabilities for IDKit AI agents.
Manages storage, retrieval, and context building for agent interactions.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentType
from app.models.agent_memory import (
    AgentContext,
    AgentMemory,
    GuardrailConfig,
    MemoryType,
)


class AgentMemoryService:
    """
    Service for managing agent memory and context.
    
    Provides:
    - Short-term memory (last 10 interactions, expires in 24h)
    - Long-term memory (summarized patterns, persists 90 days)
    - Context building for agent prompts
    - Memory retrieval with relevance scoring
    """

    # Memory limits
    MAX_SHORT_TERM_MEMORIES = 10
    SHORT_TERM_EXPIRY_HOURS = 24
    LONG_TERM_EXPIRY_DAYS = 90
    MAX_CONTEXT_MEMORIES = 5

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Memory Storage ====================

    async def store_memory(
        self,
        user_id: UUID,
        agent_type: AgentType | str,
        content: dict[str, Any],
        summary: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        tags: list[str] | None = None,
        importance_score: float = 0.5,
        task_id: UUID | None = None,
    ) -> AgentMemory:
        """Store a new memory for an agent."""
        # Convert agent_type to string if enum
        agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type
        
        # Calculate expiration
        expires_at = None
        if memory_type == MemoryType.SHORT_TERM:
            expires_at = datetime.utcnow() + timedelta(hours=self.SHORT_TERM_EXPIRY_HOURS)
        elif memory_type == MemoryType.LONG_TERM:
            expires_at = datetime.utcnow() + timedelta(days=self.LONG_TERM_EXPIRY_DAYS)

        memory = AgentMemory(
            user_id=user_id,
            agent_type=agent_type_str,
            memory_type=memory_type.value,
            content=content,
            summary=summary,
            tags=tags,
            importance_score=importance_score,
            task_id=task_id,
            expires_at=expires_at,
        )

        self.db.add(memory)
        await self.db.flush()

        # Enforce short-term memory limit
        if memory_type == MemoryType.SHORT_TERM:
            await self._enforce_memory_limit(user_id, agent_type_str)

        return memory

    async def _enforce_memory_limit(
        self,
        user_id: UUID,
        agent_type: str,
    ) -> None:
        """Remove oldest short-term memories beyond limit."""
        # Get all short-term memories for this user/agent
        result = await self.db.execute(
            select(AgentMemory)
            .where(
                AgentMemory.user_id == user_id,
                AgentMemory.agent_type == agent_type,
                AgentMemory.memory_type == MemoryType.SHORT_TERM.value,
            )
            .order_by(AgentMemory.created_at.desc())
        )
        memories = result.scalars().all()

        # Delete excess memories
        if len(memories) > self.MAX_SHORT_TERM_MEMORIES:
            excess_ids = [m.id for m in memories[self.MAX_SHORT_TERM_MEMORIES:]]
            await self.db.execute(
                delete(AgentMemory).where(AgentMemory.id.in_(excess_ids))
            )

    # ==================== Memory Retrieval ====================

    async def get_relevant_memories(
        self,
        user_id: UUID,
        agent_type: AgentType | str | None = None,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[AgentMemory]:
        """
        Retrieve relevant memories for context building.
        
        Returns memories sorted by importance and recency.
        """
        agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type

        query = (
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .where(
                (AgentMemory.expires_at.is_(None)) |
                (AgentMemory.expires_at > datetime.utcnow())
            )
        )

        if agent_type_str:
            query = query.where(AgentMemory.agent_type == agent_type_str)

        if memory_type:
            query = query.where(AgentMemory.memory_type == memory_type.value)

        if tags:
            query = query.where(AgentMemory.tags.overlap(tags))

        # Sort by importance * recency
        query = query.order_by(
            AgentMemory.importance_score.desc(),
            AgentMemory.created_at.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        memories = result.scalars().all()

        # Update access tracking
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed_at = datetime.utcnow()

        return list(memories)

    async def get_memory_summary(
        self,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Get summary of all memories for a user."""
        result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .where(
                (AgentMemory.expires_at.is_(None)) |
                (AgentMemory.expires_at > datetime.utcnow())
            )
        )
        memories = result.scalars().all()

        # Group by agent type
        by_agent: dict[str, list[dict]] = {}
        for memory in memories:
            if memory.agent_type not in by_agent:
                by_agent[memory.agent_type] = []
            by_agent[memory.agent_type].append({
                "id": str(memory.id),
                "summary": memory.summary,
                "memory_type": memory.memory_type,
                "importance": memory.importance_score,
                "created_at": memory.created_at.isoformat(),
            })

        return {
            "total_memories": len(memories),
            "by_agent": by_agent,
        }

    # ==================== Context Management ====================

    async def get_or_create_context(
        self,
        user_id: UUID,
    ) -> AgentContext:
        """Get or create agent context for a user."""
        result = await self.db.execute(
            select(AgentContext).where(AgentContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()

        if not context:
            context = AgentContext(
                user_id=user_id,
                active_context={},
                learned_preferences={},
            )
            self.db.add(context)
            await self.db.flush()

        return context

    async def build_agent_context(
        self,
        user_id: UUID,
        agent_type: AgentType | str,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Build context for an agent interaction.
        
        Retrieves relevant memories and combines with user preferences
        to create a rich context for the agent.
        """
        agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type

        # Get recent memories from this agent
        agent_memories = await self.get_relevant_memories(
            user_id=user_id,
            agent_type=agent_type_str,
            limit=self.MAX_CONTEXT_MEMORIES,
        )

        # Get long-term memories
        long_term = await self.get_relevant_memories(
            user_id=user_id,
            memory_type=MemoryType.LONG_TERM,
            limit=3,
        )

        # Get user context
        context = await self.get_or_create_context(user_id)

        # Update interaction stats
        context.total_interactions += 1
        context.last_interaction_at = datetime.utcnow()
        context.active_memory_ids = [str(m.id) for m in agent_memories]

        return {
            "recent_interactions": [
                {"summary": m.summary, "content": m.content}
                for m in agent_memories
            ],
            "long_term_context": [
                {"summary": m.summary, "importance": m.importance_score}
                for m in long_term
            ],
            "learned_preferences": context.learned_preferences,
            "total_interactions": context.total_interactions,
        }

    async def update_learned_preference(
        self,
        user_id: UUID,
        key: str,
        value: Any,
    ) -> None:
        """Update a learned preference for the user."""
        context = await self.get_or_create_context(user_id)
        context.learned_preferences[key] = value
        await self.db.flush()

    # ==================== Memory Cleanup ====================

    async def clear_user_memories(
        self,
        user_id: UUID,
        agent_type: AgentType | str | None = None,
    ) -> int:
        """Clear all memories for a user, optionally filtered by agent."""
        query = delete(AgentMemory).where(AgentMemory.user_id == user_id)
        
        if agent_type:
            agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type
            query = query.where(AgentMemory.agent_type == agent_type_str)

        result = await self.db.execute(query)
        return result.rowcount

    async def cleanup_expired_memories(self) -> int:
        """Remove all expired memories (for scheduled job)."""
        result = await self.db.execute(
            delete(AgentMemory).where(
                AgentMemory.expires_at.isnot(None),
                AgentMemory.expires_at < datetime.utcnow(),
            )
        )
        return result.rowcount

    # ==================== Guardrail Config ====================

    async def get_guardrail_config(
        self,
        user_id: UUID,
    ) -> GuardrailConfig:
        """Get or create guardrail config for a user."""
        result = await self.db.execute(
            select(GuardrailConfig).where(GuardrailConfig.user_id == user_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = GuardrailConfig(
                user_id=user_id,
                action_permissions={},
                agent_autonomy={},
                auto_approve_thresholds={},
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def update_guardrail_config(
        self,
        user_id: UUID,
        action_permissions: dict[str, str] | None = None,
        agent_autonomy: dict[str, str] | None = None,
        auto_approve_thresholds: dict[str, float] | None = None,
        risk_tolerance: str | None = None,
    ) -> GuardrailConfig:
        """Update guardrail configuration for a user."""
        config = await self.get_guardrail_config(user_id)

        if action_permissions is not None:
            config.action_permissions = action_permissions
        if agent_autonomy is not None:
            config.agent_autonomy = agent_autonomy
        if auto_approve_thresholds is not None:
            config.auto_approve_thresholds = auto_approve_thresholds
        if risk_tolerance is not None:
            config.risk_tolerance = risk_tolerance

        await self.db.flush()
        return config
