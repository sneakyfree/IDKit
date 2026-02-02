"""
Delta Service

Generates delta reports comparing two snapshots.
Shows what changed and the impact on recommendations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.audit import (
    AuditSnapshot,
    DeltaChange,
    DeltaReport,
)
from app.services.snapshot_service import SnapshotService


class DeltaService:
    """
    Service for generating delta reports between snapshots.
    
    Key principles:
    - Track all changes between states
    - Quantify impact on recommendations
    - Triggered automatically on version changes
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.snapshot_service = SnapshotService(db)

    async def generate_delta(
        self,
        snapshot_id_before: UUID,
        snapshot_id_after: UUID,
    ) -> DeltaReport:
        """
        Generate a delta report comparing two snapshots.
        """
        # Fetch both snapshots
        before = await self.snapshot_service.get_snapshot(snapshot_id_before)
        after = await self.snapshot_service.get_snapshot(snapshot_id_after)

        if not before or not after:
            raise ValueError("One or both snapshots not found")

        # Detect changes
        changes = self._detect_changes(before, after)

        # Analyze model/rule changes
        model_changes = self._compare_versions(
            before.model_versions,
            after.model_versions,
        )
        rule_changes = self._compare_versions(
            before.rule_versions,
            after.rule_versions,
        )

        # Count recommendation changes
        rec_added, rec_removed, rec_modified = self._count_recommendation_changes(
            before.recommendations,
            after.recommendations,
        )

        # Calculate time delta
        time_delta = self._format_time_delta(before.created_at, after.created_at)

        # Generate summary
        summary = self._generate_summary(
            changes, model_changes, rule_changes,
            rec_added, rec_removed, rec_modified,
        )

        report = DeltaReport(
            report_id=uuid4(),
            snapshot_before_id=snapshot_id_before,
            snapshot_after_id=snapshot_id_after,
            time_delta=time_delta,
            changes=changes,
            total_changes=len(changes),
            high_impact_changes=sum(1 for c in changes if c.impact_level == "high"),
            model_changes=model_changes,
            rule_changes=rule_changes,
            recommendations_added=rec_added,
            recommendations_removed=rec_removed,
            recommendations_modified=rec_modified,
            summary=summary,
        )

        # Persist the report
        await self._persist_report(report)

        return report

    def _detect_changes(
        self,
        before: AuditSnapshot,
        after: AuditSnapshot,
    ) -> List[DeltaChange]:
        """Detect all changes between two snapshots."""
        changes = []

        # Compare configuration
        config_changes = self._compare_dicts(
            before.configuration or {},
            after.configuration or {},
            "configuration",
        )
        changes.extend(config_changes)

        # Compare confidence scores
        score_changes = self._compare_dicts(
            before.confidence_scores or {},
            after.confidence_scores or {},
            "confidence_scores",
        )
        changes.extend(score_changes)

        # Compare data sources
        for key in set(before.data_sources.keys()) | set(after.data_sources.keys()):
            if key not in before.data_sources:
                changes.append(DeltaChange(
                    field_path=f"data_sources.{key}",
                    change_type="added",
                    old_value=None,
                    new_value="(new source)",
                    impact_level="medium",
                ))
            elif key not in after.data_sources:
                changes.append(DeltaChange(
                    field_path=f"data_sources.{key}",
                    change_type="removed",
                    old_value="(removed source)",
                    new_value=None,
                    impact_level="high",
                ))

        return changes

    def _compare_dicts(
        self,
        before: Dict,
        after: Dict,
        prefix: str,
    ) -> List[DeltaChange]:
        """Compare two dictionaries and return changes."""
        changes = []
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            path = f"{prefix}.{key}"
            old_val = before.get(key)
            new_val = after.get(key)

            if old_val is None and new_val is not None:
                changes.append(DeltaChange(
                    field_path=path,
                    change_type="added",
                    old_value=None,
                    new_value=new_val,
                    impact_level="medium",
                ))
            elif old_val is not None and new_val is None:
                changes.append(DeltaChange(
                    field_path=path,
                    change_type="removed",
                    old_value=old_val,
                    new_value=None,
                    impact_level="medium",
                ))
            elif old_val != new_val:
                # Determine impact level based on change magnitude
                impact = self._assess_change_impact(old_val, new_val)
                changes.append(DeltaChange(
                    field_path=path,
                    change_type="modified",
                    old_value=old_val,
                    new_value=new_val,
                    impact_level=impact,
                ))

        return changes

    def _compare_versions(
        self,
        before: Dict[str, str],
        after: Dict[str, str],
    ) -> Dict[str, Dict[str, str]]:
        """Compare version dictionaries."""
        changes = {}
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_ver = before.get(key)
            new_ver = after.get(key)

            if old_ver != new_ver:
                changes[key] = {
                    "before": old_ver or "(none)",
                    "after": new_ver or "(none)",
                }

        return changes

    def _count_recommendation_changes(
        self,
        before: List[Dict],
        after: List[Dict],
    ) -> tuple[int, int, int]:
        """Count added, removed, and modified recommendations."""
        before_ids = {r.get("id") for r in before if r.get("id")}
        after_ids = {r.get("id") for r in after if r.get("id")}

        added = len(after_ids - before_ids)
        removed = len(before_ids - after_ids)

        # Count modified (same ID but different content)
        common_ids = before_ids & after_ids
        modified = 0
        before_map = {r.get("id"): r for r in before if r.get("id")}
        after_map = {r.get("id"): r for r in after if r.get("id")}

        for id_ in common_ids:
            if before_map.get(id_) != after_map.get(id_):
                modified += 1

        return added, removed, modified

    def _assess_change_impact(
        self,
        old_value: Any,
        new_value: Any,
    ) -> str:
        """Assess the impact level of a change."""
        # For numeric values, calculate percentage change
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if old_value == 0:
                return "high" if new_value != 0 else "low"
            
            pct_change = abs((new_value - old_value) / old_value)
            if pct_change > 0.3:
                return "high"
            elif pct_change > 0.1:
                return "medium"
            else:
                return "low"

        return "medium"

    def _format_time_delta(
        self,
        before: datetime,
        after: datetime,
    ) -> str:
        """Format the time difference between snapshots."""
        delta = after - before
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days} day(s), {hours} hour(s)"
        elif hours > 0:
            return f"{hours} hour(s), {minutes} minute(s)"
        else:
            return f"{minutes} minute(s)"

    def _generate_summary(
        self,
        changes: List[DeltaChange],
        model_changes: Dict,
        rule_changes: Dict,
        rec_added: int,
        rec_removed: int,
        rec_modified: int,
    ) -> str:
        """Generate a human-readable summary."""
        parts = []

        if len(changes) == 0:
            parts.append("No significant changes detected.")
        else:
            high_impact = sum(1 for c in changes if c.impact_level == "high")
            parts.append(f"Detected {len(changes)} changes ({high_impact} high-impact).")

        if model_changes:
            parts.append(f"Model version changes: {', '.join(model_changes.keys())}.")

        if rule_changes:
            parts.append(f"Rule version changes: {', '.join(rule_changes.keys())}.")

        if rec_added or rec_removed or rec_modified:
            parts.append(
                f"Recommendations: +{rec_added} added, -{rec_removed} removed, ~{rec_modified} modified."
            )

        return " ".join(parts)

    async def _persist_report(self, report: DeltaReport) -> None:
        """Persist delta report to database."""
        from app.models.audit import DeltaReportRecord

        record = DeltaReportRecord(
            id=report.report_id,
            snapshot_before_id=report.snapshot_before_id,
            snapshot_after_id=report.snapshot_after_id,
            time_delta=report.time_delta,
            changes=[c.model_dump() for c in report.changes],
            total_changes=report.total_changes,
            high_impact_changes=report.high_impact_changes,
            model_changes=report.model_changes,
            rule_changes=report.rule_changes,
            recommendations_added=report.recommendations_added,
            recommendations_removed=report.recommendations_removed,
            recommendations_modified=report.recommendations_modified,
            summary=report.summary,
        )

        self.db.add(record)
        await self.db.flush()

    async def get_delta_reports_for_user(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> List[DeltaReport]:
        """Get recent delta reports involving user's snapshots."""
        # Implementation would join with snapshots table
        return []
