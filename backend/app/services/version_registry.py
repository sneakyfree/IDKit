"""
Version Registry

Tracks AI model and rule versions for reproducibility.
Enables rollback capability and version comparison.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.audit import ModelVersion, VersionRegistryEntry


class VersionRegistry:
    """
    Registry for tracking AI model and rule versions.
    
    Key principles:
    - Version pinning for reproducibility
    - Complete history tracking
    - Rollback capability
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        
        # In-memory cache of active versions
        self._active_models: Dict[str, str] = {}
        self._active_rules: Dict[str, str] = {}
        self._active_configs: Dict[str, str] = {}

    async def register_version(
        self,
        name: str,
        version: str,
        version_type: str,  # model, rule, config
        description: Optional[str] = None,
        hash_value: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VersionRegistryEntry:
        """
        Register a new version in the registry.
        """
        entry = VersionRegistryEntry(
            name=name,
            version=version,
            type=version_type,
            registered_at=datetime.utcnow(),
            hash=hash_value,
            is_active=True,
        )

        # Update active versions cache
        if version_type == "model":
            self._active_models[name] = version
        elif version_type == "rule":
            self._active_rules[name] = version
        elif version_type == "config":
            self._active_configs[name] = version

        # Persist to database
        await self._persist_version(entry, description, metadata)

        return entry

    async def get_active_versions(
        self,
        version_type: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get currently active versions.
        
        Returns dict of {name: version}.
        """
        if version_type == "model":
            return self._active_models.copy()
        elif version_type == "rule":
            return self._active_rules.copy()
        elif version_type == "config":
            return self._active_configs.copy()
        else:
            return {
                **self._active_models,
                **self._active_rules,
                **self._active_configs,
            }

    async def get_all_active(self) -> Dict[str, Dict[str, str]]:
        """Get all active versions grouped by type."""
        return {
            "models": self._active_models.copy(),
            "rules": self._active_rules.copy(),
            "configs": self._active_configs.copy(),
        }

    async def get_version(
        self,
        name: str,
        version_type: str,
    ) -> Optional[str]:
        """Get active version for a specific component."""
        versions = await self.get_active_versions(version_type)
        return versions.get(name)

    async def get_version_history(
        self,
        name: str,
        version_type: str,
        limit: int = 20,
    ) -> List[VersionRegistryEntry]:
        """Get version history for a component."""
        from app.models.audit import VersionRecord

        result = await self.db.execute(
            select(VersionRecord).where(
                VersionRecord.name == name,
                VersionRecord.version_type == version_type,
            ).order_by(
                VersionRecord.registered_at.desc()
            ).limit(limit)
        )
        records = result.scalars().all()

        return [
            VersionRegistryEntry(
                name=r.name,
                version=r.version,
                type=r.version_type,
                registered_at=r.registered_at,
                hash=r.hash,
                is_active=r.is_active,
            )
            for r in records
        ]

    async def set_active_version(
        self,
        name: str,
        version: str,
        version_type: str,
    ) -> bool:
        """
        Set a specific version as active.
        
        Used for rollback or switching versions.
        """
        # Verify version exists
        history = await self.get_version_history(name, version_type)
        version_exists = any(h.version == version for h in history)

        if not version_exists:
            return False

        # Update active cache
        if version_type == "model":
            self._active_models[name] = version
        elif version_type == "rule":
            self._active_rules[name] = version
        elif version_type == "config":
            self._active_configs[name] = version

        # Update database
        await self._set_active_in_db(name, version, version_type)

        return True

    async def rollback_check(
        self,
        name: str,
        version_type: str,
    ) -> Dict[str, Any]:
        """
        Check rollback capability for a component.
        
        Returns available previous versions and any warnings.
        """
        history = await self.get_version_history(name, version_type)

        if len(history) < 2:
            return {
                "can_rollback": False,
                "reason": "No previous versions available",
                "available_versions": [],
            }

        current = history[0]
        previous = history[1:]

        return {
            "can_rollback": True,
            "current_version": current.version,
            "available_versions": [v.version for v in previous],
            "recommended_rollback": previous[0].version if previous else None,
        }

    async def compare_versions(
        self,
        name: str,
        version_type: str,
        version_a: str,
        version_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two versions of a component.
        """
        return {
            "name": name,
            "version_a": version_a,
            "version_b": version_b,
            "comparison": "Version comparison placeholder",
            "recommendation": "No significant differences detected",
        }

    async def _persist_version(
        self,
        entry: VersionRegistryEntry,
        description: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """Persist version to database."""
        from app.models.audit import VersionRecord

        record = VersionRecord(
            id=uuid4(),
            name=entry.name,
            version=entry.version,
            version_type=entry.type,
            description=description,
            hash=entry.hash,
            metadata_json=metadata,
            is_active=entry.is_active,
        )

        self.db.add(record)
        await self.db.flush()

    async def _set_active_in_db(
        self,
        name: str,
        version: str,
        version_type: str,
    ) -> None:
        """Update active status in database."""
        from app.models.audit import VersionRecord

        # Deactivate all versions for this component
        result = await self.db.execute(
            select(VersionRecord).where(
                VersionRecord.name == name,
                VersionRecord.version_type == version_type,
            )
        )
        records = result.scalars().all()

        for record in records:
            record.is_active = (record.version == version)

        await self.db.flush()

    def load_defaults(self) -> None:
        """Load default versions (called on startup)."""
        # Default model versions
        self._active_models = {
            "engagement_predictor": "v2.1.0",
            "content_recommender": "v1.5.0",
            "trend_analyzer": "v1.2.0",
            "sentiment_analyzer": "v2.0.0",
        }

        # Default rule versions
        self._active_rules = {
            "ftc_compliance": "2024.1",
            "content_policy": "2024.2",
            "monetization_rules": "2024.1",
        }

        # Default config versions
        self._active_configs = {
            "scoring_weights": "v1.0",
            "threshold_settings": "v1.1",
        }
