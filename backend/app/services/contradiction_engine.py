"""
Contradiction Engine

Detects and manages data contradictions between user-reported values
and API-verified data. Core component of the TurboTax-style intake.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake import ContradictionRecord, IntakeAnswer, VerificationTask
from app.schemas.source_labeling import (
    ContradictionAlert,
    DataSourceType,
    VerificationRequest,
)


class ContradictionEngine:
    """
    Detects and manages contradictions in creator data.
    
    Examples of contradictions:
    - User reports 100K followers, Instagram API shows 10K
    - User claims 5% engagement rate, calculated rate is 1.2%
    - User says "verified account", API shows not verified
    """

    # Thresholds for flagging numeric discrepancies
    NUMERIC_THRESHOLD_PERCENT = 20.0  # Flag if >20% difference
    HIGH_SEVERITY_THRESHOLD = 50.0     # High severity if >50% off

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare_values(
        self,
        field_name: str,
        user_value: Any,
        api_value: Any,
        user_confidence: float = 1.0,
        api_confidence: float = 0.99,
    ) -> Optional[ContradictionAlert]:
        """
        Compare user-reported value against API-verified value.
        
        Returns ContradictionAlert if significant discrepancy found.
        """
        # Skip if either value is None
        if user_value is None or api_value is None:
            return None

        discrepancy = None
        severity = "medium"

        # Numeric comparison
        if isinstance(user_value, (int, float)) and isinstance(api_value, (int, float)):
            if api_value != 0:
                discrepancy = abs((user_value - api_value) / api_value) * 100
            elif user_value != 0:
                discrepancy = 100.0  # Complete mismatch
            else:
                discrepancy = 0.0  # Both zero

            # Check if discrepancy exceeds threshold
            if discrepancy < self.NUMERIC_THRESHOLD_PERCENT:
                return None  # Within acceptable range

            severity = "high" if discrepancy > self.HIGH_SEVERITY_THRESHOLD else "medium"

        # String comparison (case-insensitive)
        elif isinstance(user_value, str) and isinstance(api_value, str):
            if user_value.lower().strip() == api_value.lower().strip():
                return None
            severity = "low"  # String mismatches usually less critical

        # Boolean comparison
        elif isinstance(user_value, bool) and isinstance(api_value, bool):
            if user_value == api_value:
                return None
            severity = "medium"

        # List comparison
        elif isinstance(user_value, list) and isinstance(api_value, list):
            if set(user_value) == set(api_value):
                return None
            severity = "low"

        # Different types or complex objects
        else:
            if user_value == api_value:
                return None
            severity = "low"

        return ContradictionAlert(
            contradiction_id=uuid4(),
            field_name=field_name,
            value_a=user_value,
            source_a=DataSourceType.USER_INPUT,
            confidence_a=user_confidence,
            value_b=api_value,
            source_b=DataSourceType.API_VERIFIED,
            confidence_b=api_confidence,
            discrepancy_percent=discrepancy,
            severity=severity,
            suggested_resolution=self._suggest_resolution(severity, api_confidence),
        )

    def _suggest_resolution(
        self,
        severity: str,
        api_confidence: float,
    ) -> str:
        """Suggest how to resolve the contradiction."""
        if api_confidence > 0.95:
            return "accept_api"  # High-confidence API data
        elif severity == "low":
            return "accept_user"  # Minor discrepancy, trust user
        else:
            return "verify"  # Need human verification

    async def detect_contradictions(
        self,
        user_id: UUID,
        user_data: dict[str, Any],
        api_data: dict[str, Any],
        field_labels: dict[str, str],
    ) -> list[ContradictionAlert]:
        """
        Scan for contradictions between user-reported and API data.
        
        Args:
            user_id: The user's ID
            user_data: Dict of field_name -> user-reported value
            api_data: Dict of field_name -> API-verified value
            field_labels: Dict of field_name -> human-readable label
            
        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Find common fields
        common_fields = set(user_data.keys()) & set(api_data.keys())

        for field in common_fields:
            alert = await self.compare_values(
                field_name=field,
                user_value=user_data[field],
                api_value=api_data[field],
            )

            if alert:
                contradictions.append(alert)

        return contradictions

    async def save_contradiction(
        self,
        user_id: UUID,
        alert: ContradictionAlert,
        field_label: str,
    ) -> ContradictionRecord:
        """Persist a contradiction to the database."""
        record = ContradictionRecord(
            user_id=user_id,
            field_name=alert.field_name,
            field_label=field_label,
            value_a=alert.value_a,
            source_a=alert.source_a.value,
            confidence_a=alert.confidence_a,
            value_b=alert.value_b,
            source_b=alert.source_b.value,
            confidence_b=alert.confidence_b,
            discrepancy_percent=alert.discrepancy_percent,
            severity=alert.severity,
        )

        self.db.add(record)
        await self.db.flush()
        return record

    async def resolve_contradiction(
        self,
        contradiction_id: UUID,
        resolution: str,
        resolved_value: Any,
        resolved_by: str,
        explanation: Optional[str] = None,
    ) -> Optional[ContradictionRecord]:
        """Mark a contradiction as resolved."""
        result = await self.db.execute(
            select(ContradictionRecord).where(
                ContradictionRecord.id == contradiction_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        record.is_resolved = True
        record.resolution = resolution
        record.resolved_value = resolved_value
        record.resolved_by = resolved_by
        record.resolved_at = datetime.utcnow()
        record.explanation = explanation

        await self.db.flush()
        return record

    async def get_unresolved_contradictions(
        self,
        user_id: UUID,
    ) -> list[ContradictionRecord]:
        """Get all unresolved contradictions for a user."""
        result = await self.db.execute(
            select(ContradictionRecord).where(
                ContradictionRecord.user_id == user_id,
                ContradictionRecord.is_resolved == False,  # noqa: E712
            ).order_by(ContradictionRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_verification_task(
        self,
        user_id: UUID,
        request: VerificationRequest,
        answer_id: Optional[UUID] = None,
    ) -> VerificationTask:
        """Create a verification task for uncertain data."""
        task = VerificationTask(
            user_id=user_id,
            answer_id=answer_id,
            question_id=request.field_name,
            question_label=request.field_name.replace("_", " ").title(),
            current_value=request.current_value,
            current_confidence=request.current_confidence,
            verification_method=request.verification_method,
            instructions=request.instructions,
            priority=request.priority,
        )

        self.db.add(task)
        await self.db.flush()
        return task


def calculate_confidence_score(
    source: DataSourceType,
    has_evidence: bool = False,
    is_recent: bool = True,
) -> float:
    """
    Calculate confidence score based on data source and factors.
    
    Scores:
    - API verified: 0.95-0.99
    - User input with evidence: 0.80-0.90
    - User input without evidence: 0.50-0.70
    - Estimated: 0.30-0.50
    - Unknown: 0.10-0.30
    """
    base_scores = {
        DataSourceType.API_VERIFIED: 0.95,
        DataSourceType.USER_INPUT: 0.60,
        DataSourceType.ESTIMATED: 0.40,
        DataSourceType.UNKNOWN: 0.20,
    }

    score = base_scores.get(source, 0.50)

    # Boost for evidence
    if has_evidence and source == DataSourceType.USER_INPUT:
        score += 0.20

    # Penalty for stale data
    if not is_recent:
        score -= 0.10

    return min(max(score, 0.0), 1.0)
