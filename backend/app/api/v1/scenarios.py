"""
Scenarios API Endpoints

REST API for scenario universe and what-if simulations.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.scenario import (
    ContentScenario,
    ScenarioFilter,
    ScenarioGenerateRequest,
    ScenarioType,
    ScenarioUniverse,
)
from app.schemas.blockers import (
    SimulateRequest,
    SimulationResult,
    SimulationScenario,
)
from app.services.scenario_builder import ScenarioBuilder
from app.services.simulator import Simulator

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# ============== Request/Response Schemas ==============

class ScenarioResponse(BaseModel):
    """Single scenario response."""
    scenario: ContentScenario


class UniverseResponse(BaseModel):
    """Scenario universe response."""
    universe: ScenarioUniverse
    generation_time_ms: int = 0


class SimulationResponse(BaseModel):
    """Simulation results response."""
    results: List[SimulationResult]
    comparison: Dict[str, Any] = Field(default_factory=dict)


# ============== Endpoints ==============

@router.post("/generate", response_model=UniverseResponse)
async def generate_scenarios(
    request: ScenarioGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate complete scenario universe for the creator.
    
    Analyzes connected platforms and identifies all opportunities.
    """
    import time
    start = time.time()

    builder = ScenarioBuilder(db)
    
    # Get user's connected platforms (placeholder)
    connected_platforms = ["instagram"]  # Would come from user profile
    
    universe = await builder.generate_scenarios(
        user_id=current_user.id,
        connected_platforms=connected_platforms,
        include_types=request.include_types,
        time_horizon_days=request.time_horizon_days,
    )

    generation_time = int((time.time() - start) * 1000)

    return UniverseResponse(
        universe=universe,
        generation_time_ms=generation_time,
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific scenario.
    """
    # In production, would fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Scenario not found",
    )


@router.post("/filter")
async def filter_scenarios(
    filter_options: ScenarioFilter,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Filter and sort scenarios from the universe.
    """
    builder = ScenarioBuilder(db)
    
    # Generate fresh universe for filtering
    connected_platforms = ["instagram"]
    
    universe = await builder.generate_scenarios(
        user_id=current_user.id,
        connected_platforms=connected_platforms,
    )

    filtered = await builder.filter_scenarios(universe, filter_options)

    return {
        "scenarios": [s.model_dump() for s in filtered],
        "total_count": len(filtered),
    }


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_scenarios(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run what-if simulations for given scenarios.
    
    Projects outcomes and compares against baseline.
    """
    simulator = Simulator(db)

    # Get baseline metrics (placeholder)
    baseline_metrics = {
        "followers": 10000,
        "engagement_rate": 3.5,
        "reach": 25000,
        "revenue": 500,
    }

    results = await simulator.compare_scenarios(
        user_id=current_user.id,
        scenarios=request.scenarios,
        baseline_metrics=baseline_metrics,
    )

    # Generate comparison summary
    comparison = {}
    if len(results) > 1:
        best = results[0]
        comparison = {
            "best_scenario": best.scenario.name,
            "best_confidence": best.overall_confidence,
            "scenarios_compared": len(results),
        }

    return SimulationResponse(
        results=results,
        comparison=comparison,
    )


@router.post("/impact")
async def calculate_action_impact(
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate estimated impact of a single action.
    """
    simulator = Simulator(db)

    baseline_metrics = {
        "followers": 10000,
        "engagement_rate": 3.5,
        "reach": 25000,
        "revenue": 500,
    }

    impact = await simulator.calculate_impact(
        action=action,
        baseline_metrics=baseline_metrics,
    )

    return impact


@router.get("/types")
async def get_scenario_types(
    current_user: User = Depends(get_current_user),
):
    """
    Get available scenario types.
    """
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in ScenarioType
        ]
    }
