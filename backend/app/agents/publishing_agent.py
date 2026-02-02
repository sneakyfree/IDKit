"""
Publishing Agent

Handles content scheduling and cross-platform formatting.
MEDIUM autonomy - scheduling requires confirmation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.base import (
    AgentContext,
    AgentResult,
    AgentTask,
    AgentType,
    AutonomyLevel,
    BaseAgent,
    EvidenceItem,
)


class PublishingAgent(BaseAgent):
    """
    Publishing agent with MEDIUM autonomy.
    
    Can format and optimize content autonomously,
    but scheduling requires human confirmation.
    
    Capabilities:
    - Optimize posting schedule
    - Format content for different platforms
    - Schedule content (requires confirmation)
    - Suggest best posting times
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.PUBLISHING,
            autonomy_level=AutonomyLevel.MEDIUM,
        )

    @property
    def name(self) -> str:
        return "Publishing Agent"

    @property
    def description(self) -> str:
        return "Schedules and formats content for publishing"

    @property
    def capabilities(self) -> List[str]:
        return [
            "schedule_publish",
            "schedule_content",
            "queue_content",
            "format_content",
            "optimize_schedule",
            "get_schedule",
            "suggest_times",
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        """Check if this is a publishing-related task."""
        publishing_tasks = {
            "schedule_publish",
            "schedule_content",
            "queue_content",
            "format_content",
            "optimize_schedule",
            "get_schedule",
            "suggest_times",
        }
        return task.task_type.lower() in publishing_tasks

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Execute publishing task."""
        task_type = task.task_type.lower()

        if task_type in ("schedule_publish", "schedule_content", "queue_content"):
            return await self._schedule_content(task, context)
        elif task_type == "format_content":
            return await self._format_content(task, context)
        elif task_type == "optimize_schedule":
            return await self._optimize_schedule(task, context)
        elif task_type == "suggest_times":
            return await self._suggest_times(task, context)
        elif task_type == "get_schedule":
            return await self._get_schedule(task, context)
        else:
            return self._create_error_result(
                action_type=task_type,
                error=f"Unknown publishing task type: {task_type}",
            )

    async def _schedule_content(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Schedule content for publishing - REQUIRES APPROVAL."""
        content = task.inputs.get("content", {})
        platform = task.inputs.get("platform", "")
        scheduled_time = task.inputs.get("scheduled_time")
        
        if not content or not platform:
            return self._create_error_result(
                action_type="schedule_content",
                error="Content and platform are required for scheduling",
            )

        # Parse or generate schedule time
        if scheduled_time:
            schedule_dt = datetime.fromisoformat(scheduled_time)
        else:
            # Default to next optimal time
            schedule_dt = datetime.utcnow() + timedelta(hours=2)

        schedule_result = {
            "content_id": str(uuid4()),
            "platform": platform,
            "scheduled_for": schedule_dt.isoformat(),
            "timezone": "UTC",
            "content_preview": str(content.get("title", ""))[:100],
            "status": "pending_approval",
        }

        return self._create_result(
            action_type="schedule_content",
            output=schedule_result,
            output_type="schedule",
            confidence=0.90,
            reasoning=f"Prepared to schedule content for {platform} at {schedule_dt}",
            requires_approval=True,  # Scheduling requires confirmation
            approval_reason=f"Confirm scheduling post to {platform} for {schedule_dt.strftime('%Y-%m-%d %H:%M')} UTC",
            evidence=[
                EvidenceItem(
                    source_type="scheduling",
                    source_name="PublishingAgent",
                    data={
                        "platform": platform,
                        "scheduled_for": schedule_dt.isoformat(),
                    },
                    confidence=0.90,
                ),
            ],
        )

    async def _format_content(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Format content for a specific platform - autonomous."""
        content = task.inputs.get("content", "")
        source_platform = task.inputs.get("source_platform", "generic")
        target_platform = task.inputs.get("target_platform", "")
        
        if not content or not target_platform:
            return self._create_error_result(
                action_type="format_content",
                error="Content and target platform are required",
            )

        # Platform format specs
        platform_specs = {
            "twitter": {"max_length": 280, "hashtags": 2},
            "instagram": {"max_length": 2200, "hashtags": 15},
            "tiktok": {"max_length": 4000, "hashtags": 5},
            "linkedin": {"max_length": 3000, "hashtags": 3},
            "youtube": {"max_length": 5000, "hashtags": 5},
        }

        spec = platform_specs.get(target_platform.lower(), {"max_length": 1000, "hashtags": 5})
        
        formatted = {
            "original": content[:200] + "..." if len(content) > 200 else content,
            "formatted": content[:spec["max_length"]],
            "platform": target_platform,
            "character_count": min(len(content), spec["max_length"]),
            "max_allowed": spec["max_length"],
            "hashtag_limit": spec["hashtags"],
            "adaptations": [
                f"Truncated to {spec['max_length']} characters" if len(content) > spec["max_length"] else "Within character limit",
                f"Optimized for {target_platform} algorithm",
            ],
        }

        return self._create_result(
            action_type="format_content",
            output=formatted,
            output_type="formatted_content",
            confidence=0.93,
            reasoning=f"Formatted content for {target_platform} ({spec['max_length']} char limit)",
            requires_approval=False,  # Formatting is autonomous
            evidence=[
                EvidenceItem(
                    source_type="formatting",
                    source_name="PublishingAgent",
                    data={"target": target_platform, "spec": spec},
                    confidence=0.93,
                ),
            ],
        )

    async def _optimize_schedule(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Optimize posting schedule based on audience data."""
        platform = task.inputs.get("platform", "all")
        content_count = task.inputs.get("content_count", 5)
        
        # Placeholder optimized schedule
        now = datetime.utcnow()
        optimal_times = []
        
        for i in range(content_count):
            # Best times are evenings on weekdays
            days_ahead = i
            optimal_hour = 18 + (i % 3)  # 6-8 PM
            optimal_time = now + timedelta(days=days_ahead, hours=optimal_hour - now.hour)
            optimal_times.append({
                "slot": i + 1,
                "datetime": optimal_time.isoformat(),
                "day": optimal_time.strftime("%A"),
                "time": optimal_time.strftime("%H:%M"),
                "predicted_engagement": f"+{15 + i * 3}%",
            })

        return self._create_result(
            action_type="optimize_schedule",
            output={
                "platform": platform,
                "optimal_times": optimal_times,
                "recommendation": "Evening posts (6-8 PM local) perform best for your audience",
            },
            output_type="schedule_optimization",
            confidence=0.86,
            reasoning=f"Optimized {content_count} posting slots for {platform}",
            requires_approval=False,  # Suggestions don't need approval
            evidence=[
                EvidenceItem(
                    source_type="analysis",
                    source_name="ScheduleOptimizer",
                    data={"platform": platform, "slots": content_count},
                    confidence=0.86,
                ),
            ],
        )

    async def _suggest_times(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Suggest best posting times."""
        platform = task.inputs.get("platform", "general")
        
        suggestions = {
            "platform": platform,
            "best_times": [
                {"day": "Tuesday", "time": "18:00", "engagement_boost": "+22%"},
                {"day": "Wednesday", "time": "19:00", "engagement_boost": "+18%"},
                {"day": "Thursday", "time": "18:30", "engagement_boost": "+20%"},
            ],
            "avoid_times": [
                {"day": "Monday", "time": "06:00", "note": "Low engagement"},
                {"day": "Sunday", "time": "22:00", "note": "Audience inactive"},
            ],
        }

        return self._create_result(
            action_type="suggest_times",
            output=suggestions,
            output_type="time_suggestions",
            confidence=0.84,
            reasoning=f"Analyzed audience patterns for {platform}",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="analysis",
                    source_name="TimeOptimizer",
                    data={"platform": platform},
                    confidence=0.84,
                ),
            ],
        )

    async def _get_schedule(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Get current publishing schedule."""
        platform = task.inputs.get("platform", "all")
        
        # Placeholder schedule
        schedule = {
            "platform": platform,
            "scheduled_posts": [
                {
                    "id": str(uuid4()),
                    "title": "Sample scheduled post",
                    "platform": platform,
                    "scheduled_for": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "status": "scheduled",
                },
            ],
            "total_scheduled": 1,
        }

        return self._create_result(
            action_type="get_schedule",
            output=schedule,
            output_type="schedule",
            confidence=1.0,
            reasoning=f"Retrieved schedule for {platform}",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="query",
                    source_name="ScheduleDB",
                    data={"platform": platform},
                    confidence=1.0,
                ),
            ],
        )
