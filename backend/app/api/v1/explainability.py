"""
Explainability & Audit API Endpoints

REST API for multi-view rendering and audit snapshots.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.explainability import (
    Insight,
    InsightType,
    MultiViewRenderRequest,
    MultiViewRenderResponse,
    RenderedInsight,
    RenderRequest,
    RenderResponse,
    ViewType,
)
from app.schemas.audit import (
    AuditSnapshot,
    CreateSnapshotRequest,
    DeltaRequest,
    DeltaResponse,
    SnapshotListResponse,
    SnapshotResponse,
    SnapshotType,
)
from app.services.explainability_engine import ExplainabilityEngine, VIEW_TEMPLATES
from app.services.snapshot_service import SnapshotService
from app.services.delta_service import DeltaService
from app.services.version_registry import VersionRegistry

router = APIRouter(tags=["explainability"])


# ============== Explainability Endpoints ==============

@router.post("/explainability/render", response_model=RenderResponse)
async def render_insight(
    request: RenderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Render an insight for a specific view type.
    
    Same data, different presentations:
    - creator: Plain language, actionable
    - manager: Talk tracks, client-ready
    - technical: Evidence chains, statistics
    - audit: Immutable logs, full provenance
    """
    engine = ExplainabilityEngine()
    rendered = engine.render_insight(request.insight, request.view_type)

    return RenderResponse(
        rendered=rendered,
        original_insight_id=request.insight.insight_id,
    )


@router.post("/explainability/render-all", response_model=MultiViewRenderResponse)
async def render_all_views(
    request: MultiViewRenderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Render an insight in all view types at once.
    """
    engine = ExplainabilityEngine()
    renderings = engine.render_all_views(request.insight)

    return MultiViewRenderResponse(
        renderings=renderings,
        insight_id=request.insight.insight_id,
    )


@router.get("/explainability/views")
async def get_available_views(
    current_user: User = Depends(get_current_user),
):
    """
    Get available view types and their descriptions.
    """
    return {
        "views": [
            {
                "type": view.value,
                "name": template.name,
                "description": template.description,
                "tone": template.tone,
            }
            for view, template in VIEW_TEMPLATES.items()
        ]
    }


# ============== Audit Snapshot Endpoints ==============

@router.post("/audit/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an immutable audit snapshot.
    
    Captures the exact state at time of creation.
    Cannot be modified after creation.
    """
    service = SnapshotService(db)
    
    snapshot = await service.create_snapshot(
        user_id=current_user.id,
        snapshot_type=request.snapshot_type,
        analysis_type=request.analysis_type,
        description=request.description,
        recommendations=[request.data] if request.data else [],
    )
    
    await db.commit()

    return SnapshotResponse(snapshot=snapshot)


@router.get("/audit/snapshots", response_model=SnapshotListResponse)
async def list_snapshots(
    snapshot_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List audit snapshots for the current user.
    """
    service = SnapshotService(db)
    
    type_filter = SnapshotType(snapshot_type) if snapshot_type else None
    
    snapshots = await service.get_snapshots_for_user(
        user_id=current_user.id,
        snapshot_type=type_filter,
        limit=limit,
        offset=offset,
    )

    return SnapshotListResponse(
        snapshots=snapshots,
        total_count=len(snapshots),
    )


@router.get("/audit/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific audit snapshot.
    
    Verifies integrity via content hash.
    """
    service = SnapshotService(db)
    snapshot = await service.get_snapshot(snapshot_id)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found",
        )

    # Verify ownership
    if snapshot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return SnapshotResponse(snapshot=snapshot)


# ============== Delta Report Endpoints ==============

@router.post("/audit/delta", response_model=DeltaResponse)
async def generate_delta_report(
    request: DeltaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a delta report comparing two snapshots.
    
    Shows what changed and the impact on recommendations.
    """
    service = DeltaService(db)
    
    try:
        report = await service.generate_delta(
            snapshot_id_before=request.snapshot_id_before,
            snapshot_id_after=request.snapshot_id_after,
        )
        await db.commit()
        return DeltaResponse(report=report)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/audit/delta/{before_id}/{after_id}", response_model=DeltaResponse)
async def get_delta_report(
    before_id: UUID,
    after_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get or generate a delta report between two snapshots.
    """
    service = DeltaService(db)
    
    try:
        report = await service.generate_delta(
            snapshot_id_before=before_id,
            snapshot_id_after=after_id,
        )
        await db.commit()
        return DeltaResponse(report=report)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============== Version Registry Endpoints ==============

@router.get("/audit/versions")
async def get_active_versions(
    version_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get currently active model/rule versions.
    """
    registry = VersionRegistry(db)
    registry.load_defaults()
    
    if version_type:
        versions = await registry.get_active_versions(version_type)
    else:
        versions = await registry.get_all_active()

    return {"versions": versions}


@router.get("/audit/versions/{name}/history")
async def get_version_history(
    name: str,
    version_type: str = "model",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get version history for a component.
    """
    registry = VersionRegistry(db)
    history = await registry.get_version_history(name, version_type)

    return {
        "name": name,
        "type": version_type,
        "history": [h.model_dump() for h in history],
    }


@router.get("/audit/versions/{name}/rollback-check")
async def check_rollback(
    name: str,
    version_type: str = "model",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check rollback capability for a component.
    """
    registry = VersionRegistry(db)
    result = await registry.rollback_check(name, version_type)

    return result
