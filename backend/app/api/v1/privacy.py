"""
Privacy & GDPR API

Endpoints for data portability, deletion, and privacy settings.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.gdpr import gdpr_service
from app.services.gdpr.models import (
    DataCategory,
    DataRequestStatus,
    DataRequestType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class DataRequestCreate(BaseModel):
    """Request to create a data export or deletion."""

    request_type: DataRequestType
    categories: Optional[list[DataCategory]] = None
    reason: Optional[str] = Field(None, max_length=500)


class DataRequestResponse(BaseModel):
    """Data request response."""

    id: UUID
    request_type: str
    status: str
    categories: list[str]
    created_at: str
    completed_at: Optional[str]
    download_url: Optional[str]
    expires_at: Optional[str]


class PrivacySettingsRequest(BaseModel):
    """Privacy settings update request."""

    profile_visibility: Optional[str] = Field(
        None, regex="^(public|followers|private)$"
    )
    activity_visibility: Optional[str] = Field(
        None, regex="^(public|followers|private)$"
    )
    search_visibility: Optional[bool] = None
    analytics_enabled: Optional[bool] = None
    personalization_enabled: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    product_updates: Optional[bool] = None
    third_party_sharing: Optional[bool] = None


class PrivacySettingsResponse(BaseModel):
    """Privacy settings response."""

    profile_visibility: str
    activity_visibility: str
    search_visibility: bool
    analytics_enabled: bool
    personalization_enabled: bool
    marketing_emails: bool
    product_updates: bool
    third_party_sharing: bool


class ConsentRequest(BaseModel):
    """Consent update request."""

    consent_type: str
    granted: bool


class ConsentResponse(BaseModel):
    """Consent record response."""

    id: UUID
    consent_type: str
    granted: bool
    recorded_at: str


class DeletionResultResponse(BaseModel):
    """Data deletion result."""

    deleted_at: str
    categories_deleted: list[str]
    items_deleted: dict[str, int]
    retained_items: dict[str, int]
    retention_reasons: list[str]


# =============================================================================
# Data Export Endpoints
# =============================================================================


@router.post("/data-requests", response_model=DataRequestResponse)
async def create_data_request(
    request: DataRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a data export or deletion request.

    - **export**: Request a copy of all your data (Article 20)
    - **delete**: Request deletion of your data (Article 17)
    - **access**: Request access to your data (Article 15)

    Processing may take up to 30 days as per GDPR requirements.
    """
    data_request = await gdpr_service.create_data_request(
        db=db,
        user_id=current_user.id,
        request_type=request.request_type,
        categories=request.categories,
        reason=request.reason,
    )

    # Process export requests in background
    if request.request_type == DataRequestType.EXPORT:
        background_tasks.add_task(
            process_export_request,
            str(data_request.id),
            str(current_user.id),
            [c.value for c in (request.categories or list(DataCategory))],
        )

    return DataRequestResponse(
        id=data_request.id,
        request_type=data_request.request_type.value,
        status=data_request.status.value,
        categories=[c.value for c in data_request.categories],
        created_at=data_request.created_at.isoformat(),
        completed_at=None,
        download_url=None,
        expires_at=data_request.expires_at.isoformat() if data_request.expires_at else None,
    )


@router.get("/data-requests", response_model=list[DataRequestResponse])
async def list_data_requests(
    status: Optional[DataRequestStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all your data requests."""
    requests = await gdpr_service.list_data_requests(
        db=db,
        user_id=current_user.id,
        status=status,
    )

    return [
        DataRequestResponse(
            id=r.id,
            request_type=r.request_type.value,
            status=r.status.value,
            categories=[c.value for c in r.categories],
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            download_url=r.download_url,
            expires_at=None,
        )
        for r in requests
    ]


@router.get("/data-requests/{request_id}", response_model=DataRequestResponse)
async def get_data_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific data request."""
    data_request = await gdpr_service.get_data_request(
        db=db,
        request_id=request_id,
        user_id=current_user.id,
    )

    if not data_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data request not found",
        )

    return DataRequestResponse(
        id=data_request.id,
        request_type=data_request.request_type.value,
        status=data_request.status.value,
        categories=[c.value for c in data_request.categories],
        created_at=data_request.created_at.isoformat(),
        completed_at=(
            data_request.completed_at.isoformat() if data_request.completed_at else None
        ),
        download_url=data_request.download_url,
        expires_at=(
            data_request.expires_at.isoformat() if data_request.expires_at else None
        ),
    )


@router.get("/export")
async def download_data_export(
    categories: Optional[str] = Query(
        None, description="Comma-separated categories to export"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download your data export immediately.

    This generates an export on-the-fly. For large accounts,
    use the async data request endpoint instead.
    """
    category_list = None
    if categories:
        try:
            category_list = [
                DataCategory(c.strip()) for c in categories.split(",") if c.strip()
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {e}",
            )

    file_bytes, filename = await gdpr_service.generate_export_file(
        db=db,
        user_id=current_user.id,
        categories=category_list,
    )

    return StreamingResponse(
        iter([file_bytes]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_bytes)),
        },
    )


# =============================================================================
# Data Deletion Endpoints
# =============================================================================


@router.delete("/data")
async def delete_my_data(
    categories: Optional[str] = Query(
        None, description="Comma-separated categories to delete (default: all)"
    ),
    confirm: bool = Query(
        ..., description="Must be true to confirm deletion"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete your personal data (Right to Erasure).

    Some data may be retained for legal compliance (e.g., payment records).
    Account will be deactivated after deletion.

    **WARNING: This action is irreversible!**
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion by setting confirm=true",
        )

    category_list = None
    if categories:
        try:
            category_list = [
                DataCategory(c.strip()) for c in categories.split(",") if c.strip()
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {e}",
            )

    result = await gdpr_service.delete_user_data(
        db=db,
        user_id=current_user.id,
        categories=category_list,
    )

    logger.info(f"User {current_user.id} deleted their data: {result.items_deleted}")

    return DeletionResultResponse(
        deleted_at=result.deleted_at.isoformat(),
        categories_deleted=[c.value for c in result.categories_deleted],
        items_deleted=result.items_deleted,
        retained_items=result.retained_items,
        retention_reasons=result.retention_reasons,
    )


@router.delete("/account")
async def delete_account(
    confirm: bool = Query(..., description="Must be true to confirm"),
    confirmation_text: str = Query(
        ..., description="Type 'DELETE MY ACCOUNT' to confirm"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete your account and all associated data.

    This will:
    1. Delete all your content, media, and interactions
    2. Remove your AI twins and generated content
    3. Disconnect all social accounts
    4. Anonymize your profile
    5. Retain only legally required records

    **WARNING: This action is irreversible!**
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm account deletion",
        )

    # Verify confirmation text (since we use OAuth, no password to verify)
    if confirmation_text != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please type 'DELETE MY ACCOUNT' to confirm deletion",
        )

    # Delete all data
    result = await gdpr_service.delete_user_data(
        db=db,
        user_id=current_user.id,
        categories=None,  # All categories
    )

    logger.warning(f"Account deleted: {current_user.id}")

    return {
        "message": "Account successfully deleted",
        "deleted_at": result.deleted_at.isoformat(),
        "items_deleted": result.items_deleted,
        "retained_for_legal": result.retained_items,
    }


# =============================================================================
# Privacy Settings Endpoints
# =============================================================================


@router.get("/settings", response_model=PrivacySettingsResponse)
async def get_privacy_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get your privacy settings."""
    settings = await gdpr_service.get_privacy_settings(
        db=db,
        user_id=current_user.id,
    )

    return PrivacySettingsResponse(
        profile_visibility=settings.profile_visibility,
        activity_visibility=settings.activity_visibility,
        search_visibility=settings.search_visibility,
        analytics_enabled=settings.analytics_enabled,
        personalization_enabled=settings.personalization_enabled,
        marketing_emails=settings.marketing_emails,
        product_updates=settings.product_updates,
        third_party_sharing=settings.third_party_sharing,
    )


@router.put("/settings", response_model=PrivacySettingsResponse)
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update your privacy settings."""
    current_settings = await gdpr_service.get_privacy_settings(
        db=db,
        user_id=current_user.id,
    )

    # Update only provided fields
    if request.profile_visibility is not None:
        current_settings.profile_visibility = request.profile_visibility
    if request.activity_visibility is not None:
        current_settings.activity_visibility = request.activity_visibility
    if request.search_visibility is not None:
        current_settings.search_visibility = request.search_visibility
    if request.analytics_enabled is not None:
        current_settings.analytics_enabled = request.analytics_enabled
    if request.personalization_enabled is not None:
        current_settings.personalization_enabled = request.personalization_enabled
    if request.marketing_emails is not None:
        current_settings.marketing_emails = request.marketing_emails
    if request.product_updates is not None:
        current_settings.product_updates = request.product_updates
    if request.third_party_sharing is not None:
        current_settings.third_party_sharing = request.third_party_sharing

    updated = await gdpr_service.update_privacy_settings(
        db=db,
        user_id=current_user.id,
        settings=current_settings,
    )

    return PrivacySettingsResponse(
        profile_visibility=updated.profile_visibility,
        activity_visibility=updated.activity_visibility,
        search_visibility=updated.search_visibility,
        analytics_enabled=updated.analytics_enabled,
        personalization_enabled=updated.personalization_enabled,
        marketing_emails=updated.marketing_emails,
        product_updates=updated.product_updates,
        third_party_sharing=updated.third_party_sharing,
    )


# =============================================================================
# Consent Management Endpoints
# =============================================================================


@router.post("/consent", response_model=ConsentResponse)
async def update_consent(
    request: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update your consent preferences.

    Consent types:
    - **marketing**: Marketing communications
    - **analytics**: Usage analytics
    - **personalization**: Personalized recommendations
    - **third_party**: Third-party data sharing
    """
    from fastapi import Request

    consent = await gdpr_service.record_consent(
        db=db,
        user_id=current_user.id,
        consent_type=request.consent_type,
        granted=request.granted,
    )

    return ConsentResponse(
        id=consent.id,
        consent_type=consent.consent_type,
        granted=consent.granted,
        recorded_at=(
            consent.granted_at.isoformat()
            if consent.granted_at
            else consent.revoked_at.isoformat()
        ),
    )


# =============================================================================
# Privacy Information Endpoints
# =============================================================================


@router.get("/data-categories")
async def list_data_categories():
    """List available data categories for export/deletion."""
    return {
        "categories": [
            {
                "id": category.value,
                "name": category.name.replace("_", " ").title(),
                "description": _get_category_description(category),
            }
            for category in DataCategory
        ]
    }


@router.get("/rights")
async def get_gdpr_rights():
    """
    Get information about your GDPR rights.

    Returns a summary of your data protection rights under GDPR.
    """
    return {
        "rights": [
            {
                "article": "15",
                "name": "Right of Access",
                "description": "You can request access to your personal data.",
                "endpoint": "/api/v1/privacy/export",
            },
            {
                "article": "16",
                "name": "Right to Rectification",
                "description": "You can update incorrect personal data.",
                "endpoint": "/api/v1/profiles/me",
            },
            {
                "article": "17",
                "name": "Right to Erasure",
                "description": "You can request deletion of your personal data.",
                "endpoint": "/api/v1/privacy/data",
            },
            {
                "article": "18",
                "name": "Right to Restrict Processing",
                "description": "You can restrict how we process your data.",
                "endpoint": "/api/v1/privacy/settings",
            },
            {
                "article": "20",
                "name": "Right to Data Portability",
                "description": "You can download your data in a portable format.",
                "endpoint": "/api/v1/privacy/export",
            },
            {
                "article": "21",
                "name": "Right to Object",
                "description": "You can object to certain processing activities.",
                "endpoint": "/api/v1/privacy/consent",
            },
        ],
        "contact": {
            "email": "privacy@idkit.com",
            "dpo": "dpo@idkit.com",
        },
        "response_time": "30 days",
    }


def _get_category_description(category: DataCategory) -> str:
    """Get human-readable description for a data category."""
    descriptions = {
        DataCategory.PROFILE: "Your profile information (name, bio, avatar)",
        DataCategory.CONTENT: "Your posts, comments, and other content",
        DataCategory.MEDIA: "Uploaded images, videos, and audio files",
        DataCategory.INTERACTIONS: "Likes, saves, follows, and other interactions",
        DataCategory.MESSAGES: "Direct messages and conversations",
        DataCategory.ANALYTICS: "Usage analytics and activity logs",
        DataCategory.PAYMENTS: "Payment history and subscription data",
        DataCategory.SETTINGS: "Preferences and notification settings",
        DataCategory.AI_DATA: "AI twin configurations and generated content",
        DataCategory.SOCIAL: "Connected social media accounts",
    }
    return descriptions.get(category, "")


# =============================================================================
# Background Task for Export Processing
# =============================================================================


async def process_export_request(
    request_id: str,
    user_id: str,
    categories: list[str],
):
    """Background task to process data export request."""
    from uuid import UUID

    from app.dependencies import get_db_session

    try:
        async with get_db_session() as db:
            from app.models.user import DataRequest

            # Update status to processing
            await db.execute(
                DataRequest.__table__.update()
                .where(DataRequest.id == UUID(request_id))
                .values(status=DataRequestStatus.PROCESSING.value)
            )
            await db.commit()

            # Generate export
            category_list = [DataCategory(c) for c in categories]
            file_bytes, filename = await gdpr_service.generate_export_file(
                db=db,
                user_id=UUID(user_id),
                categories=category_list,
            )

            # Upload to S3 and get URL
            from app.utils.storage import upload_file

            download_url = await upload_file(
                file_bytes,
                filename,
                content_type="application/zip",
                expires_in=86400 * 30,  # 30 days
            )

            # Update request with download URL
            from datetime import datetime

            await db.execute(
                DataRequest.__table__.update()
                .where(DataRequest.id == UUID(request_id))
                .values(
                    status=DataRequestStatus.COMPLETED.value,
                    download_url=download_url,
                    completed_at=datetime.utcnow(),
                )
            )
            await db.commit()

            logger.info(f"Export completed for request {request_id}")

    except Exception as e:
        logger.error(f"Export failed for request {request_id}: {e}")
        try:
            async with get_db_session() as db:
                from app.models.user import DataRequest

                await db.execute(
                    DataRequest.__table__.update()
                    .where(DataRequest.id == UUID(request_id))
                    .values(
                        status=DataRequestStatus.FAILED.value,
                        error_message=str(e),
                    )
                )
                await db.commit()
        except Exception:
            pass
