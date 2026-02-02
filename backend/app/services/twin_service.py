"""
Twin Service

Core service for AI Twin management.
Creates and manages digital avatars with cloned voices.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.heygen_client import HeyGenClient, HeyGenError
from app.integrations.elevenlabs_client import ElevenLabsClient, ElevenLabsError
from app.schemas.twin import (
    AITwin,
    AssetType,
    AvatarSettings,
    TwinAsset,
    TwinStatus,
    VoiceSettings,
)


class TwinService:
    """
    Service for creating and managing AI Twins.
    
    Orchestrates:
    - Voice cloning via ElevenLabs
    - Avatar creation via HeyGen
    - Asset management
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._heygen: Optional[HeyGenClient] = None
        self._elevenlabs: Optional[ElevenLabsClient] = None

    @property
    def heygen(self) -> HeyGenClient:
        """Lazy-load HeyGen client."""
        if not self._heygen:
            try:
                self._heygen = HeyGenClient()
            except ValueError:
                # API key not configured - will fail on actual use
                pass
        return self._heygen

    @property
    def elevenlabs(self) -> ElevenLabsClient:
        """Lazy-load ElevenLabs client."""
        if not self._elevenlabs:
            try:
                self._elevenlabs = ElevenLabsClient()
            except ValueError:
                pass
        return self._elevenlabs

    async def create_twin(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        voice_settings: Optional[VoiceSettings] = None,
        avatar_settings: Optional[AvatarSettings] = None,
    ) -> AITwin:
        """
        Create a new AI Twin.
        
        Returns a pending twin awaiting samples.
        """
        twin = AITwin(
            twin_id=uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            status=TwinStatus.PENDING,
            status_message="Awaiting video sample upload",
            voice_settings=voice_settings or VoiceSettings(),
            avatar_settings=avatar_settings or AvatarSettings(),
        )

        # Persist to database
        await self._save_twin(twin)

        return twin

    async def get_twin(
        self,
        twin_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[AITwin]:
        """Get a twin by ID."""
        from app.models.twin import AITwinRecord

        query = select(AITwinRecord).where(AITwinRecord.id == twin_id)
        if user_id:
            query = query.where(AITwinRecord.user_id == user_id)

        result = await self.db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._record_to_twin(record)

    async def get_twins_for_user(
        self,
        user_id: UUID,
        include_disabled: bool = False,
    ) -> List[AITwin]:
        """Get all twins for a user."""
        from app.models.twin import AITwinRecord

        query = select(AITwinRecord).where(AITwinRecord.user_id == user_id)

        if not include_disabled:
            query = query.where(AITwinRecord.status != TwinStatus.DISABLED.value)

        query = query.order_by(AITwinRecord.created_at.desc())

        result = await self.db.execute(query)
        records = result.scalars().all()

        return [self._record_to_twin(r) for r in records]

    async def add_video_sample(
        self,
        twin_id: UUID,
        video_url: str,
        filename: str,
        duration_seconds: float,
    ) -> TwinAsset:
        """
        Add a video sample for avatar creation.
        
        This also extracts audio for voice cloning.
        """
        asset = TwinAsset(
            asset_id=uuid4(),
            asset_type=AssetType.VIDEO_SAMPLE,
            url=video_url,
            filename=filename,
            duration_seconds=duration_seconds,
        )

        # Update twin
        twin = await self.get_twin(twin_id)
        if twin:
            twin.assets.append(asset)
            await self._update_twin(twin)

        return asset

    async def add_audio_sample(
        self,
        twin_id: UUID,
        audio_url: str,
        filename: str,
        duration_seconds: float,
    ) -> TwinAsset:
        """Add an audio sample for voice cloning."""
        asset = TwinAsset(
            asset_id=uuid4(),
            asset_type=AssetType.AUDIO_SAMPLE,
            url=audio_url,
            filename=filename,
            duration_seconds=duration_seconds,
        )

        twin = await self.get_twin(twin_id)
        if twin:
            twin.assets.append(asset)
            await self._update_twin(twin)

        return asset

    async def start_processing(
        self,
        twin_id: UUID,
    ) -> AITwin:
        """
        Start processing samples to create the twin.
        
        Initiates:
        1. Voice cloning via ElevenLabs
        2. Avatar creation via HeyGen
        """
        twin = await self.get_twin(twin_id)
        if not twin:
            raise ValueError(f"Twin {twin_id} not found")

        # Get samples
        video_samples = [
            a for a in twin.assets
            if a.asset_type == AssetType.VIDEO_SAMPLE
        ]
        audio_samples = [
            a for a in twin.assets
            if a.asset_type == AssetType.AUDIO_SAMPLE
        ]

        if not video_samples:
            raise ValueError("No video sample provided")

        # Start voice cloning
        twin.status = TwinStatus.PROCESSING_VOICE
        twin.status_message = "Creating voice clone..."
        await self._update_twin(twin)

        try:
            # Use audio from video if no separate audio
            audio_urls = [a.url for a in audio_samples if a.url]
            if not audio_urls and video_samples:
                # Extract audio from video (would use ffmpeg in production)
                audio_urls = [v.url for v in video_samples if v.url]

            if self.elevenlabs and audio_urls:
                voice_result = await self.elevenlabs.clone_voice(
                    name=f"{twin.name}_voice",
                    audio_files=audio_urls[:3],  # Max 3 samples
                    description=f"Voice clone for {twin.name}",
                )
                twin.elevenlabs_voice_id = voice_result.get("voice_id")

                # Get similarity score
                if twin.elevenlabs_voice_id:
                    score = await self.elevenlabs.get_similarity_score(
                        twin.elevenlabs_voice_id,
                        audio_urls[0],
                    )
                    twin.voice_similarity_score = score

        except ElevenLabsError as e:
            twin.status = TwinStatus.FAILED
            twin.status_message = f"Voice clone failed: {e.message}"
            await self._update_twin(twin)
            raise

        # Start avatar creation
        twin.status = TwinStatus.PROCESSING_AVATAR
        twin.status_message = "Creating avatar..."
        await self._update_twin(twin)

        try:
            if self.heygen and video_samples:
                avatar_result = await self.heygen.create_avatar(
                    video_url=video_samples[0].url,
                    name=twin.name,
                    user_id=twin.user_id,
                )
                twin.heygen_avatar_id = avatar_result.get("avatar_id")

        except HeyGenError as e:
            twin.status = TwinStatus.FAILED
            twin.status_message = f"Avatar creation failed: {e.message}"
            await self._update_twin(twin)
            raise

        # Mark as ready
        twin.status = TwinStatus.READY
        twin.status_message = "Twin is ready!"
        twin.ready_at = datetime.utcnow()
        await self._update_twin(twin)

        return twin

    async def update_twin(
        self,
        twin_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        voice_settings: Optional[VoiceSettings] = None,
        avatar_settings: Optional[AvatarSettings] = None,
    ) -> AITwin:
        """Update twin settings."""
        twin = await self.get_twin(twin_id)
        if not twin:
            raise ValueError(f"Twin {twin_id} not found")

        if name:
            twin.name = name
        if description is not None:
            twin.description = description
        if voice_settings:
            twin.voice_settings = voice_settings
        if avatar_settings:
            twin.avatar_settings = avatar_settings

        twin.updated_at = datetime.utcnow()
        await self._update_twin(twin)

        return twin

    async def delete_twin(
        self,
        twin_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a twin and its external assets."""
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            return False

        # Delete external resources
        try:
            if twin.heygen_avatar_id and self.heygen:
                await self.heygen.delete_avatar(twin.heygen_avatar_id)
        except HeyGenError:
            pass

        try:
            if twin.elevenlabs_voice_id and self.elevenlabs:
                await self.elevenlabs.delete_voice(twin.elevenlabs_voice_id)
        except ElevenLabsError:
            pass

        # Delete from database
        from app.models.twin import AITwinRecord
        result = await self.db.execute(
            select(AITwinRecord).where(
                AITwinRecord.id == twin_id,
                AITwinRecord.user_id == user_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            await self.db.delete(record)
            await self.db.flush()

        return True

    async def _save_twin(self, twin: AITwin) -> None:
        """Save a new twin to database."""
        from app.models.twin import AITwinRecord

        record = AITwinRecord(
            id=twin.twin_id,
            user_id=twin.user_id,
            name=twin.name,
            description=twin.description,
            status=twin.status.value,
            status_message=twin.status_message,
            heygen_avatar_id=twin.heygen_avatar_id,
            elevenlabs_voice_id=twin.elevenlabs_voice_id,
            voice_settings=twin.voice_settings.model_dump(),
            avatar_settings=twin.avatar_settings.model_dump(),
            voice_similarity_score=twin.voice_similarity_score,
            avatar_quality_score=twin.avatar_quality_score,
            assets=[a.model_dump() for a in twin.assets],
        )

        self.db.add(record)
        await self.db.flush()

    async def _update_twin(self, twin: AITwin) -> None:
        """Update existing twin in database."""
        from app.models.twin import AITwinRecord

        result = await self.db.execute(
            select(AITwinRecord).where(AITwinRecord.id == twin.twin_id)
        )
        record = result.scalar_one_or_none()

        if record:
            record.name = twin.name
            record.description = twin.description
            record.status = twin.status.value
            record.status_message = twin.status_message
            record.heygen_avatar_id = twin.heygen_avatar_id
            record.elevenlabs_voice_id = twin.elevenlabs_voice_id
            record.voice_settings = twin.voice_settings.model_dump()
            record.avatar_settings = twin.avatar_settings.model_dump()
            record.voice_similarity_score = twin.voice_similarity_score
            record.avatar_quality_score = twin.avatar_quality_score
            record.assets = [a.model_dump() for a in twin.assets]
            record.ready_at = twin.ready_at

            await self.db.flush()

    def _record_to_twin(self, record: Any) -> AITwin:
        """Convert database record to AITwin."""
        return AITwin(
            twin_id=record.id,
            user_id=record.user_id,
            name=record.name,
            description=record.description,
            status=TwinStatus(record.status),
            status_message=record.status_message,
            heygen_avatar_id=record.heygen_avatar_id,
            elevenlabs_voice_id=record.elevenlabs_voice_id,
            voice_settings=VoiceSettings(**(record.voice_settings or {})),
            avatar_settings=AvatarSettings(**(record.avatar_settings or {})),
            voice_similarity_score=record.voice_similarity_score,
            avatar_quality_score=record.avatar_quality_score,
            assets=[TwinAsset(**a) for a in (record.assets or [])],
            total_videos_generated=record.total_videos_generated or 0,
            total_audio_generated=record.total_audio_generated or 0,
            created_at=record.created_at,
            updated_at=record.updated_at,
            ready_at=record.ready_at,
        )
