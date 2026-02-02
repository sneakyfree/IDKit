"""
Stub API Endpoints for New Features

Returns mock data to enable frontend development.
These endpoints will be replaced with real implementations
once database models and business logic are complete.

Usage: Include router in main.py:
    from app.api.v1.stubs import router as stubs_router
    app.include_router(stubs_router, prefix="/api/v1")
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["stubs"])


# ==================== API Keys (Developer Portal) ====================

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: datetime
    scopes: List[str]
    status: str = "active"
    last_used_at: Optional[datetime] = None


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: List[str]


class ApiKeyCreateResponse(ApiKeyResponse):
    secret: str  # Only returned on creation


MOCK_API_KEYS = [
    ApiKeyResponse(
        id="key-1",
        name="Production API",
        prefix="pk_live_****",
        created_at=datetime.now() - timedelta(days=30),
        scopes=["read:content", "write:content"],
        status="active",
        last_used_at=datetime.now() - timedelta(hours=2),
    ),
    ApiKeyResponse(
        id="key-2",
        name="Development",
        prefix="pk_test_****",
        created_at=datetime.now() - timedelta(days=7),
        scopes=["read:content"],
        status="active",
    ),
]


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys():
    return MOCK_API_KEYS


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(request: ApiKeyCreateRequest):
    return ApiKeyCreateResponse(
        id=f"key-{uuid4().hex[:8]}",
        name=request.name,
        prefix="pk_live_****",
        created_at=datetime.now(),
        scopes=request.scopes,
        status="active",
        secret=f"pk_live_{uuid4().hex}",
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    return {"success": True}


@router.get("/api-keys/{key_id}/usage")
async def get_api_key_usage(key_id: str, period: str = "week"):
    days = {"day": 1, "week": 7, "month": 30}.get(period, 7)
    return {
        "timestamps": [(datetime.now() - timedelta(days=i)).isoformat() for i in range(days)],
        "requests": [100 + i * 10 for i in range(days)],
    }


# ==================== Contracts ====================

class DeliverableResponse(BaseModel):
    id: str
    description: str
    due_date: datetime
    status: str = "pending"


class ContractResponse(BaseModel):
    id: str
    title: str
    brand_name: str
    status: str = "active"
    value_cents: int
    created_at: datetime
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    deliverables: List[DeliverableResponse] = []


MOCK_CONTRACTS = [
    ContractResponse(
        id="contract-1",
        title="Summer Campaign 2026",
        brand_name="Nike",
        status="active",
        value_cents=500000,
        created_at=datetime.now() - timedelta(days=14),
        signed_at=datetime.now() - timedelta(days=7),
        expires_at=datetime.now() + timedelta(days=60),
        deliverables=[
            DeliverableResponse(id="d1", description="Instagram Post", due_date=datetime.now() + timedelta(days=7), status="pending"),
            DeliverableResponse(id="d2", description="TikTok Video", due_date=datetime.now() + timedelta(days=14), status="pending"),
        ],
    ),
]


@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts():
    return MOCK_CONTRACTS


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: str):
    return MOCK_CONTRACTS[0]


@router.post("/contracts", response_model=ContractResponse)
async def create_contract(request: dict):
    return ContractResponse(
        id=f"contract-{uuid4().hex[:8]}",
        title=request.get("title", "New Contract"),
        brand_name=request.get("brand_name", "Unknown"),
        status="draft",
        value_cents=request.get("value_cents", 0),
        created_at=datetime.now(),
        deliverables=[],
    )


@router.post("/contracts/{contract_id}/sign", response_model=ContractResponse)
async def sign_contract(contract_id: str):
    contract = MOCK_CONTRACTS[0].model_copy()
    contract.status = "active"
    contract.signed_at = datetime.now()
    return contract


# ==================== Contract Templates ====================

class ContractTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    variables: List[dict]
    content: str
    usage_count: int = 0


MOCK_TEMPLATES = [
    ContractTemplateResponse(
        id="tmpl-1",
        name="Brand Sponsorship",
        description="Standard brand sponsorship agreement",
        category="Sponsorship",
        variables=[{"name": "brand_name", "type": "string", "required": True}],
        content="This agreement is between {{creator_name}} and {{brand_name}}...",
        usage_count=45,
    ),
    ContractTemplateResponse(
        id="tmpl-2",
        name="Affiliate Partnership",
        description="Revenue sharing affiliate agreement",
        category="Affiliate",
        variables=[{"name": "commission_rate", "type": "number", "required": True}],
        content="This affiliate agreement between {{creator_name}}...",
        usage_count=32,
    ),
]


@router.get("/contracts/templates", response_model=List[ContractTemplateResponse])
async def list_contract_templates():
    return MOCK_TEMPLATES


@router.get("/contracts/templates/{template_id}", response_model=ContractTemplateResponse)
async def get_contract_template(template_id: str):
    return MOCK_TEMPLATES[0]


# ==================== Collaborations ====================

class CollaboratorResponse(BaseModel):
    id: str
    name: str
    avatar_url: str
    role: str = "collaborator"


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    content: str
    sent_at: datetime


class CollaborationResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str = "in_progress"
    collaborators: List[CollaboratorResponse] = []
    created_at: datetime
    messages: List[MessageResponse] = []


MOCK_COLLABORATIONS = [
    CollaborationResponse(
        id="collab-1",
        name="Summer Music Video",
        description="Collaborative music video project",
        status="in_progress",
        collaborators=[
            CollaboratorResponse(id="u1", name="You", avatar_url="/avatars/1.jpg", role="owner"),
            CollaboratorResponse(id="u2", name="Alex Music", avatar_url="/avatars/2.jpg", role="collaborator"),
        ],
        created_at=datetime.now() - timedelta(days=5),
        messages=[
            MessageResponse(id="m1", sender_id="u2", content="Ready for the shoot tomorrow?", sent_at=datetime.now() - timedelta(hours=2)),
        ],
    ),
]


@router.get("/collaborations", response_model=List[CollaborationResponse])
async def list_collaborations():
    return MOCK_COLLABORATIONS


@router.get("/collaborations/{collaboration_id}", response_model=CollaborationResponse)
async def get_collaboration(collaboration_id: str):
    return MOCK_COLLABORATIONS[0]


@router.post("/collaborations", response_model=CollaborationResponse)
async def create_collaboration(request: dict):
    return CollaborationResponse(
        id=f"collab-{uuid4().hex[:8]}",
        name=request.get("name", "New Project"),
        description=request.get("description", ""),
        status="planning",
        created_at=datetime.now(),
    )


@router.post("/collaborations/{collaboration_id}/invite")
async def invite_collaborator(collaboration_id: str, request: dict):
    return {"success": True, "email": request.get("email")}


@router.post("/collaborations/{collaboration_id}/messages", response_model=MessageResponse)
async def send_collaboration_message(collaboration_id: str, request: dict):
    return MessageResponse(
        id=f"msg-{uuid4().hex[:8]}",
        sender_id="current-user",
        content=request.get("content", ""),
        sent_at=datetime.now(),
    )


@router.get("/collaborations/{collaboration_id}/analytics")
async def get_collaboration_analytics(collaboration_id: str):
    return {
        "collaboration_id": collaboration_id,
        "combined_reach": 125000,
        "combined_engagement": 8500,
        "revenue_total_cents": 250000,
        "content_count": 12,
        "top_performing": [
            {"platform": "instagram", "engagement": 4200},
            {"platform": "tiktok", "engagement": 3100},
        ],
    }


# ==================== Revenue Sharing ====================

class RevenueAgreementResponse(BaseModel):
    id: str
    partner_name: str
    partner_avatar: str
    split_percentage: int
    total_earned_cents: int
    total_paid_cents: int
    status: str = "active"
    created_at: datetime


MOCK_REVENUE_AGREEMENTS = [
    RevenueAgreementResponse(
        id="rev-1",
        partner_name="Alex Music",
        partner_avatar="/avatars/2.jpg",
        split_percentage=30,
        total_earned_cents=450000,
        total_paid_cents=135000,
        status="active",
        created_at=datetime.now() - timedelta(days=60),
    ),
]


@router.get("/revenue-sharing", response_model=List[RevenueAgreementResponse])
async def list_revenue_agreements():
    return MOCK_REVENUE_AGREEMENTS


@router.post("/revenue-sharing", response_model=RevenueAgreementResponse)
async def create_revenue_agreement(request: dict):
    return RevenueAgreementResponse(
        id=f"rev-{uuid4().hex[:8]}",
        partner_name=request.get("partner_email", "Partner"),
        partner_avatar="/avatars/default.jpg",
        split_percentage=request.get("split_percentage", 50),
        total_earned_cents=0,
        total_paid_cents=0,
        status="active",
        created_at=datetime.now(),
    )


@router.post("/revenue-sharing/{agreement_id}/payout")
async def process_revenue_payout(agreement_id: str):
    return {
        "payout_id": f"payout-{uuid4().hex[:8]}",
        "amount_cents": 15000,
        "status": "processing",
    }


# ==================== Social Listening ====================

class SentimentBreakdown(BaseModel):
    positive: int
    neutral: int
    negative: int


class ListeningQueryResponse(BaseModel):
    id: str
    name: str
    keywords: List[str]
    platforms: List[str]
    status: str = "active"
    mentions_count: int
    sentiment_breakdown: SentimentBreakdown
    created_at: datetime


class MentionResponse(BaseModel):
    id: str
    platform: str
    author_name: str
    author_avatar: str
    content: str
    sentiment: str
    engagement: int
    posted_at: datetime
    url: str


MOCK_LISTENING_QUERIES = [
    ListeningQueryResponse(
        id="query-1",
        name="Brand Mentions",
        keywords=["@myhandle", "mybrand"],
        platforms=["twitter", "instagram"],
        status="active",
        mentions_count=156,
        sentiment_breakdown=SentimentBreakdown(positive=89, neutral=52, negative=15),
        created_at=datetime.now() - timedelta(days=14),
    ),
]


@router.get("/listening/queries", response_model=List[ListeningQueryResponse])
async def list_listening_queries():
    return MOCK_LISTENING_QUERIES


@router.post("/listening/queries", response_model=ListeningQueryResponse)
async def create_listening_query(request: dict):
    return ListeningQueryResponse(
        id=f"query-{uuid4().hex[:8]}",
        name=request.get("name", "New Query"),
        keywords=request.get("keywords", []),
        platforms=request.get("platforms", []),
        status="active",
        mentions_count=0,
        sentiment_breakdown=SentimentBreakdown(positive=0, neutral=0, negative=0),
        created_at=datetime.now(),
    )


@router.get("/listening/queries/{query_id}/mentions", response_model=List[MentionResponse])
async def get_listening_mentions(query_id: str, sentiment: Optional[str] = None, platform: Optional[str] = None):
    mentions = [
        MentionResponse(
            id="mention-1",
            platform="twitter",
            author_name="@fan123",
            author_avatar="/avatars/fan.jpg",
            content="Love the new content from @myhandle! 🔥",
            sentiment="positive",
            engagement=245,
            posted_at=datetime.now() - timedelta(hours=3),
            url="https://twitter.com/fan123/status/123456",
        ),
    ]
    if sentiment:
        mentions = [m for m in mentions if m.sentiment == sentiment]
    if platform:
        mentions = [m for m in mentions if m.platform == platform]
    return mentions


# ==================== Custom Reports ====================

class ReportResponse(BaseModel):
    id: str
    name: str
    description: str
    metrics: List[str]
    platforms: List[str]
    schedule: Optional[dict] = None
    last_generated_at: Optional[datetime] = None
    created_at: datetime


MOCK_REPORTS = [
    ReportResponse(
        id="report-1",
        name="Weekly Performance",
        description="Weekly engagement and growth metrics",
        metrics=["impressions", "engagement", "followers"],
        platforms=["instagram", "tiktok", "youtube"],
        schedule={"frequency": "weekly", "next_run": (datetime.now() + timedelta(days=3)).isoformat()},
        last_generated_at=datetime.now() - timedelta(days=4),
        created_at=datetime.now() - timedelta(days=30),
    ),
]


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports():
    return MOCK_REPORTS


@router.post("/reports", response_model=ReportResponse)
async def create_report(request: dict):
    return ReportResponse(
        id=f"report-{uuid4().hex[:8]}",
        name=request.get("name", "New Report"),
        description=request.get("description", ""),
        metrics=request.get("metrics", []),
        platforms=request.get("platforms", []),
        created_at=datetime.now(),
    )


@router.post("/reports/{report_id}/generate")
async def generate_report(report_id: str):
    return {
        "report_id": report_id,
        "generated_at": datetime.now().isoformat(),
        "data": {"impressions": 125000, "engagement": 8500, "followers": 45200},
        "download_url": f"/api/v1/reports/{report_id}/download",
    }


@router.put("/reports/{report_id}/schedule", response_model=ReportResponse)
async def schedule_report(report_id: str, request: dict):
    report = MOCK_REPORTS[0].model_copy()
    report.schedule = request
    return report


# ==================== Tax Documentation ====================

class TaxInfoResponse(BaseModel):
    business_type: str = "individual"
    tax_id: str = "***-**-1234"
    legal_name: str = "John Creator"
    address: dict = Field(default_factory=lambda: {
        "street": "123 Creator Lane",
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90001",
        "country": "US",
    })
    w9_submitted: bool = True


class TaxDocumentResponse(BaseModel):
    id: str
    type: str
    year: int
    status: str = "available"
    download_url: Optional[str] = None
    created_at: datetime


MOCK_TAX_DOCUMENTS = [
    TaxDocumentResponse(
        id="tax-doc-1",
        type="1099",
        year=2025,
        status="available",
        download_url="/api/v1/tax/documents/tax-doc-1/download",
        created_at=datetime.now() - timedelta(days=30),
    ),
]


@router.get("/tax", response_model=TaxInfoResponse)
async def get_tax_info():
    return TaxInfoResponse()


@router.put("/tax", response_model=TaxInfoResponse)
async def update_tax_info(request: dict):
    return TaxInfoResponse(**request)


@router.get("/tax/documents", response_model=List[TaxDocumentResponse])
async def list_tax_documents(year: Optional[int] = None):
    docs = MOCK_TAX_DOCUMENTS
    if year:
        docs = [d for d in docs if d.year == year]
    return docs


@router.get("/tax/documents/{document_id}/download")
async def download_tax_document(document_id: str):
    return {"download_url": f"https://storage.example.com/tax/{document_id}.pdf"}


# ==================== Compliance Reporting ====================

class ComplianceFinding(BaseModel):
    category: str
    status: str
    message: str


class ComplianceReportResponse(BaseModel):
    id: str
    type: str
    status: str
    generated_at: datetime
    findings: List[ComplianceFinding] = []


class ComplianceCheckResponse(BaseModel):
    id: str
    name: str
    category: str
    last_checked: datetime
    status: str


MOCK_COMPLIANCE_REPORTS = [
    ComplianceReportResponse(
        id="compliance-1",
        type="gdpr",
        status="passed",
        generated_at=datetime.now() - timedelta(days=1),
        findings=[
            ComplianceFinding(category="Data Retention", status="passed", message="All data retention policies met"),
            ComplianceFinding(category="Consent Management", status="passed", message="Valid consent records found"),
        ],
    ),
]


@router.get("/admin/compliance", response_model=List[ComplianceReportResponse])
async def list_compliance_reports():
    return MOCK_COMPLIANCE_REPORTS


@router.post("/admin/compliance/generate", response_model=ComplianceReportResponse)
async def generate_compliance_report(request: dict):
    return ComplianceReportResponse(
        id=f"compliance-{uuid4().hex[:8]}",
        type=request.get("type", "gdpr"),
        status="passed",
        generated_at=datetime.now(),
        findings=[],
    )


@router.get("/admin/compliance/checks", response_model=List[ComplianceCheckResponse])
async def list_compliance_checks():
    return [
        ComplianceCheckResponse(
            id="check-1",
            name="GDPR Data Export",
            category="Privacy",
            last_checked=datetime.now() - timedelta(hours=6),
            status="passed",
        ),
        ComplianceCheckResponse(
            id="check-2",
            name="Content Moderation",
            category="Safety",
            last_checked=datetime.now() - timedelta(hours=2),
            status="passed",
        ),
    ]


# ==================== Backup Management ====================

class BackupResponse(BaseModel):
    id: str
    type: str = "full"
    size_bytes: int
    status: str = "completed"
    created_at: datetime
    completed_at: Optional[datetime] = None


class BackupScheduleResponse(BaseModel):
    id: str
    name: str
    frequency: str
    next_run: datetime
    last_run: Optional[datetime] = None
    enabled: bool = True


MOCK_BACKUPS = [
    BackupResponse(
        id="backup-1",
        type="full",
        size_bytes=1024 * 1024 * 500,  # 500MB
        status="completed",
        created_at=datetime.now() - timedelta(days=1),
        completed_at=datetime.now() - timedelta(days=1) + timedelta(minutes=15),
    ),
]


@router.get("/admin/backups", response_model=List[BackupResponse])
async def list_backups():
    return MOCK_BACKUPS


@router.post("/admin/backups", response_model=BackupResponse)
async def create_backup(request: dict = None):
    return BackupResponse(
        id=f"backup-{uuid4().hex[:8]}",
        type=request.get("type", "full") if request else "full",
        size_bytes=0,
        status="in_progress",
        created_at=datetime.now(),
    )


@router.post("/admin/backups/{backup_id}/restore")
async def restore_backup(backup_id: str):
    return {"job_id": f"restore-{uuid4().hex[:8]}"}


@router.get("/admin/backups/schedules", response_model=List[BackupScheduleResponse])
async def list_backup_schedules():
    return [
        BackupScheduleResponse(
            id="schedule-1",
            name="Daily Backup",
            frequency="daily",
            next_run=datetime.now() + timedelta(hours=6),
            last_run=datetime.now() - timedelta(days=1),
            enabled=True,
        ),
    ]


@router.patch("/admin/backups/schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def toggle_backup_schedule(schedule_id: str, request: dict):
    return BackupScheduleResponse(
        id=schedule_id,
        name="Daily Backup",
        frequency="daily",
        next_run=datetime.now() + timedelta(hours=6),
        enabled=request.get("enabled", True),
    )


# ==================== Sponsorship Management ====================

class SponsorshipDeliverableResponse(BaseModel):
    id: str
    type: str
    platform: str
    description: str
    due_date: datetime
    status: str = "pending"


class SponsorshipResponse(BaseModel):
    id: str
    brand_name: str
    brand_logo: str
    status: str = "active"
    value_cents: int
    start_date: datetime
    end_date: datetime
    deliverables: List[SponsorshipDeliverableResponse] = []


MOCK_SPONSORSHIPS = [
    SponsorshipResponse(
        id="sponsor-1",
        brand_name="Adidas",
        brand_logo="/logos/adidas.png",
        status="active",
        value_cents=750000,
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now() + timedelta(days=45),
        deliverables=[
            SponsorshipDeliverableResponse(
                id="sd1",
                type="video",
                platform="youtube",
                description="Product review video (5+ min)",
                due_date=datetime.now() + timedelta(days=7),
                status="pending",
            ),
        ],
    ),
]


@router.get("/sponsorships", response_model=List[SponsorshipResponse])
async def list_sponsorships():
    return MOCK_SPONSORSHIPS


@router.get("/sponsorships/{sponsorship_id}", response_model=SponsorshipResponse)
async def get_sponsorship(sponsorship_id: str):
    return MOCK_SPONSORSHIPS[0]


@router.post("/sponsorships", response_model=SponsorshipResponse)
async def create_sponsorship(request: dict):
    return SponsorshipResponse(
        id=f"sponsor-{uuid4().hex[:8]}",
        brand_name=request.get("brand_name", "New Brand"),
        brand_logo="/logos/default.png",
        status="negotiating",
        value_cents=request.get("value_cents", 0),
        start_date=datetime.fromisoformat(request.get("start_date", datetime.now().isoformat())),
        end_date=datetime.fromisoformat(request.get("end_date", (datetime.now() + timedelta(days=30)).isoformat())),
    )


@router.patch("/sponsorships/{sponsorship_id}/deliverables/{deliverable_id}")
async def update_sponsorship_deliverable(sponsorship_id: str, deliverable_id: str, request: dict):
    return SponsorshipDeliverableResponse(
        id=deliverable_id,
        type="video",
        platform="youtube",
        description="Product review video",
        due_date=datetime.now() + timedelta(days=7),
        status=request.get("status", "pending"),
    )


# ==================== Offline Mode ====================

@router.get("/offline/status")
async def get_offline_status():
    return {
        "last_synced_at": datetime.now().isoformat(),
        "pending_actions": 0,
        "cached_items": 156,
        "storage_used_bytes": 1024 * 1024 * 25,  # 25MB
    }


@router.post("/offline/sync")
async def sync_offline_data():
    return {"synced_count": 0}


@router.delete("/offline/cache")
async def clear_offline_cache():
    return {"success": True}
