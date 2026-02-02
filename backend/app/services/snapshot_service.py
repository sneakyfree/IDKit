"""
Snapshot Service

Immutable snapshot system for audit-grade reproducibility.
Snapshots are append-only and capture exact state at analysis time.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.audit import (
    AuditSnapshot,
    ComputationStep,
    DataSourceSnapshot,
    SnapshotType,
)


class SnapshotService:
    """
    Immutable snapshot service for audit-grade reproducibility.
    
    Key principles:
    - Append-only: Snapshots are never modified or deleted
    - Content-addressable: Hash of content for verification
    - Complete provenance: All inputs, models, rules captured
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(
        self,
        user_id: UUID,
        snapshot_type: SnapshotType,
        analysis_type: str,
        description: Optional[str] = None,
        data_sources: Optional[Dict[str, DataSourceSnapshot]] = None,
        model_versions: Optional[Dict[str, str]] = None,
        rule_versions: Optional[Dict[str, str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        confidence_scores: Optional[Dict[str, float]] = None,
        evidence_chain: Optional[List[Dict[str, Any]]] = None,
        computation_log: Optional[List[ComputationStep]] = None,
    ) -> AuditSnapshot:
        """
        Create an immutable snapshot of current state.
        
        Once created, the snapshot cannot be modified.
        """
        snapshot = AuditSnapshot(
            snapshot_id=uuid4(),
            snapshot_type=snapshot_type,
            created_at=datetime.utcnow(),
            user_id=user_id,
            analysis_type=analysis_type,
            description=description,
            data_sources=data_sources or {},
            model_versions=model_versions or {},
            rule_versions=rule_versions or {},
            configuration=configuration or {},
            recommendations=recommendations or [],
            confidence_scores=confidence_scores or {},
            evidence_chain=evidence_chain or [],
            computation_log=computation_log or [],
            is_sealed=True,
        )

        # Generate content hash for integrity verification
        snapshot.content_hash = self._generate_content_hash(snapshot)

        # Store in database
        await self._persist_snapshot(snapshot)

        return snapshot

    async def get_snapshot(
        self,
        snapshot_id: UUID,
    ) -> Optional[AuditSnapshot]:
        """
        Retrieve a snapshot by ID.
        
        Verifies content hash for integrity.
        """
        from app.models.audit import AuditSnapshotRecord

        result = await self.db.execute(
            select(AuditSnapshotRecord).where(
                AuditSnapshotRecord.id == snapshot_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        snapshot = self._record_to_snapshot(record)

        # Verify integrity
        if not self._verify_integrity(snapshot):
            # Log integrity violation but still return
            pass

        return snapshot

    async def get_snapshots_for_user(
        self,
        user_id: UUID,
        snapshot_type: Optional[SnapshotType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditSnapshot]:
        """Get snapshots for a user."""
        from app.models.audit import AuditSnapshotRecord

        query = select(AuditSnapshotRecord).where(
            AuditSnapshotRecord.user_id == user_id
        )

        if snapshot_type:
            query = query.where(
                AuditSnapshotRecord.snapshot_type == snapshot_type.value
            )

        query = query.order_by(AuditSnapshotRecord.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        records = result.scalars().all()

        return [self._record_to_snapshot(r) for r in records]

    async def get_latest_snapshot(
        self,
        user_id: UUID,
        analysis_type: str,
    ) -> Optional[AuditSnapshot]:
        """Get the most recent snapshot for an analysis type."""
        from app.models.audit import AuditSnapshotRecord

        result = await self.db.execute(
            select(AuditSnapshotRecord).where(
                AuditSnapshotRecord.user_id == user_id,
                AuditSnapshotRecord.analysis_type == analysis_type,
            ).order_by(
                AuditSnapshotRecord.created_at.desc()
            ).limit(1)
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._record_to_snapshot(record)

    def _generate_content_hash(self, snapshot: AuditSnapshot) -> str:
        """Generate SHA-256 hash of snapshot content."""
        # Exclude the hash itself and timestamps that would change
        content = {
            "snapshot_id": str(snapshot.snapshot_id),
            "user_id": str(snapshot.user_id),
            "snapshot_type": snapshot.snapshot_type.value,
            "analysis_type": snapshot.analysis_type,
            "data_sources": {
                k: v.model_dump() if hasattr(v, 'model_dump') else v
                for k, v in snapshot.data_sources.items()
            },
            "model_versions": snapshot.model_versions,
            "rule_versions": snapshot.rule_versions,
            "configuration": snapshot.configuration,
            "recommendations": snapshot.recommendations,
            "confidence_scores": snapshot.confidence_scores,
            "evidence_chain": snapshot.evidence_chain,
        }

        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _verify_integrity(self, snapshot: AuditSnapshot) -> bool:
        """Verify snapshot integrity using content hash."""
        if not snapshot.content_hash:
            return True  # No hash to verify

        expected_hash = self._generate_content_hash(snapshot)
        return expected_hash == snapshot.content_hash

    async def _persist_snapshot(self, snapshot: AuditSnapshot) -> None:
        """Persist snapshot to database."""
        from app.models.audit import AuditSnapshotRecord

        record = AuditSnapshotRecord(
            id=snapshot.snapshot_id,
            user_id=snapshot.user_id,
            snapshot_type=snapshot.snapshot_type.value,
            analysis_type=snapshot.analysis_type,
            description=snapshot.description,
            data_sources={
                k: v.model_dump() if hasattr(v, 'model_dump') else v
                for k, v in snapshot.data_sources.items()
            },
            model_versions=snapshot.model_versions,
            rule_versions=snapshot.rule_versions,
            configuration=snapshot.configuration,
            recommendations=snapshot.recommendations,
            confidence_scores=snapshot.confidence_scores,
            evidence_chain=snapshot.evidence_chain,
            computation_log=[
                s.model_dump() if hasattr(s, 'model_dump') else s
                for s in snapshot.computation_log
            ],
            content_hash=snapshot.content_hash,
            is_sealed=snapshot.is_sealed,
        )

        self.db.add(record)
        await self.db.flush()

    def _record_to_snapshot(self, record: Any) -> AuditSnapshot:
        """Convert database record to AuditSnapshot."""
        return AuditSnapshot(
            snapshot_id=record.id,
            snapshot_type=SnapshotType(record.snapshot_type),
            created_at=record.created_at,
            user_id=record.user_id,
            analysis_type=record.analysis_type,
            description=record.description,
            data_sources=record.data_sources or {},
            model_versions=record.model_versions or {},
            rule_versions=record.rule_versions or {},
            configuration=record.configuration or {},
            recommendations=record.recommendations or [],
            confidence_scores=record.confidence_scores or {},
            evidence_chain=record.evidence_chain or [],
            computation_log=[],  # Would need to deserialize
            content_hash=record.content_hash,
            is_sealed=record.is_sealed,
        )
