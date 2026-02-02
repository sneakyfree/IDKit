"""
Revenue Agent

Handles ROI tracking, deal analysis, and pricing recommendations.
MEDIUM autonomy - financial actions require approval.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

from app.agents.base import (
    AgentContext,
    AgentResult,
    AgentTask,
    AgentType,
    AutonomyLevel,
    BaseAgent,
    EvidenceItem,
)


class RevenueAgent(BaseAgent):
    """
    Revenue agent with MEDIUM autonomy.
    
    Analysis is autonomous, but payment/contract actions require approval.
    
    Capabilities:
    - Calculate ROI projections
    - Analyze deal terms
    - Recommend pricing
    - Track revenue streams
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.REVENUE,
            autonomy_level=AutonomyLevel.MEDIUM,
        )

    @property
    def name(self) -> str:
        return "Revenue Agent"

    @property
    def description(self) -> str:
        return "ROI tracking, deal analysis, and pricing recommendations"

    @property
    def capabilities(self) -> List[str]:
        return [
            "calculate_roi",
            "analyze_deal",
            "recommend_pricing",
            "track_revenue",
            "forecast_earnings",
            "compare_rates",
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        """Check if this is a revenue-related task."""
        revenue_tasks = {
            "calculate_roi",
            "analyze_deal",
            "recommend_pricing",
            "track_revenue",
            "forecast_earnings",
            "compare_rates",
            "revenue",
        }
        return task.task_type.lower() in revenue_tasks

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Execute revenue analysis task."""
        task_type = task.task_type.lower()

        if task_type == "calculate_roi":
            return await self._calculate_roi(task, context)
        elif task_type == "analyze_deal":
            return await self._analyze_deal(task, context)
        elif task_type == "recommend_pricing":
            return await self._recommend_pricing(task, context)
        elif task_type == "forecast_earnings":
            return await self._forecast_earnings(task, context)
        else:
            return self._create_error_result(
                action_type=task_type,
                error=f"Unknown revenue task type: {task_type}",
            )

    async def _calculate_roi(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Calculate ROI for a campaign or content."""
        investment = task.inputs.get("investment", 0)
        revenue = task.inputs.get("revenue", 0)
        timeframe = task.inputs.get("timeframe", "30d")

        if investment <= 0:
            return self._create_error_result(
                action_type="calculate_roi",
                error="Investment amount must be positive",
            )

        roi = ((revenue - investment) / investment) * 100 if investment > 0 else 0

        return self._create_result(
            action_type="calculate_roi",
            output={
                "investment": investment,
                "revenue": revenue,
                "roi_percent": round(roi, 2),
                "net_profit": revenue - investment,
                "timeframe": timeframe,
                "confidence_interval": {
                    "low": round(roi * 0.8, 2),
                    "high": round(roi * 1.2, 2),
                },
            },
            output_type="roi_calculation",
            confidence=0.90,
            reasoning=f"Calculated ROI of {roi:.1f}% over {timeframe}",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="calculation",
                    source_name="RevenueAgent",
                    data={"investment": investment, "revenue": revenue},
                    confidence=0.90,
                ),
            ],
        )

    async def _analyze_deal(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Analyze a brand deal opportunity."""
        deal_value = task.inputs.get("deal_value", 0)
        deliverables = task.inputs.get("deliverables", [])
        usage_rights = task.inputs.get("usage_rights", "limited")
        exclusivity = task.inputs.get("exclusivity", False)

        # Calculate deal score
        score = 70  # Base score
        if deal_value > 5000:
            score += 10
        if usage_rights == "limited":
            score += 10
        if not exclusivity:
            score += 5
        score = min(score, 100)

        analysis = {
            "deal_value": deal_value,
            "deliverables": deliverables,
            "score": score,
            "recommendation": "accept" if score >= 75 else "negotiate" if score >= 60 else "decline",
            "concerns": [],
            "opportunities": [],
        }

        if exclusivity:
            analysis["concerns"].append("Exclusivity clause limits future opportunities")
        if usage_rights == "perpetual":
            analysis["concerns"].append("Perpetual usage rights undervalues long-term IP")
        if deal_value > 1000:
            analysis["opportunities"].append("Good base value for deliverable count")

        return self._create_result(
            action_type="analyze_deal",
            output=analysis,
            output_type="deal_analysis",
            confidence=0.82,
            reasoning=f"Deal scored {score}/100 - {analysis['recommendation'].upper()}",
            requires_approval=True,
            approval_reason="Deal decisions require human judgment",
            evidence=[
                EvidenceItem(
                    source_type="analysis",
                    source_name="RevenueAgent",
                    data={"deal_value": deal_value, "score": score},
                    confidence=0.82,
                ),
            ],
        )

    async def _recommend_pricing(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Recommend pricing for sponsored content."""
        platform = task.inputs.get("platform", "instagram")
        content_type = task.inputs.get("content_type", "post")
        follower_count = task.inputs.get("follower_count", 10000)
        engagement_rate = task.inputs.get("engagement_rate", 3.0)

        # Calculate base rate using industry benchmarks
        base_cpm = {
            "instagram": 10,
            "tiktok": 8,
            "youtube": 15,
            "twitter": 5,
        }.get(platform.lower(), 8)

        # Estimated impressions (20% of followers for posts)
        impressions = follower_count * 0.2
        base_rate = (impressions / 1000) * base_cpm

        # Adjust for engagement rate (above 3% gets premium)
        engagement_multiplier = 1 + max(0, (engagement_rate - 3) * 0.1)
        recommended_rate = base_rate * engagement_multiplier

        return self._create_result(
            action_type="recommend_pricing",
            output={
                "platform": platform,
                "content_type": content_type,
                "recommended_rate": round(recommended_rate, 2),
                "rate_range": {
                    "low": round(recommended_rate * 0.8, 2),
                    "high": round(recommended_rate * 1.3, 2),
                },
                "benchmarks": {
                    "industry_cpm": base_cpm,
                    "your_engagement": engagement_rate,
                    "avg_engagement": 3.0,
                },
            },
            output_type="pricing_recommendation",
            confidence=0.78,
            reasoning=f"Recommended ${recommended_rate:.0f} based on {follower_count} followers, {engagement_rate}% engagement",
            requires_approval=True,
            approval_reason="Pricing decisions require human confirmation before sharing",
            evidence=[
                EvidenceItem(
                    source_type="benchmark",
                    source_name="RevenueAgent",
                    data={"platform": platform, "base_cpm": base_cpm},
                    confidence=0.78,
                ),
            ],
        )

    async def _forecast_earnings(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Forecast future earnings based on current trends."""
        current_monthly = task.inputs.get("current_monthly", 0)
        growth_rate = task.inputs.get("growth_rate", 5)
        months = task.inputs.get("months", 12)

        projections = []
        monthly = current_monthly
        for i in range(months):
            monthly = monthly * (1 + growth_rate / 100)
            projections.append({
                "month": i + 1,
                "projected": round(monthly, 2),
                "confidence": max(0.5, 0.95 - (i * 0.03)),
            })

        total_projected = sum(p["projected"] for p in projections)

        return self._create_result(
            action_type="forecast_earnings",
            output={
                "current_monthly": current_monthly,
                "growth_rate_percent": growth_rate,
                "projections": projections,
                "total_projected": round(total_projected, 2),
                "confidence_band": {
                    "low": round(total_projected * 0.7, 2),
                    "high": round(total_projected * 1.3, 2),
                },
            },
            output_type="earnings_forecast",
            confidence=0.70,
            reasoning=f"Projected ${total_projected:.0f} over {months} months at {growth_rate}% growth",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="projection",
                    source_name="RevenueAgent",
                    data={"growth_rate": growth_rate, "months": months},
                    confidence=0.70,
                ),
            ],
        )
