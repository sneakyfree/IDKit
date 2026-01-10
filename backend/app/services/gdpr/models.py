"""
GDPR Data Models

Data structures for GDPR compliance operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class DataRequestType(str, Enum):
    """Types of GDPR data requests."""

    EXPORT = "export"  # Data portability (Article 20)
    DELETE = "delete"  # Right to erasure (Article 17)
    ACCESS = "access"  # Right of access (Article 15)
    RECTIFY = "rectify"  # Right to rectification (Article 16)
    RESTRICT = "restrict"  # Right to restrict processing (Article 18)
    OBJECT = "object"  # Right to object (Article 21)


class DataRequestStatus(str, Enum):
    """Status of GDPR data requests."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DataCategory(str, Enum):
    """Categories of personal data."""

    PROFILE = "profile"  # Basic profile info
    CONTENT = "content"  # Posts, comments, etc.
    MEDIA = "media"  # Uploaded images/videos
    INTERACTIONS = "interactions"  # Likes, follows, etc.
    MESSAGES = "messages"  # DMs and conversations
    ANALYTICS = "analytics"  # Usage analytics
    PAYMENTS = "payments"  # Payment history
    SETTINGS = "settings"  # Preferences and settings
    AI_DATA = "ai_data"  # AI twin data
    SOCIAL = "social"  # Connected social accounts


@dataclass
class DataRequest:
    """GDPR data request record."""

    id: UUID
    user_id: UUID
    request_type: DataRequestType
    status: DataRequestStatus
    categories: list[DataCategory] = field(default_factory=list)
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportedData:
    """Exported user data structure."""

    user_id: UUID
    export_date: datetime
    categories: list[DataCategory]
    data: dict[str, Any]
    file_format: str = "json"
    checksum: Optional[str] = None


@dataclass
class DeletionResult:
    """Result of data deletion operation."""

    user_id: UUID
    deleted_at: datetime
    categories_deleted: list[DataCategory]
    items_deleted: dict[str, int]
    retained_items: dict[str, int]  # Items kept for legal reasons
    retention_reasons: list[str]


@dataclass
class ConsentRecord:
    """User consent record for tracking consent history."""

    id: UUID
    user_id: UUID
    consent_type: str  # e.g., "marketing", "analytics", "third_party"
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    version: str = "1.0"  # Consent policy version


@dataclass
class PrivacySettings:
    """User privacy preferences."""

    user_id: UUID
    profile_visibility: str = "public"  # public, followers, private
    activity_visibility: str = "followers"
    search_visibility: bool = True
    analytics_enabled: bool = True
    personalization_enabled: bool = True
    marketing_emails: bool = False
    product_updates: bool = True
    third_party_sharing: bool = False
    data_retention_preference: int = 365  # days
    updated_at: datetime = field(default_factory=datetime.utcnow)
