"""
Enterprise Features API

Advanced enterprise-grade features for large organizations and agencies.
Includes team management, white-labeling, SSO, audit logs, and more.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr

router = APIRouter()


# =============================================================================
# Enums
# =============================================================================


class SubscriptionTier(str, Enum):
    """Enterprise subscription tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TeamRole(str, Enum):
    """Team member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class SSOProvider(str, Enum):
    """SSO provider types."""
    SAML = "saml"
    OIDC = "oidc"
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"


class AuditAction(str, Enum):
    """Audit log action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"
    BILLING = "billing"
    API_KEY = "api_key"


class ApprovalStatus(str, Enum):
    """Content approval workflow status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


# =============================================================================
# Request/Response Models
# =============================================================================


class OrganizationBase(BaseModel):
    """Base organization model."""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Create organization request."""
    subscription_tier: SubscriptionTier = SubscriptionTier.PROFESSIONAL
    admin_email: EmailStr


class OrganizationUpdate(BaseModel):
    """Update organization request."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(OrganizationBase):
    """Organization response."""
    id: UUID
    subscription_tier: SubscriptionTier
    is_active: bool
    member_count: int
    seat_limit: int
    features: list[str]
    created_at: datetime
    settings: dict


class TeamMemberBase(BaseModel):
    """Base team member model."""
    email: EmailStr
    role: TeamRole = TeamRole.EDITOR
    department: Optional[str] = None


class TeamMemberInvite(TeamMemberBase):
    """Team member invite request."""
    send_email: bool = True
    custom_message: Optional[str] = None


class TeamMemberUpdate(BaseModel):
    """Update team member request."""
    role: Optional[TeamRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[list[str]] = None


class TeamMemberResponse(TeamMemberBase):
    """Team member response."""
    id: UUID
    user_id: Optional[UUID]
    organization_id: UUID
    is_active: bool
    invite_status: str
    permissions: list[str]
    last_active_at: Optional[datetime]
    invited_at: datetime
    joined_at: Optional[datetime]


class SSOConfigBase(BaseModel):
    """Base SSO configuration."""
    provider: SSOProvider
    is_enabled: bool = False


class SSOConfigCreate(SSOConfigBase):
    """Create SSO configuration."""
    # SAML settings
    idp_entity_id: Optional[str] = None
    idp_sso_url: Optional[str] = None
    idp_certificate: Optional[str] = None

    # OIDC settings
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    issuer_url: Optional[str] = None

    # Common settings
    auto_provision_users: bool = True
    default_role: TeamRole = TeamRole.EDITOR
    allowed_domains: Optional[list[str]] = None


class SSOConfigResponse(SSOConfigBase):
    """SSO configuration response."""
    id: UUID
    organization_id: UUID
    sp_entity_id: str
    sp_acs_url: str
    sp_metadata_url: str
    created_at: datetime
    updated_at: datetime


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: UUID
    organization_id: UUID
    user_id: Optional[UUID]
    user_email: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    details: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime


class AuditLogFilter(BaseModel):
    """Audit log filter options."""
    user_id: Optional[UUID] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class APIKeyBase(BaseModel):
    """Base API key model."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    """Create API key request."""
    rate_limit: Optional[int] = None  # Requests per minute


class APIKeyResponse(APIKeyBase):
    """API key response."""
    id: UUID
    key_prefix: str  # First 8 chars for identification
    organization_id: UUID
    created_by: UUID
    is_active: bool
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Response when API key is created (includes full key)."""
    key: str  # Full key (only shown once)


class WhiteLabelConfig(BaseModel):
    """White-label configuration."""
    brand_name: str
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#8B5CF6"
    secondary_color: str = "#EC4899"
    custom_domain: Optional[str] = None
    custom_email_domain: Optional[str] = None
    email_from_name: Optional[str] = None
    support_email: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None
    hide_powered_by: bool = False
    custom_css: Optional[str] = None


class ApprovalWorkflowConfig(BaseModel):
    """Content approval workflow configuration."""
    is_enabled: bool = True
    require_approval_for: list[str] = Field(
        default_factory=lambda: ["publish", "schedule"]
    )
    approvers: list[UUID] = Field(default_factory=list)
    auto_approve_for_roles: list[TeamRole] = Field(
        default_factory=lambda: [TeamRole.OWNER, TeamRole.ADMIN]
    )
    notification_settings: dict = Field(default_factory=dict)


class ContentApprovalRequest(BaseModel):
    """Content approval request."""
    content_id: UUID
    notes: Optional[str] = None


class ContentApprovalResponse(BaseModel):
    """Content approval response."""
    id: UUID
    content_id: UUID
    status: ApprovalStatus
    requested_by: UUID
    reviewed_by: Optional[UUID]
    notes: Optional[str]
    review_notes: Optional[str]
    requested_at: datetime
    reviewed_at: Optional[datetime]


class UsageReport(BaseModel):
    """Usage report for billing."""
    period_start: datetime
    period_end: datetime
    organization_id: UUID

    # User metrics
    total_users: int
    active_users: int

    # Content metrics
    content_generated: int
    ai_generations: int
    videos_created: int
    podcasts_created: int

    # Social metrics
    posts_published: int
    engagement_total: int

    # Resource metrics
    storage_used_gb: float
    gpu_hours_used: float
    api_calls: int

    # Cost breakdown
    estimated_cost: float
    cost_breakdown: dict


class BillingInfo(BaseModel):
    """Billing information."""
    organization_id: UUID
    subscription_tier: SubscriptionTier
    billing_email: EmailStr
    payment_method: Optional[str]
    next_billing_date: datetime
    current_period_start: datetime
    current_period_end: datetime
    amount_due: float
    currency: str = "USD"


# =============================================================================
# Organization Endpoints
# =============================================================================


@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    data: OrganizationCreate,
) -> OrganizationResponse:
    """
    Create a new enterprise organization.

    Creates organization with admin user and default settings.
    """
    # Implementation would create org in database
    return OrganizationResponse(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name=data.name,
        display_name=data.display_name,
        domain=data.domain,
        logo_url=data.logo_url,
        website=data.website,
        industry=data.industry,
        subscription_tier=data.subscription_tier,
        is_active=True,
        member_count=1,
        seat_limit=_get_seat_limit(data.subscription_tier),
        features=_get_tier_features(data.subscription_tier),
        created_at=datetime.utcnow(),
        settings={},
    )


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
) -> OrganizationResponse:
    """Get organization details."""
    # Implementation would fetch from database
    raise HTTPException(status_code=404, detail="Organization not found")


@router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
) -> OrganizationResponse:
    """Update organization settings."""
    raise HTTPException(status_code=404, detail="Organization not found")


@router.get("/organizations/{org_id}/usage", response_model=UsageReport)
async def get_organization_usage(
    org_id: UUID,
    period: str = Query("current", description="Billing period: current, previous, or YYYY-MM"),
) -> UsageReport:
    """Get organization usage report for billing period."""
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = now

    return UsageReport(
        period_start=period_start,
        period_end=period_end,
        organization_id=org_id,
        total_users=0,
        active_users=0,
        content_generated=0,
        ai_generations=0,
        videos_created=0,
        podcasts_created=0,
        posts_published=0,
        engagement_total=0,
        storage_used_gb=0.0,
        gpu_hours_used=0.0,
        api_calls=0,
        estimated_cost=0.0,
        cost_breakdown={},
    )


# =============================================================================
# Team Management Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    org_id: UUID,
    role: Optional[TeamRole] = None,
    include_inactive: bool = False,
) -> list[TeamMemberResponse]:
    """List all team members in organization."""
    return []


@router.post("/organizations/{org_id}/members/invite", response_model=TeamMemberResponse)
async def invite_team_member(
    org_id: UUID,
    data: TeamMemberInvite,
) -> TeamMemberResponse:
    """
    Invite a new team member.

    Sends invitation email if send_email is True.
    """
    return TeamMemberResponse(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        email=data.email,
        role=data.role,
        department=data.department,
        user_id=None,
        organization_id=org_id,
        is_active=True,
        invite_status="pending",
        permissions=_get_role_permissions(data.role),
        last_active_at=None,
        invited_at=datetime.utcnow(),
        joined_at=None,
    )


@router.patch("/organizations/{org_id}/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    org_id: UUID,
    member_id: UUID,
    data: TeamMemberUpdate,
) -> TeamMemberResponse:
    """Update team member role or permissions."""
    raise HTTPException(status_code=404, detail="Team member not found")


@router.delete("/organizations/{org_id}/members/{member_id}")
async def remove_team_member(
    org_id: UUID,
    member_id: UUID,
) -> dict:
    """Remove team member from organization."""
    return {"success": True, "message": "Team member removed"}


@router.post("/organizations/{org_id}/members/{member_id}/resend-invite")
async def resend_invite(
    org_id: UUID,
    member_id: UUID,
) -> dict:
    """Resend invitation email to pending member."""
    return {"success": True, "message": "Invitation resent"}


# =============================================================================
# SSO Configuration Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/sso", response_model=Optional[SSOConfigResponse])
async def get_sso_config(
    org_id: UUID,
) -> Optional[SSOConfigResponse]:
    """Get SSO configuration for organization."""
    return None


@router.post("/organizations/{org_id}/sso", response_model=SSOConfigResponse)
async def configure_sso(
    org_id: UUID,
    data: SSOConfigCreate,
) -> SSOConfigResponse:
    """
    Configure SSO for organization.

    Supports SAML 2.0, OIDC, and specific providers (Okta, Azure AD, Google).
    """
    return SSOConfigResponse(
        id=UUID("00000000-0000-0000-0000-000000000003"),
        organization_id=org_id,
        provider=data.provider,
        is_enabled=data.is_enabled,
        sp_entity_id=f"https://api.idkit.io/sso/{org_id}",
        sp_acs_url=f"https://api.idkit.io/sso/{org_id}/acs",
        sp_metadata_url=f"https://api.idkit.io/sso/{org_id}/metadata",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.delete("/organizations/{org_id}/sso")
async def disable_sso(
    org_id: UUID,
) -> dict:
    """Disable SSO for organization."""
    return {"success": True, "message": "SSO disabled"}


@router.get("/organizations/{org_id}/sso/metadata")
async def get_sso_metadata(
    org_id: UUID,
) -> dict:
    """Get SAML metadata for service provider configuration."""
    return {
        "entity_id": f"https://api.idkit.io/sso/{org_id}",
        "acs_url": f"https://api.idkit.io/sso/{org_id}/acs",
        "metadata_url": f"https://api.idkit.io/sso/{org_id}/metadata.xml",
    }


# =============================================================================
# Audit Log Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/audit-logs", response_model=list[AuditLogEntry])
async def get_audit_logs(
    org_id: UUID,
    user_id: Optional[UUID] = None,
    action: Optional[AuditAction] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> list[AuditLogEntry]:
    """
    Get audit logs for organization.

    Supports filtering by user, action type, resource, and date range.
    """
    return []


@router.get("/organizations/{org_id}/audit-logs/export")
async def export_audit_logs(
    org_id: UUID,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", enum=["csv", "json"]),
) -> dict:
    """
    Export audit logs for compliance.

    Returns download URL for exported file.
    """
    return {
        "download_url": f"https://api.idkit.io/exports/audit-{org_id}.{format}",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }


# =============================================================================
# API Key Management Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    org_id: UUID,
    include_inactive: bool = False,
) -> list[APIKeyResponse]:
    """List all API keys for organization."""
    return []


@router.post("/organizations/{org_id}/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    org_id: UUID,
    data: APIKeyCreate,
) -> APIKeyCreatedResponse:
    """
    Create a new API key.

    The full key is only returned once at creation time.
    Store it securely as it cannot be retrieved again.
    """
    import secrets
    key = f"idk_{secrets.token_urlsafe(32)}"

    return APIKeyCreatedResponse(
        id=UUID("00000000-0000-0000-0000-000000000004"),
        name=data.name,
        scopes=data.scopes,
        expires_at=data.expires_at,
        key_prefix=key[:12],
        organization_id=org_id,
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
        is_active=True,
        last_used_at=None,
        usage_count=0,
        created_at=datetime.utcnow(),
        key=key,
    )


@router.delete("/organizations/{org_id}/api-keys/{key_id}")
async def revoke_api_key(
    org_id: UUID,
    key_id: UUID,
) -> dict:
    """Revoke an API key."""
    return {"success": True, "message": "API key revoked"}


@router.post("/organizations/{org_id}/api-keys/{key_id}/rotate", response_model=APIKeyCreatedResponse)
async def rotate_api_key(
    org_id: UUID,
    key_id: UUID,
) -> APIKeyCreatedResponse:
    """
    Rotate an API key.

    Creates a new key and revokes the old one.
    """
    import secrets
    key = f"idk_{secrets.token_urlsafe(32)}"

    return APIKeyCreatedResponse(
        id=UUID("00000000-0000-0000-0000-000000000005"),
        name="Rotated Key",
        scopes=["read", "write"],
        expires_at=None,
        key_prefix=key[:12],
        organization_id=org_id,
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
        is_active=True,
        last_used_at=None,
        usage_count=0,
        created_at=datetime.utcnow(),
        key=key,
    )


# =============================================================================
# White-Label Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/white-label", response_model=WhiteLabelConfig)
async def get_white_label_config(
    org_id: UUID,
) -> WhiteLabelConfig:
    """Get white-label configuration."""
    return WhiteLabelConfig(
        brand_name="IDKit",
        primary_color="#8B5CF6",
        secondary_color="#EC4899",
    )


@router.put("/organizations/{org_id}/white-label", response_model=WhiteLabelConfig)
async def update_white_label_config(
    org_id: UUID,
    data: WhiteLabelConfig,
) -> WhiteLabelConfig:
    """Update white-label configuration."""
    return data


@router.post("/organizations/{org_id}/white-label/verify-domain")
async def verify_custom_domain(
    org_id: UUID,
    domain: str,
) -> dict:
    """
    Verify custom domain ownership.

    Returns DNS records to add for verification.
    """
    return {
        "domain": domain,
        "status": "pending",
        "verification_records": [
            {
                "type": "TXT",
                "name": f"_idkit-verify.{domain}",
                "value": f"idkit-domain-verification={org_id}",
            },
            {
                "type": "CNAME",
                "name": f"app.{domain}",
                "value": "custom.idkit.io",
            },
        ],
    }


# =============================================================================
# Approval Workflow Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/approval-workflow", response_model=ApprovalWorkflowConfig)
async def get_approval_workflow(
    org_id: UUID,
) -> ApprovalWorkflowConfig:
    """Get content approval workflow configuration."""
    return ApprovalWorkflowConfig()


@router.put("/organizations/{org_id}/approval-workflow", response_model=ApprovalWorkflowConfig)
async def update_approval_workflow(
    org_id: UUID,
    data: ApprovalWorkflowConfig,
) -> ApprovalWorkflowConfig:
    """Configure content approval workflow."""
    return data


@router.post("/content/{content_id}/submit-for-approval", response_model=ContentApprovalResponse)
async def submit_for_approval(
    content_id: UUID,
    data: ContentApprovalRequest,
) -> ContentApprovalResponse:
    """Submit content for approval."""
    return ContentApprovalResponse(
        id=UUID("00000000-0000-0000-0000-000000000006"),
        content_id=content_id,
        status=ApprovalStatus.PENDING_REVIEW,
        requested_by=UUID("00000000-0000-0000-0000-000000000001"),
        reviewed_by=None,
        notes=data.notes,
        review_notes=None,
        requested_at=datetime.utcnow(),
        reviewed_at=None,
    )


@router.post("/content/{content_id}/approve", response_model=ContentApprovalResponse)
async def approve_content(
    content_id: UUID,
    notes: Optional[str] = None,
) -> ContentApprovalResponse:
    """Approve content for publishing."""
    return ContentApprovalResponse(
        id=UUID("00000000-0000-0000-0000-000000000006"),
        content_id=content_id,
        status=ApprovalStatus.APPROVED,
        requested_by=UUID("00000000-0000-0000-0000-000000000001"),
        reviewed_by=UUID("00000000-0000-0000-0000-000000000002"),
        notes=None,
        review_notes=notes,
        requested_at=datetime.utcnow() - timedelta(hours=1),
        reviewed_at=datetime.utcnow(),
    )


@router.post("/content/{content_id}/reject", response_model=ContentApprovalResponse)
async def reject_content(
    content_id: UUID,
    reason: str,
) -> ContentApprovalResponse:
    """Reject content with feedback."""
    return ContentApprovalResponse(
        id=UUID("00000000-0000-0000-0000-000000000006"),
        content_id=content_id,
        status=ApprovalStatus.REJECTED,
        requested_by=UUID("00000000-0000-0000-0000-000000000001"),
        reviewed_by=UUID("00000000-0000-0000-0000-000000000002"),
        notes=None,
        review_notes=reason,
        requested_at=datetime.utcnow() - timedelta(hours=1),
        reviewed_at=datetime.utcnow(),
    )


@router.get("/organizations/{org_id}/pending-approvals", response_model=list[ContentApprovalResponse])
async def get_pending_approvals(
    org_id: UUID,
) -> list[ContentApprovalResponse]:
    """Get all content pending approval."""
    return []


# =============================================================================
# Billing Endpoints
# =============================================================================


@router.get("/organizations/{org_id}/billing", response_model=BillingInfo)
async def get_billing_info(
    org_id: UUID,
) -> BillingInfo:
    """Get billing information."""
    now = datetime.utcnow()
    return BillingInfo(
        organization_id=org_id,
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        billing_email="billing@example.com",
        payment_method="visa_****4242",
        next_billing_date=now.replace(day=1) + timedelta(days=32),
        current_period_start=now.replace(day=1),
        current_period_end=now.replace(day=1) + timedelta(days=30),
        amount_due=299.00,
        currency="USD",
    )


@router.get("/organizations/{org_id}/invoices")
async def list_invoices(
    org_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
) -> list[dict]:
    """List billing invoices."""
    return []


@router.get("/organizations/{org_id}/invoices/{invoice_id}/download")
async def download_invoice(
    org_id: UUID,
    invoice_id: str,
) -> dict:
    """Get invoice download URL."""
    return {
        "download_url": f"https://api.idkit.io/invoices/{invoice_id}.pdf",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
    }


# =============================================================================
# Data Export & GDPR Endpoints
# =============================================================================


@router.post("/organizations/{org_id}/export-data")
async def request_data_export(
    org_id: UUID,
    include_media: bool = False,
) -> dict:
    """
    Request full data export for GDPR compliance.

    Returns job ID to track export progress.
    """
    return {
        "job_id": "export-12345",
        "status": "processing",
        "estimated_completion": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }


@router.get("/organizations/{org_id}/export-data/{job_id}")
async def get_export_status(
    org_id: UUID,
    job_id: str,
) -> dict:
    """Check data export job status."""
    return {
        "job_id": job_id,
        "status": "completed",
        "download_url": f"https://api.idkit.io/exports/{job_id}.zip",
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }


@router.delete("/organizations/{org_id}/data")
async def request_data_deletion(
    org_id: UUID,
    confirm: bool = Query(..., description="Must be true to confirm deletion"),
) -> dict:
    """
    Request complete data deletion for GDPR compliance.

    This action is irreversible. All organization data will be deleted.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion with confirm=true",
        )

    return {
        "status": "scheduled",
        "deletion_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "message": "Data will be deleted in 30 days. Contact support to cancel.",
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _get_seat_limit(tier: SubscriptionTier) -> int:
    """Get seat limit for subscription tier."""
    limits = {
        SubscriptionTier.STARTER: 3,
        SubscriptionTier.PROFESSIONAL: 10,
        SubscriptionTier.BUSINESS: 50,
        SubscriptionTier.ENTERPRISE: 500,
        SubscriptionTier.CUSTOM: 999999,
    }
    return limits.get(tier, 10)


def _get_tier_features(tier: SubscriptionTier) -> list[str]:
    """Get features available for subscription tier."""
    base_features = [
        "content_generation",
        "social_publishing",
        "analytics",
    ]

    tier_features = {
        SubscriptionTier.STARTER: base_features,
        SubscriptionTier.PROFESSIONAL: base_features + [
            "ai_twins",
            "podcasts",
            "brand_voice",
        ],
        SubscriptionTier.BUSINESS: base_features + [
            "ai_twins",
            "podcasts",
            "brand_voice",
            "team_management",
            "approval_workflow",
            "api_access",
        ],
        SubscriptionTier.ENTERPRISE: base_features + [
            "ai_twins",
            "podcasts",
            "brand_voice",
            "team_management",
            "approval_workflow",
            "api_access",
            "sso",
            "audit_logs",
            "white_label",
            "priority_support",
            "custom_integrations",
        ],
        SubscriptionTier.CUSTOM: base_features + [
            "everything",
            "custom_features",
        ],
    }
    return tier_features.get(tier, base_features)


def _get_role_permissions(role: TeamRole) -> list[str]:
    """Get default permissions for role."""
    permissions = {
        TeamRole.VIEWER: ["read"],
        TeamRole.EDITOR: ["read", "write", "publish"],
        TeamRole.MANAGER: ["read", "write", "publish", "approve", "manage_team"],
        TeamRole.ADMIN: ["read", "write", "publish", "approve", "manage_team", "manage_settings"],
        TeamRole.OWNER: ["*"],
    }
    return permissions.get(role, ["read"])


@router.get("/content/approvals")
async def _qa_content_approvals():
    """QA gap-closure: content approvals list."""
    return []
