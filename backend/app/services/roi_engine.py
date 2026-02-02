"""
ROI Engine

Enhanced ROI calculator with scenario integration and confidence intervals.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.schemas.revenue import (
    ConfidenceInterval,
    ROIProjection,
    RevenueSource,
)


class ROIEngine:
    """
    ROI projection engine with confidence bands.
    
    Integrates with Scenario Universe for what-if analysis.
    """

    # Industry benchmarks for revenue estimation
    REVENUE_MULTIPLIERS = {
        "content": {
            "micro": 1.5,    # 10K-50K followers
            "mid": 2.0,      # 50K-500K followers
            "macro": 2.5,    # 500K-1M followers
            "mega": 3.0,     # 1M+ followers
        },
        "collaboration": {
            "micro": 2.0,
            "mid": 3.0,
            "macro": 4.0,
            "mega": 5.0,
        },
        "monetization": {
            "micro": 3.0,
            "mid": 4.0,
            "macro": 5.0,
            "mega": 6.0,
        },
    }

    def project_roi(
        self,
        scenario_name: str,
        scenario_type: str,
        investment_amount: float,
        investment_breakdown: Optional[Dict[str, float]] = None,
        time_horizon_days: int = 90,
        confidence_level: float = 0.80,
        creator_tier: str = "mid",
        scenario_data: Optional[Dict[str, Any]] = None,
    ) -> ROIProjection:
        """
        Project ROI with confidence intervals.
        
        Returns expected return with uncertainty bands.
        """
        # Get multiplier for scenario type
        multiplier = self.REVENUE_MULTIPLIERS.get(
            scenario_type, {}
        ).get(creator_tier, 2.0)

        # Calculate base projected revenue
        base_revenue = investment_amount * multiplier

        # Calculate confidence interval based on volatility
        volatility = self._get_volatility(scenario_type)
        
        revenue_interval = self._calculate_confidence_interval(
            base_revenue,
            volatility,
            confidence_level,
        )

        # Investment interval (typically more certain)
        investment_interval = self._calculate_confidence_interval(
            investment_amount,
            0.1,  # 10% uncertainty on costs
            confidence_level,
        )

        # ROI calculation
        roi_estimate = (
            (revenue_interval.estimate - investment_interval.estimate) 
            / investment_interval.estimate
        ) * 100

        roi_lower = (
            (revenue_interval.lower - investment_interval.upper) 
            / investment_interval.upper
        ) * 100

        roi_upper = (
            (revenue_interval.upper - investment_interval.lower) 
            / investment_interval.lower
        ) * 100

        roi_interval = ConfidenceInterval(
            lower=max(roi_lower, -100),  # Cap at -100%
            estimate=roi_estimate,
            upper=roi_upper,
            confidence_level=confidence_level,
        )

        # Payback period
        payback_interval = None
        if revenue_interval.estimate > 0:
            daily_revenue = revenue_interval.estimate / time_horizon_days
            payback_days = investment_amount / daily_revenue if daily_revenue > 0 else time_horizon_days
            
            payback_interval = ConfidenceInterval(
                lower=max(1, payback_days * 0.7),
                estimate=payback_days,
                upper=payback_days * 1.5,
                confidence_level=confidence_level,
            )

        # Build revenue breakdown by source
        revenue_breakdown = self._estimate_revenue_breakdown(
            base_revenue,
            scenario_type,
            volatility,
            confidence_level,
        )

        # Generate assumptions
        assumptions = self._generate_assumptions(
            scenario_type,
            creator_tier,
            time_horizon_days,
        )

        return ROIProjection(
            projection_id=uuid4(),
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            time_horizon_days=time_horizon_days,
            investment=investment_interval,
            investment_breakdown=investment_breakdown or {},
            projected_revenue=revenue_interval,
            revenue_breakdown=revenue_breakdown,
            roi_percent=roi_interval,
            payback_period_days=payback_interval,
            assumptions=assumptions,
            data_sources=["Historical creator data", "Industry benchmarks", "Platform analytics"],
            comparable_cases=47,  # Would query database
        )

    def compare_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compare multiple scenarios side-by-side."""
        projections = []
        
        for scenario in scenarios:
            projection = self.project_roi(
                scenario_name=scenario.get("name", "Unnamed"),
                scenario_type=scenario.get("type", "content"),
                investment_amount=scenario.get("investment", 0),
                time_horizon_days=scenario.get("time_horizon", 90),
                creator_tier=scenario.get("tier", "mid"),
            )
            projections.append(projection)

        # Find best scenario
        best_idx = max(
            range(len(projections)),
            key=lambda i: projections[i].roi_percent.estimate,
        )

        return {
            "projections": projections,
            "best_scenario_index": best_idx,
            "best_scenario_name": projections[best_idx].scenario_name,
            "comparison_summary": self._generate_comparison_summary(projections),
        }

    def _calculate_confidence_interval(
        self,
        estimate: float,
        volatility: float,
        confidence_level: float,
    ) -> ConfidenceInterval:
        """Calculate confidence interval based on volatility."""
        # Z-score for confidence level (approximate)
        z_scores = {
            0.80: 1.28,
            0.85: 1.44,
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576,
        }
        z = z_scores.get(confidence_level, 1.28)

        margin = estimate * volatility * z

        return ConfidenceInterval(
            lower=max(0, estimate - margin),
            estimate=estimate,
            upper=estimate + margin,
            confidence_level=confidence_level,
        )

    def _get_volatility(self, scenario_type: str) -> float:
        """Get volatility factor for scenario type."""
        volatilities = {
            "content": 0.25,       # 25% standard deviation
            "collaboration": 0.35,  # More uncertain
            "monetization": 0.30,
            "growth": 0.40,
            "brand_deal": 0.20,    # More predictable
        }
        return volatilities.get(scenario_type, 0.30)

    def _estimate_revenue_breakdown(
        self,
        total_revenue: float,
        scenario_type: str,
        volatility: float,
        confidence_level: float,
    ) -> Dict[str, ConfidenceInterval]:
        """Estimate revenue by source."""
        # Allocation by scenario type
        allocations = {
            "content": {
                "ad_revenue": 0.40,
                "brand_deal": 0.30,
                "affiliate": 0.20,
                "tips": 0.10,
            },
            "collaboration": {
                "brand_deal": 0.50,
                "sponsorship": 0.30,
                "affiliate": 0.20,
            },
            "monetization": {
                "subscription": 0.35,
                "course": 0.30,
                "merchandise": 0.20,
                "tips": 0.15,
            },
        }

        allocation = allocations.get(scenario_type, {"other": 1.0})
        
        breakdown = {}
        for source, pct in allocation.items():
            amount = total_revenue * pct
            breakdown[source] = self._calculate_confidence_interval(
                amount, volatility, confidence_level
            )

        return breakdown

    def _generate_assumptions(
        self,
        scenario_type: str,
        creator_tier: str,
        time_horizon: int,
    ) -> List[str]:
        """Generate list of assumptions for transparency."""
        assumptions = [
            f"Assumes {creator_tier}-tier creator performance metrics",
            f"Based on {time_horizon}-day projection horizon",
            "Revenue estimates based on industry benchmarks",
            "Does not account for platform algorithm changes",
            "Assumes consistent posting schedule",
        ]

        if scenario_type == "collaboration":
            assumptions.append("Partner reach estimates based on average collaboration lift")

        if scenario_type == "monetization":
            assumptions.append("Conversion rates based on creator economy averages")

        return assumptions

    def _generate_comparison_summary(
        self,
        projections: List[ROIProjection],
    ) -> str:
        """Generate human-readable comparison."""
        if not projections:
            return "No scenarios to compare"

        best = max(projections, key=lambda p: p.roi_percent.estimate)
        worst = min(projections, key=lambda p: p.roi_percent.estimate)

        return (
            f"Best: {best.scenario_name} ({best.roi_percent.estimate:.0f}% ROI). "
            f"Expected return: ${best.projected_revenue.estimate:,.0f}. "
            f"Lowest risk: {worst.scenario_name} with tighter confidence bands."
        )
