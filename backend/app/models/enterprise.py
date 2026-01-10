"""
Enterprise Models

Database models for enterprise features including organizations,
teams, SSO, API keys, and audit logging.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class OrganizationPlan(str, Enum):
    """Organization subscription plans."""

    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class MemberRole(str, Enum):
    """Team member roles."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class InviteStatus(str, Enum):
    """Team invite status."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Organization/Team for enterprise accounts.

    Allows multiple users to collaborate under a single billing account.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Billing
    plan: Mapped[str] = mapped_column(
        String(50),
        default=OrganizationPlan.TEAM.value,
        nullable=False,
    )

    billing_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Limits
    max_members: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    max_ai_twins: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    max_storage_gb: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    # Settings
    settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # White labeling
    white_label_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    brand_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # Custom colors, logo, domain

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    suspension_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    sso_config: Mapped[Optional["SSOConfiguration"]] = relationship(
        "SSOConfiguration",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"


class TeamMember(Base, UUIDMixin, TimestampMixin):
    """
    Team member association between User and Organization.
    """

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_team_member"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default=MemberRole.MEMBER.value,
        nullable=False,
    )

    # Permissions (can override role defaults)
    permissions: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Invitation tracking
    invited_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )

    invited_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )

    def __repr__(self) -> str:
        return f"<TeamMember {self.user_id} in {self.organization_id}>"


class TeamInvite(Base, UUIDMixin, TimestampMixin):
    """
    Pending team invitations.
    """

    __tablename__ = "team_invites"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default=MemberRole.MEMBER.value,
        nullable=False,
    )

    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=InviteStatus.PENDING.value,
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    invited_by: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<TeamInvite {self.email} to {self.organization_id}>"


class SSOConfiguration(Base, UUIDMixin, TimestampMixin):
    """
    SSO configuration for enterprise organizations.
    """

    __tablename__ = "sso_configurations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # 'saml', 'oidc', 'okta', 'azure_ad', 'google_workspace'

    # SAML settings
    saml_entity_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    saml_sso_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    saml_certificate: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # OIDC settings
    oidc_issuer: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    oidc_client_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    oidc_client_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # Encrypted

    # General settings
    domain_restriction: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )  # Allowed email domains

    auto_provision: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )  # Auto-create users on first login

    default_role: Mapped[str] = mapped_column(
        String(50),
        default=MemberRole.MEMBER.value,
        nullable=False,
    )

    # Status
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="sso_config",
    )

    def __repr__(self) -> str:
        return f"<SSOConfiguration {self.provider_type} for {self.organization_id}>"


class APIKey(Base, UUIDMixin, TimestampMixin):
    """
    API keys for programmatic access.
    """

    __tablename__ = "api_keys"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Key (hashed, prefix stored for display)
    key_prefix: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # First 8 chars for display

    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Permissions
    scopes: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )  # ['read:content', 'write:posts', etc.]

    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
    )  # Requests per hour

    # Restrictions
    allowed_ips: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    allowed_origins: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_used_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="api_keys",
    )

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix}*** for {self.user_id}>"


class AuditLog(Base, UUIDMixin):
    """
    Audit log for tracking important actions.

    Immutable log entries for compliance and security.
    """

    __tablename__ = "audit_logs"

    # Who
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
    )

    # What
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # 'user.login', 'content.create', 'twin.generate', etc.

    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )  # 'user', 'post', 'ai_twin', etc.

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Details
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    changes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # {field: {old: x, new: y}}

    # Context
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Result
    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        nullable=False,
    )  # 'success', 'failure', 'error'

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamp (no updated_at since logs are immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"


class ContentApproval(Base, UUIDMixin, TimestampMixin):
    """
    Content approval workflow for enterprise teams.
    """

    __tablename__ = "content_approvals"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # 'post', 'episode', 'video', etc.

    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Workflow
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # 'pending', 'approved', 'rejected', 'revision_requested'

    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
    )  # 'low', 'normal', 'high', 'urgent'

    # Review
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Auto-publish settings
    auto_publish: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    scheduled_publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    submitted_by: Mapped["User"] = relationship(
        "User", foreign_keys=[submitted_by_id]
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewer_id]
    )

    def __repr__(self) -> str:
        return f"<ContentApproval {self.content_type}:{self.content_id}>"
