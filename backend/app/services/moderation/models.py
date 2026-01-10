"""
Content Moderation Models

Data models for moderation results and actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class ContentType(str, Enum):
    """Types of content that can be moderated."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    USERNAME = "username"
    PROFILE_BIO = "profile_bio"


class ModerationCategory(str, Enum):
    """Categories of content violations."""

    # Violence & Safety
    VIOLENCE = "violence"
    VIOLENCE_GRAPHIC = "violence_graphic"
    SELF_HARM = "self_harm"
    TERRORISM = "terrorism"

    # Sexual Content
    SEXUAL = "sexual"
    SEXUAL_MINORS = "sexual_minors"
    NUDITY = "nudity"

    # Hate & Harassment
    HATE = "hate"
    HATE_THREATENING = "hate_threatening"
    HARASSMENT = "harassment"
    HARASSMENT_THREATENING = "harassment_threatening"
    BULLYING = "bullying"

    # Harmful Content
    DANGEROUS = "dangerous"
    ILLEGAL = "illegal"
    DRUGS = "drugs"
    WEAPONS = "weapons"

    # Misinformation
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    SCAM = "scam"

    # Platform-Specific
    PROFANITY = "profanity"
    PERSONAL_INFO = "personal_info"
    COPYRIGHT = "copyright"

    # Safe
    SAFE = "safe"


class ModerationAction(str, Enum):
    """Actions to take based on moderation results."""

    APPROVE = "approve"
    FLAG_FOR_REVIEW = "flag_for_review"
    AUTO_REMOVE = "auto_remove"
    WARN_USER = "warn_user"
    SHADOW_BAN = "shadow_ban"
    SUSPEND_USER = "suspend_user"
    ESCALATE = "escalate"


class ModerationSeverity(str, Enum):
    """Severity levels for content violations."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CategoryScore:
    """Score for a specific moderation category."""

    category: ModerationCategory
    score: float  # 0.0 to 1.0
    flagged: bool
    details: Optional[str] = None


@dataclass
class ModerationResult:
    """Result of content moderation analysis."""

    content_id: Optional[UUID]
    content_type: ContentType
    is_flagged: bool
    action: ModerationAction
    severity: ModerationSeverity
    categories: list[CategoryScore] = field(default_factory=list)
    primary_category: Optional[ModerationCategory] = None
    confidence: float = 0.0
    details: Optional[str] = None
    moderated_at: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "1.0"

    @property
    def flagged_categories(self) -> list[CategoryScore]:
        """Get only flagged categories."""
        return [c for c in self.categories if c.flagged]

    @property
    def highest_score_category(self) -> Optional[CategoryScore]:
        """Get the category with the highest score."""
        if not self.categories:
            return None
        return max(self.categories, key=lambda c: c.score)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/API response."""
        return {
            "content_id": str(self.content_id) if self.content_id else None,
            "content_type": self.content_type.value,
            "is_flagged": self.is_flagged,
            "action": self.action.value,
            "severity": self.severity.value,
            "primary_category": self.primary_category.value if self.primary_category else None,
            "confidence": self.confidence,
            "details": self.details,
            "moderated_at": self.moderated_at.isoformat(),
            "model_version": self.model_version,
            "categories": [
                {
                    "category": c.category.value,
                    "score": c.score,
                    "flagged": c.flagged,
                    "details": c.details,
                }
                for c in self.categories
            ],
        }


@dataclass
class ModerationConfig:
    """Configuration for moderation thresholds."""

    # Category thresholds (0.0 to 1.0)
    violence_threshold: float = 0.7
    sexual_threshold: float = 0.8
    hate_threshold: float = 0.7
    harassment_threshold: float = 0.75
    self_harm_threshold: float = 0.5
    spam_threshold: float = 0.85

    # Actions
    auto_remove_threshold: float = 0.9
    flag_for_review_threshold: float = 0.6
    warn_user_threshold: float = 0.5

    # Special handling
    zero_tolerance_categories: list[ModerationCategory] = field(
        default_factory=lambda: [
            ModerationCategory.SEXUAL_MINORS,
            ModerationCategory.TERRORISM,
            ModerationCategory.VIOLENCE_GRAPHIC,
        ]
    )

    # Rate limiting
    max_flags_before_suspension: int = 3
    flag_window_hours: int = 24


@dataclass
class ModerationReport:
    """User report of content for moderation."""

    report_id: UUID
    reporter_id: UUID
    content_id: UUID
    content_type: ContentType
    reason: ModerationCategory
    details: Optional[str]
    status: str  # pending, reviewed, actioned, dismissed
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[UUID] = None
    action_taken: Optional[ModerationAction] = None


@dataclass
class ModerationLog:
    """Log entry for moderation actions."""

    log_id: UUID
    content_id: UUID
    content_type: ContentType
    user_id: UUID
    action: ModerationAction
    reason: ModerationCategory
    automated: bool
    confidence: float
    reviewer_id: Optional[UUID]
    notes: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
