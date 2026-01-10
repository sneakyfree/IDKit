"""
GDPR Service Implementation

Handles data export, deletion, and privacy compliance operations.
"""

import hashlib
import io
import json
import logging
import zipfile
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gdpr.models import (
    ConsentRecord,
    DataCategory,
    DataRequest,
    DataRequestStatus,
    DataRequestType,
    DeletionResult,
    ExportedData,
    PrivacySettings,
)

logger = logging.getLogger(__name__)


class GDPRService:
    """
    GDPR compliance service.

    Implements:
    - Right of Access (Article 15)
    - Right to Rectification (Article 16)
    - Right to Erasure (Article 17)
    - Right to Restrict Processing (Article 18)
    - Right to Data Portability (Article 20)
    - Right to Object (Article 21)
    """

    # Data retention periods (days) by category
    RETENTION_PERIODS = {
        DataCategory.PROFILE: 0,  # Delete immediately when requested
        DataCategory.CONTENT: 0,
        DataCategory.MEDIA: 0,
        DataCategory.INTERACTIONS: 0,
        DataCategory.MESSAGES: 0,
        DataCategory.ANALYTICS: 90,  # Keep for 90 days for legal compliance
        DataCategory.PAYMENTS: 2555,  # 7 years for financial records
        DataCategory.SETTINGS: 0,
        DataCategory.AI_DATA: 0,
        DataCategory.SOCIAL: 0,
    }

    # Categories that require legal retention
    LEGAL_RETENTION_CATEGORIES = {
        DataCategory.PAYMENTS,
        DataCategory.ANALYTICS,
    }

    async def create_data_request(
        self,
        db: AsyncSession,
        user_id: UUID,
        request_type: DataRequestType,
        categories: Optional[list[DataCategory]] = None,
        reason: Optional[str] = None,
    ) -> DataRequest:
        """Create a new data request (export/delete/access)."""
        from app.models.user import DataRequest as DataRequestModel

        # Default to all categories if not specified
        if categories is None:
            categories = list(DataCategory)

        request_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(days=30)  # 30-day expiry

        request = DataRequestModel(
            id=request_id,
            user_id=user_id,
            request_type=request_type.value,
            status=DataRequestStatus.PENDING.value,
            categories=[c.value for c in categories],
            reason=reason,
            expires_at=expires_at,
        )

        db.add(request)
        await db.commit()

        logger.info(
            f"Created {request_type.value} request {request_id} for user {user_id}"
        )

        return DataRequest(
            id=request_id,
            user_id=user_id,
            request_type=request_type,
            status=DataRequestStatus.PENDING,
            categories=categories,
            reason=reason,
            expires_at=expires_at,
        )

    async def get_data_request(
        self,
        db: AsyncSession,
        request_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[DataRequest]:
        """Get a data request by ID."""
        from app.models.user import DataRequest as DataRequestModel

        query = select(DataRequestModel).where(DataRequestModel.id == request_id)
        if user_id:
            query = query.where(DataRequestModel.user_id == user_id)

        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return DataRequest(
            id=record.id,
            user_id=record.user_id,
            request_type=DataRequestType(record.request_type),
            status=DataRequestStatus(record.status),
            categories=[DataCategory(c) for c in (record.categories or [])],
            reason=record.reason,
            created_at=record.created_at,
            processed_at=record.processed_at,
            completed_at=record.completed_at,
            expires_at=record.expires_at,
            download_url=record.download_url,
            error_message=record.error_message,
        )

    async def list_data_requests(
        self,
        db: AsyncSession,
        user_id: UUID,
        status: Optional[DataRequestStatus] = None,
    ) -> list[DataRequest]:
        """List all data requests for a user."""
        from app.models.user import DataRequest as DataRequestModel

        query = select(DataRequestModel).where(DataRequestModel.user_id == user_id)
        if status:
            query = query.where(DataRequestModel.status == status.value)
        query = query.order_by(DataRequestModel.created_at.desc())

        result = await db.execute(query)
        records = result.scalars().all()

        return [
            DataRequest(
                id=r.id,
                user_id=r.user_id,
                request_type=DataRequestType(r.request_type),
                status=DataRequestStatus(r.status),
                categories=[DataCategory(c) for c in (r.categories or [])],
                reason=r.reason,
                created_at=r.created_at,
                completed_at=r.completed_at,
                download_url=r.download_url,
            )
            for r in records
        ]

    async def export_user_data(
        self,
        db: AsyncSession,
        user_id: UUID,
        categories: Optional[list[DataCategory]] = None,
    ) -> ExportedData:
        """
        Export all user data (Article 20 - Right to Data Portability).

        Returns structured data in a portable format.
        """
        if categories is None:
            categories = list(DataCategory)

        data: dict[str, Any] = {}

        for category in categories:
            try:
                category_data = await self._export_category(db, user_id, category)
                if category_data:
                    data[category.value] = category_data
            except Exception as e:
                logger.error(f"Error exporting {category.value} for {user_id}: {e}")
                data[category.value] = {"error": str(e)}

        # Calculate checksum for integrity
        data_json = json.dumps(data, default=str, sort_keys=True)
        checksum = hashlib.sha256(data_json.encode()).hexdigest()

        return ExportedData(
            user_id=user_id,
            export_date=datetime.utcnow(),
            categories=categories,
            data=data,
            checksum=checksum,
        )

    async def _export_category(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: DataCategory,
    ) -> dict[str, Any]:
        """Export data for a specific category."""
        exporters = {
            DataCategory.PROFILE: self._export_profile,
            DataCategory.CONTENT: self._export_content,
            DataCategory.MEDIA: self._export_media,
            DataCategory.INTERACTIONS: self._export_interactions,
            DataCategory.MESSAGES: self._export_messages,
            DataCategory.ANALYTICS: self._export_analytics,
            DataCategory.PAYMENTS: self._export_payments,
            DataCategory.SETTINGS: self._export_settings,
            DataCategory.AI_DATA: self._export_ai_data,
            DataCategory.SOCIAL: self._export_social,
        }

        exporter = exporters.get(category)
        if exporter:
            return await exporter(db, user_id)
        return {}

    async def _export_profile(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user profile data."""
        from app.models.user import User, UserProfile

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        data = {
            "account": {
                "email": user.email if user else None,
                "created_at": str(user.created_at) if user else None,
                "last_login": str(user.last_login) if user and user.last_login else None,
            }
        }

        if profile:
            data["profile"] = {
                "username": profile.username,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "website_url": profile.website_url,
                "avatar_url": profile.avatar_url,
                "cover_image_url": profile.cover_image_url,
                "is_verified": profile.is_verified,
            }

        return data

    async def _export_content(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user-generated content."""
        from app.models.feed import FeedPost, FeedComment

        # Posts
        posts_result = await db.execute(
            select(FeedPost).where(FeedPost.user_id == user_id)
        )
        posts = posts_result.scalars().all()

        # Comments
        comments_result = await db.execute(
            select(FeedComment).where(FeedComment.user_id == user_id)
        )
        comments = comments_result.scalars().all()

        return {
            "posts": [
                {
                    "id": str(p.id),
                    "content_text": p.content_text,
                    "post_type": p.post_type,
                    "created_at": str(p.created_at),
                    "hashtags": p.hashtags,
                }
                for p in posts
            ],
            "comments": [
                {
                    "id": str(c.id),
                    "content": c.content,
                    "post_id": str(c.post_id),
                    "created_at": str(c.created_at),
                }
                for c in comments
            ],
        }

    async def _export_media(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user media files metadata."""
        from app.models.media import MediaUpload

        result = await db.execute(
            select(MediaUpload).where(MediaUpload.user_id == user_id)
        )
        media = result.scalars().all()

        return {
            "media_files": [
                {
                    "id": str(m.id),
                    "filename": m.filename,
                    "file_type": m.file_type,
                    "file_size": m.file_size,
                    "url": m.url,
                    "uploaded_at": str(m.created_at),
                }
                for m in media
            ]
        }

    async def _export_interactions(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user interactions (likes, follows, etc.)."""
        from app.models.feed import FeedLike, FeedSave
        from app.models.social import Follow

        likes_result = await db.execute(
            select(FeedLike).where(FeedLike.user_id == user_id)
        )
        likes = likes_result.scalars().all()

        saves_result = await db.execute(
            select(FeedSave).where(FeedSave.user_id == user_id)
        )
        saves = saves_result.scalars().all()

        follows_result = await db.execute(
            select(Follow).where(Follow.follower_id == user_id)
        )
        follows = follows_result.scalars().all()

        return {
            "likes": [{"post_id": str(l.post_id), "created_at": str(l.created_at)} for l in likes],
            "saves": [{"post_id": str(s.post_id), "collection": s.collection_name} for s in saves],
            "following": [{"user_id": str(f.following_id), "since": str(f.created_at)} for f in follows],
        }

    async def _export_messages(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user messages and conversations."""
        # Placeholder - implement based on your messaging model
        return {"conversations": [], "messages": []}

    async def _export_analytics(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user analytics data."""
        # Limited export for analytics - aggregate data only
        return {"note": "Analytics data is aggregated and anonymized."}

    async def _export_payments(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export payment history."""
        from app.models.payment import Payment, Subscription

        payments_result = await db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        payments = payments_result.scalars().all()

        subs_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscriptions = subs_result.scalars().all()

        return {
            "payments": [
                {
                    "id": str(p.id),
                    "amount": p.amount,
                    "currency": p.currency,
                    "status": p.status,
                    "created_at": str(p.created_at),
                }
                for p in payments
            ],
            "subscriptions": [
                {
                    "id": str(s.id),
                    "plan": s.plan_id,
                    "status": s.status,
                    "start_date": str(s.start_date),
                }
                for s in subscriptions
            ],
        }

    async def _export_settings(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export user settings and preferences."""
        from app.models.user import UserSettings

        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if settings:
            return {
                "notification_preferences": settings.notification_preferences,
                "privacy_settings": settings.privacy_settings,
                "theme": settings.theme,
                "language": settings.language,
            }
        return {}

    async def _export_ai_data(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export AI twin data."""
        from app.models.twin import AITwin

        result = await db.execute(select(AITwin).where(AITwin.user_id == user_id))
        twins = result.scalars().all()

        return {
            "ai_twins": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "status": t.status,
                    "created_at": str(t.created_at),
                    "avatar_trained": t.avatar_trained,
                    "voice_trained": t.voice_trained,
                }
                for t in twins
            ]
        }

    async def _export_social(
        self, db: AsyncSession, user_id: UUID
    ) -> dict[str, Any]:
        """Export connected social accounts (metadata only, not tokens)."""
        from app.models.social import SocialAccount

        result = await db.execute(
            select(SocialAccount).where(SocialAccount.user_id == user_id)
        )
        accounts = result.scalars().all()

        return {
            "connected_accounts": [
                {
                    "platform": a.platform,
                    "platform_username": a.platform_username,
                    "connected_at": str(a.created_at),
                }
                for a in accounts
            ]
        }

    async def generate_export_file(
        self,
        db: AsyncSession,
        user_id: UUID,
        categories: Optional[list[DataCategory]] = None,
    ) -> tuple[bytes, str]:
        """
        Generate a downloadable export file.

        Returns (file_bytes, filename).
        """
        exported = await self.export_user_data(db, user_id, categories)

        # Create ZIP file with JSON data
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Main data file
            data_json = json.dumps(exported.data, indent=2, default=str)
            zf.writestr("data.json", data_json)

            # Metadata file
            metadata = {
                "user_id": str(exported.user_id),
                "export_date": exported.export_date.isoformat(),
                "categories": [c.value for c in exported.categories],
                "checksum": exported.checksum,
                "format_version": "1.0",
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # README
            readme = """IDKit Data Export
==================

This archive contains your personal data exported from IDKit.

Files:
- data.json: Your personal data organized by category
- metadata.json: Export metadata including checksum

Format: JSON
Encoding: UTF-8

For questions about this export, contact: privacy@idkit.com
"""
            zf.writestr("README.txt", readme)

        filename = f"idkit_export_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        return buffer.getvalue(), filename

    async def delete_user_data(
        self,
        db: AsyncSession,
        user_id: UUID,
        categories: Optional[list[DataCategory]] = None,
        hard_delete: bool = False,
    ) -> DeletionResult:
        """
        Delete user data (Article 17 - Right to Erasure).

        Some data may be retained for legal compliance.
        """
        if categories is None:
            categories = list(DataCategory)

        items_deleted: dict[str, int] = {}
        retained_items: dict[str, int] = {}
        retention_reasons: list[str] = []
        categories_deleted: list[DataCategory] = []

        for category in categories:
            if category in self.LEGAL_RETENTION_CATEGORIES and not hard_delete:
                # Mark for delayed deletion instead
                retained_items[category.value] = await self._count_category_items(
                    db, user_id, category
                )
                retention_reasons.append(
                    f"{category.value}: Retained for {self.RETENTION_PERIODS[category]} days for legal compliance"
                )
            else:
                deleted = await self._delete_category(db, user_id, category)
                items_deleted[category.value] = deleted
                categories_deleted.append(category)

        await db.commit()

        logger.info(
            f"Deleted user data for {user_id}: {items_deleted}, retained: {retained_items}"
        )

        return DeletionResult(
            user_id=user_id,
            deleted_at=datetime.utcnow(),
            categories_deleted=categories_deleted,
            items_deleted=items_deleted,
            retained_items=retained_items,
            retention_reasons=retention_reasons,
        )

    async def _count_category_items(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: DataCategory,
    ) -> int:
        """Count items in a category for a user."""
        # Implement counting logic per category
        return 0

    async def _delete_category(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: DataCategory,
    ) -> int:
        """Delete data for a specific category."""
        deleters = {
            DataCategory.PROFILE: self._delete_profile,
            DataCategory.CONTENT: self._delete_content,
            DataCategory.MEDIA: self._delete_media,
            DataCategory.INTERACTIONS: self._delete_interactions,
            DataCategory.MESSAGES: self._delete_messages,
            DataCategory.SETTINGS: self._delete_settings,
            DataCategory.AI_DATA: self._delete_ai_data,
            DataCategory.SOCIAL: self._delete_social,
        }

        deleter = deleters.get(category)
        if deleter:
            return await deleter(db, user_id)
        return 0

    async def _delete_profile(self, db: AsyncSession, user_id: UUID) -> int:
        """Anonymize user profile (soft delete)."""
        from app.models.user import User, UserProfile

        # Anonymize profile
        await db.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                display_name="Deleted User",
                username=f"deleted_{user_id}",
                bio=None,
                avatar_url=None,
                cover_image_url=None,
                website_url=None,
            )
        )

        # Anonymize user email
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                email=f"deleted_{user_id}@deleted.idkit.com",
                is_active=False,
            )
        )

        return 1

    async def _delete_content(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete user posts and comments."""
        from app.models.feed import FeedPost, FeedComment

        posts_result = await db.execute(
            delete(FeedPost).where(FeedPost.user_id == user_id)
        )
        comments_result = await db.execute(
            delete(FeedComment).where(FeedComment.user_id == user_id)
        )

        return posts_result.rowcount + comments_result.rowcount

    async def _delete_media(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete user media files from database and S3 storage."""
        from app.models.media import MediaUpload
        from app.utils.storage import storage_service

        # First, fetch all media URLs to delete from S3
        media_result = await db.execute(
            select(MediaUpload.file_url, MediaUpload.thumbnail_url)
            .where(MediaUpload.user_id == user_id)
        )
        media_records = media_result.all()

        # Collect all S3 keys to delete
        s3_keys_to_delete = []
        for record in media_records:
            if record.file_url:
                key = storage_service.extract_key_from_url(record.file_url)
                if key:
                    s3_keys_to_delete.append(key)
            if record.thumbnail_url:
                key = storage_service.extract_key_from_url(record.thumbnail_url)
                if key:
                    s3_keys_to_delete.append(key)

        # Delete files from S3 in batches
        if s3_keys_to_delete:
            try:
                deletion_results = await storage_service.delete_files(s3_keys_to_delete)
                deleted_count = sum(1 for success in deletion_results.values() if success)
                failed_count = len(s3_keys_to_delete) - deleted_count
                if failed_count > 0:
                    logger.warning(
                        f"Failed to delete {failed_count} media files from S3 for user {user_id}"
                    )
                logger.info(f"Deleted {deleted_count} media files from S3 for user {user_id}")
            except Exception as e:
                logger.error(f"Error deleting media files from S3 for user {user_id}: {e}")

        # Also delete any files in the user's upload prefix (catch-all)
        try:
            user_prefix = f"uploads/{user_id}/"
            user_files = await storage_service.list_files(user_prefix)
            if user_files:
                additional_keys = [f["key"] for f in user_files]
                await storage_service.delete_files(additional_keys)
                logger.info(f"Deleted {len(additional_keys)} additional files from S3 prefix for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning user S3 prefix for {user_id}: {e}")

        # Delete from database
        result = await db.execute(
            delete(MediaUpload).where(MediaUpload.user_id == user_id)
        )
        return result.rowcount

    async def _delete_interactions(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete user interactions."""
        from app.models.feed import FeedLike, FeedSave
        from app.models.social import Follow

        likes = await db.execute(delete(FeedLike).where(FeedLike.user_id == user_id))
        saves = await db.execute(delete(FeedSave).where(FeedSave.user_id == user_id))
        follows = await db.execute(
            delete(Follow).where(
                (Follow.follower_id == user_id) | (Follow.following_id == user_id)
            )
        )

        return likes.rowcount + saves.rowcount + follows.rowcount

    async def _delete_messages(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete user messages."""
        # Implement based on messaging model
        return 0

    async def _delete_settings(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete user settings."""
        from app.models.user import UserSettings

        result = await db.execute(
            delete(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.rowcount

    async def _delete_ai_data(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete AI twin data from database and S3 storage."""
        from app.models.twin import AITwin, AvatarConfig, VoiceConfig
        from app.utils.storage import storage_service

        # First, fetch all AI twin related URLs to delete from S3
        twins_result = await db.execute(
            select(AITwin).where(AITwin.user_id == user_id)
        )
        twins = twins_result.scalars().all()

        s3_keys_to_delete = []

        for twin in twins:
            # Collect avatar-related assets
            if twin.avatar_url:
                key = storage_service.extract_key_from_url(twin.avatar_url)
                if key:
                    s3_keys_to_delete.append(key)

            # Collect voice samples and synthesized audio
            if hasattr(twin, 'voice_samples') and twin.voice_samples:
                for sample_url in twin.voice_samples:
                    key = storage_service.extract_key_from_url(sample_url)
                    if key:
                        s3_keys_to_delete.append(key)

            # Collect training images
            if hasattr(twin, 'training_images') and twin.training_images:
                for image_url in twin.training_images:
                    key = storage_service.extract_key_from_url(image_url)
                    if key:
                        s3_keys_to_delete.append(key)

        # Delete files from S3
        if s3_keys_to_delete:
            try:
                deletion_results = await storage_service.delete_files(s3_keys_to_delete)
                deleted_count = sum(1 for success in deletion_results.values() if success)
                logger.info(f"Deleted {deleted_count} AI assets from S3 for user {user_id}")
            except Exception as e:
                logger.error(f"Error deleting AI assets from S3 for user {user_id}: {e}")

        # Also delete any files in the user's AI twins prefix (catch-all)
        try:
            ai_prefix = f"ai-twins/{user_id}/"
            ai_files = await storage_service.list_files(ai_prefix)
            if ai_files:
                additional_keys = [f["key"] for f in ai_files]
                await storage_service.delete_files(additional_keys)
                logger.info(f"Deleted {len(additional_keys)} additional AI files from S3 prefix for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning AI twins S3 prefix for {user_id}: {e}")

        # Delete voice and avatar config records first (due to foreign keys)
        for twin in twins:
            if hasattr(twin, 'avatar_config_id') and twin.avatar_config_id:
                await db.execute(delete(AvatarConfig).where(AvatarConfig.id == twin.avatar_config_id))
            if hasattr(twin, 'voice_config_id') and twin.voice_config_id:
                await db.execute(delete(VoiceConfig).where(VoiceConfig.id == twin.voice_config_id))

        # Delete AI twins from database
        result = await db.execute(delete(AITwin).where(AITwin.user_id == user_id))
        return result.rowcount

    async def _delete_social(self, db: AsyncSession, user_id: UUID) -> int:
        """Delete connected social accounts."""
        from app.models.social import SocialAccount

        result = await db.execute(
            delete(SocialAccount).where(SocialAccount.user_id == user_id)
        )
        return result.rowcount

    async def record_consent(
        self,
        db: AsyncSession,
        user_id: UUID,
        consent_type: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """Record user consent (opt-in/opt-out)."""
        from app.models.user import ConsentLog

        consent_id = uuid4()
        now = datetime.utcnow()

        consent = ConsentLog(
            id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=now if granted else None,
            revoked_at=None if granted else now,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(consent)
        await db.commit()

        return ConsentRecord(
            id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=now if granted else None,
            revoked_at=None if granted else now,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_privacy_settings(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> PrivacySettings:
        """Get user privacy settings."""
        from app.models.user import UserSettings

        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if settings and settings.privacy_settings:
            ps = settings.privacy_settings
            return PrivacySettings(
                user_id=user_id,
                profile_visibility=ps.get("profile_visibility", "public"),
                activity_visibility=ps.get("activity_visibility", "followers"),
                search_visibility=ps.get("search_visibility", True),
                analytics_enabled=ps.get("analytics_enabled", True),
                personalization_enabled=ps.get("personalization_enabled", True),
                marketing_emails=ps.get("marketing_emails", False),
                product_updates=ps.get("product_updates", True),
                third_party_sharing=ps.get("third_party_sharing", False),
            )

        return PrivacySettings(user_id=user_id)

    async def update_privacy_settings(
        self,
        db: AsyncSession,
        user_id: UUID,
        settings: PrivacySettings,
    ) -> PrivacySettings:
        """Update user privacy settings."""
        from app.models.user import UserSettings

        privacy_dict = {
            "profile_visibility": settings.profile_visibility,
            "activity_visibility": settings.activity_visibility,
            "search_visibility": settings.search_visibility,
            "analytics_enabled": settings.analytics_enabled,
            "personalization_enabled": settings.personalization_enabled,
            "marketing_emails": settings.marketing_emails,
            "product_updates": settings.product_updates,
            "third_party_sharing": settings.third_party_sharing,
        }

        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()

        if user_settings:
            user_settings.privacy_settings = privacy_dict
        else:
            user_settings = UserSettings(
                user_id=user_id,
                privacy_settings=privacy_dict,
            )
            db.add(user_settings)

        await db.commit()
        settings.updated_at = datetime.utcnow()
        return settings


# Global service instance
gdpr_service = GDPRService()
