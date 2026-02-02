"""
What-If Simulator

Projects outcomes from hypothetical actions.
All projections include confidence intervals.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.blockers import (
    SimulationResult,
    SimulationScenario,
)


class Simulator:
    """
    What-If simulator for projecting outcomes.
    
    Key principles:
    - All projections include confidence intervals
    - Clearly states assumptions made
    - Compares to baseline for context
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def project_outcome(
        self,
        user_id: UUID,
        scenario: SimulationScenario,
        baseline_metrics: Dict[str, Any],
    ) -> SimulationResult:
        """
        Project outcome for a single scenario.
        
        Args:
            user_id: The creator's ID
            scenario: The what-if scenario to simulate
            baseline_metrics: Current metrics to compare against
        """
        # Calculate projected metrics based on actions
        projected = await self._calculate_projections(
            actions=scenario.actions,
            baseline=baseline_metrics,
            assumptions=scenario.assumptions,
        )

        # Calculate confidence intervals
        confidence_low, confidence_high = self._calculate_intervals(projected)

        # Calculate improvements vs baseline
        improvements = self._calculate_improvements(
            baseline=baseline_metrics,
            projected=projected,
        )

        # Identify assumptions and warnings
        assumptions_made = self._identify_assumptions(scenario)
        warnings = self._generate_warnings(scenario, baseline_metrics)

        return SimulationResult(
            simulation_id=uuid4(),
            scenario=scenario,
            projected_metrics=projected,
            confidence_low=confidence_low,
            confidence_high=confidence_high,
            overall_confidence=self._calculate_overall_confidence(scenario),
            baseline_metrics=baseline_metrics,
            improvement_vs_baseline=improvements,
            warnings=warnings,
            assumptions_made=assumptions_made,
        )

    async def compare_scenarios(
        self,
        user_id: UUID,
        scenarios: List[SimulationScenario],
        baseline_metrics: Dict[str, Any],
    ) -> List[SimulationResult]:
        """
        Compare multiple scenarios side by side.
        
        Returns results sorted by expected impact.
        """
        results = []

        for scenario in scenarios:
            result = await self.project_outcome(
                user_id=user_id,
                scenario=scenario,
                baseline_metrics=baseline_metrics,
            )
            results.append(result)

        # Sort by improvement potential
        results.sort(
            key=lambda r: sum(r.improvement_vs_baseline.values()),
            reverse=True,
        )

        return results

    async def _calculate_projections(
        self,
        actions: List[str],
        baseline: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate projected metrics based on actions."""
        projected = baseline.copy()

        # Action impact multipliers (simplified model)
        action_impacts = {
            # Content actions
            "increase_posting_frequency": {
                "reach": 1.30,
                "followers": 1.15,
                "engagement": 1.10,
            },
            "add_video_content": {
                "reach": 1.40,
                "engagement": 1.35,
                "followers": 1.20,
            },
            "improve_hashtags": {
                "reach": 1.20,
                "discovery": 1.30,
            },
            # Engagement actions
            "respond_to_comments": {
                "engagement": 1.25,
                "retention": 1.15,
            },
            "community_engagement": {
                "engagement": 1.20,
                "follower_loyalty": 1.30,
            },
            # Monetization actions
            "add_affiliate_links": {
                "revenue": 1.50,
            },
            "launch_digital_product": {
                "revenue": 2.00,
            },
            "optimize_pricing": {
                "revenue_per_deal": 1.30,
            },
            # Growth actions
            "collaboration": {
                "followers": 1.25,
                "reach": 1.20,
            },
            "cross_platform_expansion": {
                "total_reach": 1.50,
                "followers": 1.30,
            },
        }

        # Apply action impacts
        for action in actions:
            action_key = action.lower().replace(" ", "_")
            impacts = action_impacts.get(action_key, {})
            
            for metric, multiplier in impacts.items():
                if metric in projected:
                    projected[metric] = projected[metric] * multiplier
                else:
                    # Estimate if not in baseline
                    projected[metric] = assumptions.get(metric, 100) * multiplier

        return projected

    def _calculate_intervals(
        self,
        projected: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Calculate confidence intervals (80% range)."""
        low = {}
        high = {}

        for key, value in projected.items():
            if isinstance(value, (int, float)):
                # 80% confidence interval
                low[key] = value * 0.7   # -30%
                high[key] = value * 1.4  # +40%

        return low, high

    def _calculate_improvements(
        self,
        baseline: Dict[str, Any],
        projected: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate percentage improvements vs baseline."""
        improvements = {}

        for key, proj_value in projected.items():
            if key in baseline and isinstance(proj_value, (int, float)):
                base_value = baseline[key]
                if base_value and base_value > 0:
                    pct_change = ((proj_value - base_value) / base_value) * 100
                    improvements[key] = round(pct_change, 1)

        return improvements

    def _calculate_overall_confidence(
        self,
        scenario: SimulationScenario,
    ) -> float:
        """Calculate overall confidence in projection."""
        # More actions = more uncertainty
        action_penalty = min(len(scenario.actions) * 0.05, 0.3)
        
        # More assumptions = more uncertainty
        assumption_penalty = min(len(scenario.assumptions) * 0.05, 0.2)
        
        base_confidence = 0.75
        return max(base_confidence - action_penalty - assumption_penalty, 0.3)

    def _identify_assumptions(
        self,
        scenario: SimulationScenario,
    ) -> List[str]:
        """Identify assumptions being made."""
        assumptions = []

        if scenario.actions:
            assumptions.append("Actions will be executed consistently")
            assumptions.append("Current market conditions remain stable")

        if len(scenario.actions) > 1:
            assumptions.append("No negative interactions between actions")

        assumptions.append("Historical patterns continue to predict future results")

        return assumptions

    def _generate_warnings(
        self,
        scenario: SimulationScenario,
        baseline: Dict[str, Any],
    ) -> List[str]:
        """Generate warnings about the projection."""
        warnings = []

        if len(scenario.actions) > 3:
            warnings.append(
                "Many simultaneous actions increase execution risk and decrease prediction accuracy"
            )

        if not baseline:
            warnings.append(
                "No baseline data available - projection based on assumptions only"
            )

        # Check for high-effort combinations
        high_effort_actions = [
            "launch_digital_product",
            "cross_platform_expansion",
            "add_video_content",
        ]
        high_effort_count = sum(
            1 for a in scenario.actions
            if a.lower().replace(" ", "_") in high_effort_actions
        )
        if high_effort_count >= 2:
            warnings.append(
                "Multiple high-effort actions may be difficult to execute simultaneously"
            )

        return warnings

    async def calculate_impact(
        self,
        action: str,
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate estimated impact of a single action."""
        scenario = SimulationScenario(
            name=f"Impact of {action}",
            description=f"Single action impact analysis",
            actions=[action],
        )
        
        result = await self.project_outcome(
            user_id=uuid4(),  # Dummy for single calculation
            scenario=scenario,
            baseline_metrics=baseline_metrics,
        )

        return {
            "action": action,
            "projected_impact": result.improvement_vs_baseline,
            "confidence": result.overall_confidence,
        }
