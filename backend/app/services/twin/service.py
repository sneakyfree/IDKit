"""
AI Twin Service

Orchestrates avatar and voice providers for AI Twin creation and generation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ai_twin import (
    AiTwin,
    TwinMediaUpload,
    AvatarConfig,
    VoiceConfig,
    TwinTrainingJob,
    TwinGeneratedAsset,
    TwinStatus,
    TrainingJobStatus,
)
from app.providers.interfaces.avatar_provider import (
    AvatarProvider,
    AvatarTrainingConfig,
    AvatarGenerationConfig,
    AvatarJobStatus,
)
from app.providers.interfaces.voice_provider import (
    VoiceProvider,
    VoiceCloningConfig,
    VoiceSynthesisConfig,
    VoiceJobStatus,
)
from app.providers.heygen import HeyGenAvatarProvider
from app.providers.elevenlabs import ElevenLabsVoiceProvider


class AiTwinService:
    """
    Orchestrates AI Twin creation and content generation.

    Manages:
    - Avatar creation (via HeyGen or self-hosted)
    - Voice cloning (via ElevenLabs or self-hosted)
    - Video generation with avatar and voice
    - Asset tracking and management
    """

    def __init__(
        self,
        db: AsyncSession,
        avatar_provider: Optional[AvatarProvider] = None,
        voice_provider: Optional[VoiceProvider] = None,
    ):
        self.db = db
        self._avatar_provider = avatar_provider
        self._voice_provider = voice_provider

    @property
    def avatar_provider(self) -> AvatarProvider:
        """Get avatar provider (lazy init)."""
        if self._avatar_provider is None:
            self._avatar_provider = HeyGenAvatarProvider()
        return self._avatar_provider

    @property
    def voice_provider(self) -> VoiceProvider:
        """Get voice provider (lazy init)."""
        if self._voice_provider is None:
            self._voice_provider = ElevenLabsVoiceProvider()
        return self._voice_provider

    # ==================== Twin Management ====================

    async def create_twin(
        self,
        user_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        personality_prompt: Optional[str] = None,
        communication_style: str = "conversational",
        default_language: str = "en",
    ) -> AiTwin:
        """
        Create a new AI Twin.

        The twin starts in DRAFT status until avatar and voice are trained.
        """
        twin = AiTwin(
            user_id=user_id,
            name=name,
            description=description,
            personality_prompt=personality_prompt,
            communication_style=communication_style,
            default_language=default_language,
            status=TwinStatus.DRAFT.value,
        )

        self.db.add(twin)
        await self.db.commit()
        await self.db.refresh(twin)

        # Create default configs
        avatar_config = AvatarConfig(ai_twin_id=twin.id)
        voice_config = VoiceConfig(ai_twin_id=twin.id)

        self.db.add(avatar_config)
        self.db.add(voice_config)
        await self.db.commit()

        return twin

    async def get_twin(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[AiTwin]:
        """Get a twin by ID (with ownership check)."""
        result = await self.db.execute(
            select(AiTwin).where(
                AiTwin.id == twin_id,
                AiTwin.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_twins(
        self,
        user_id: uuid.UUID,
    ) -> List[AiTwin]:
        """List all twins for a user."""
        result = await self.db.execute(
            select(AiTwin)
            .where(AiTwin.user_id == user_id)
            .order_by(desc(AiTwin.created_at))
        )
        return list(result.scalars().all())

    async def delete_twin(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a twin and its associated resources."""
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            return False

        # Delete from providers
        if twin.avatar_id:
            try:
                await self.avatar_provider.delete_avatar(twin.avatar_id)
            except Exception:
                pass  # Best effort

        if twin.voice_id:
            try:
                await self.voice_provider.delete_voice(twin.voice_id)
            except Exception:
                pass  # Best effort

        # Delete from database (cascades to related tables)
        await self.db.delete(twin)
        await self.db.commit()

        return True

    # ==================== Media Upload ====================

    async def add_media(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
        media_type: str,
        purpose: str,
        file_url: str,
        file_name: str,
        file_size_bytes: int,
        mime_type: str,
        duration_seconds: Optional[float] = None,
    ) -> TwinMediaUpload:
        """Add a media file for training."""
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError("Twin not found")

        media = TwinMediaUpload(
            ai_twin_id=twin_id,
            user_id=user_id,
            media_type=media_type,
            purpose=purpose,
            file_url=file_url,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
        )

        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)

        return media

    async def get_training_media(
        self,
        twin_id: uuid.UUID,
        purpose: str,
    ) -> List[TwinMediaUpload]:
        """Get all approved media for a specific purpose."""
        result = await self.db.execute(
            select(TwinMediaUpload).where(
                TwinMediaUpload.ai_twin_id == twin_id,
                TwinMediaUpload.purpose == purpose,
                TwinMediaUpload.is_approved == True,
            )
        )
        return list(result.scalars().all())

    async def approve_media(
        self,
        media_id: uuid.UUID,
        user_id: uuid.UUID,
        quality_score: Optional[float] = None,
    ) -> bool:
        """Approve media for training after quality check."""
        result = await self.db.execute(
            select(TwinMediaUpload).where(
                TwinMediaUpload.id == media_id,
                TwinMediaUpload.user_id == user_id,
            )
        )
        media = result.scalar_one_or_none()

        if not media:
            return False

        media.is_approved = True
        media.is_processed = True
        if quality_score is not None:
            media.quality_score = quality_score

        await self.db.commit()
        return True

    # ==================== Avatar Training ====================

    async def train_avatar(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TwinTrainingJob:
        """
        Start avatar training from uploaded photos.

        Requires approved photo media uploads.
        """
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError("Twin not found")

        # Get approved training media
        photos = await self.get_training_media(twin_id, "avatar_training")
        if not photos:
            raise ValueError("No approved photos for avatar training")

        photo_urls = [p.file_url for p in photos]

        # Get video URLs if any (for motion training)
        videos = await self.get_training_media(twin_id, "avatar_video_training")
        video_urls = [v.file_url for v in videos]

        # Create training job
        job = TwinTrainingJob(
            ai_twin_id=twin_id,
            user_id=user_id,
            job_type="avatar_training",
            provider=self.avatar_provider.provider_name,
            status=TrainingJobStatus.PENDING.value,
            input_config={
                "photo_count": len(photo_urls),
                "video_count": len(video_urls),
            },
        )
        self.db.add(job)

        # Update twin status
        twin.avatar_status = TwinStatus.TRAINING.value
        await self.db.commit()
        await self.db.refresh(job)

        # Start training with provider
        try:
            config = AvatarTrainingConfig(
                photo_urls=photo_urls,
                video_urls=video_urls,
                name=twin.name,
            )

            result = await self.avatar_provider.create_avatar(config)

            # Update job with provider info
            job.provider_job_id = result.avatar_id
            job.started_at = datetime.now(timezone.utc)

            if result.status == AvatarJobStatus.COMPLETED:
                job.status = TrainingJobStatus.COMPLETED.value
                job.completed_at = datetime.now(timezone.utc)
                job.result_id = result.avatar_id
                job.result_url = result.preview_url

                # Update twin
                twin.avatar_id = result.avatar_id
                twin.avatar_preview_url = result.preview_url
                twin.avatar_provider = self.avatar_provider.provider_name
                twin.avatar_status = TwinStatus.READY.value
            else:
                job.status = TrainingJobStatus.PROCESSING.value

            await self.db.commit()
            await self.db.refresh(job)

        except Exception as e:
            job.status = TrainingJobStatus.FAILED.value
            job.error_message = str(e)
            twin.avatar_status = TwinStatus.ERROR.value
            await self.db.commit()
            raise

        return job

    async def check_avatar_training(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TwinTrainingJob:
        """Check status of avatar training job."""
        result = await self.db.execute(
            select(TwinTrainingJob).where(
                TwinTrainingJob.id == job_id,
                TwinTrainingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError("Training job not found")

        if job.status == TrainingJobStatus.PROCESSING.value and job.provider_job_id:
            # Check with provider
            status_result = await self.avatar_provider.get_avatar_status(
                job.provider_job_id
            )

            if status_result.status == AvatarJobStatus.COMPLETED:
                job.status = TrainingJobStatus.COMPLETED.value
                job.completed_at = datetime.now(timezone.utc)
                job.result_id = status_result.avatar_id
                job.result_url = status_result.preview_url

                # Update twin
                twin_result = await self.db.execute(
                    select(AiTwin).where(AiTwin.id == job.ai_twin_id)
                )
                twin = twin_result.scalar_one_or_none()
                if twin:
                    twin.avatar_id = status_result.avatar_id
                    twin.avatar_preview_url = status_result.preview_url
                    twin.avatar_provider = self.avatar_provider.provider_name
                    twin.avatar_status = TwinStatus.READY.value

                await self.db.commit()

            elif status_result.status == AvatarJobStatus.FAILED:
                job.status = TrainingJobStatus.FAILED.value
                job.error_message = status_result.metadata.get("error", "Unknown error")
                await self.db.commit()

        await self.db.refresh(job)
        return job

    # ==================== Voice Cloning ====================

    async def train_voice(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TwinTrainingJob:
        """
        Start voice cloning from uploaded audio samples.

        Requires approved audio media uploads.
        """
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError("Twin not found")

        # Get approved training media
        audio_samples = await self.get_training_media(twin_id, "voice_training")
        if not audio_samples:
            raise ValueError("No approved audio samples for voice training")

        audio_urls = [a.file_url for a in audio_samples]

        # Create training job
        job = TwinTrainingJob(
            ai_twin_id=twin_id,
            user_id=user_id,
            job_type="voice_training",
            provider=self.voice_provider.provider_name,
            status=TrainingJobStatus.PENDING.value,
            input_config={
                "sample_count": len(audio_urls),
            },
        )
        self.db.add(job)

        # Update twin status
        twin.voice_status = TwinStatus.TRAINING.value
        await self.db.commit()
        await self.db.refresh(job)

        # Start cloning with provider
        try:
            config = VoiceCloningConfig(
                audio_urls=audio_urls,
                name=f"{twin.name}'s Voice",
                description=f"Cloned voice for AI Twin: {twin.name}",
            )

            result = await self.voice_provider.clone_voice(config)

            # Update job
            job.provider_job_id = result.voice_id
            job.started_at = datetime.now(timezone.utc)

            if result.status == VoiceJobStatus.COMPLETED:
                job.status = TrainingJobStatus.COMPLETED.value
                job.completed_at = datetime.now(timezone.utc)
                job.result_id = result.voice_id
                job.result_url = result.preview_url

                # Update twin
                twin.voice_id = result.voice_id
                twin.voice_preview_url = result.preview_url
                twin.voice_provider = self.voice_provider.provider_name
                twin.voice_status = TwinStatus.READY.value
            elif result.status == VoiceJobStatus.FAILED:
                job.status = TrainingJobStatus.FAILED.value
                job.error_message = result.metadata.get("error", "Unknown error")
                twin.voice_status = TwinStatus.ERROR.value
            else:
                job.status = TrainingJobStatus.PROCESSING.value

            await self.db.commit()
            await self.db.refresh(job)

        except Exception as e:
            job.status = TrainingJobStatus.FAILED.value
            job.error_message = str(e)
            twin.voice_status = TwinStatus.ERROR.value
            await self.db.commit()
            raise

        return job

    # ==================== Content Generation ====================

    async def generate_video(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
        text: Optional[str] = None,
        audio_url: Optional[str] = None,
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        background_color: str = "#ffffff",
    ) -> TwinGeneratedAsset:
        """
        Generate a video with the AI Twin speaking.

        Either text or audio_url must be provided.
        """
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError("Twin not found")

        if twin.avatar_status != TwinStatus.READY.value:
            raise ValueError("Avatar not ready. Please train avatar first.")

        if not twin.avatar_id:
            raise ValueError("Avatar ID not set")

        # If text provided and voice is ready, synthesize audio first
        actual_audio_url = audio_url
        if text and not audio_url:
            if twin.voice_status == TwinStatus.READY.value and twin.voice_id:
                # Synthesize speech
                synthesis_config = VoiceSynthesisConfig(
                    voice_id=twin.voice_id,
                    text=text,
                )
                synthesis_result = await self.voice_provider.synthesize_speech(
                    synthesis_config
                )
                # In production, would upload audio_data to S3
                # For now, we'll pass text directly to HeyGen
                pass

        # Build generation config
        config = AvatarGenerationConfig(
            avatar_id=twin.avatar_id,
            text=text,
            audio_url=actual_audio_url,
            voice_id=twin.voice_id if text and not audio_url else None,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            background_color=background_color,
        )

        # Start generation
        result = await self.avatar_provider.generate_video(config)

        # Create asset record
        asset = TwinGeneratedAsset(
            ai_twin_id=twin_id,
            user_id=user_id,
            asset_type="video",
            input_text=text,
            input_audio_url=audio_url,
            output_url="",  # Will be updated when complete
            duration_seconds=0,  # Will be updated when complete
            status="generating",
            provider=self.avatar_provider.provider_name,
            provider_job_id=result.job_id,
            settings={
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
                "background_color": background_color,
            },
        )

        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)

        # Update twin stats
        twin.video_count += 1
        await self.db.commit()

        return asset

    async def check_video_generation(
        self,
        asset_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TwinGeneratedAsset:
        """Check status of video generation."""
        result = await self.db.execute(
            select(TwinGeneratedAsset).where(
                TwinGeneratedAsset.id == asset_id,
                TwinGeneratedAsset.user_id == user_id,
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            raise ValueError("Asset not found")

        if asset.status == "generating" and asset.provider_job_id:
            # Check with provider
            status_result = await self.avatar_provider.get_video_status(
                asset.provider_job_id
            )

            if status_result.status == AvatarJobStatus.COMPLETED:
                asset.status = "ready"
                asset.output_url = status_result.video_url or ""
                asset.thumbnail_url = status_result.thumbnail_url
                asset.duration_seconds = status_result.duration_seconds or 0

                # Update twin stats
                twin_result = await self.db.execute(
                    select(AiTwin).where(AiTwin.id == asset.ai_twin_id)
                )
                twin = twin_result.scalar_one_or_none()
                if twin and status_result.duration_seconds:
                    twin.total_minutes_generated += status_result.duration_seconds / 60

                await self.db.commit()

            elif status_result.status == AvatarJobStatus.FAILED:
                asset.status = "failed"
                await self.db.commit()

        await self.db.refresh(asset)
        return asset

    async def synthesize_speech(
        self,
        twin_id: uuid.UUID,
        user_id: uuid.UUID,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> TwinGeneratedAsset:
        """
        Generate speech audio from the AI Twin's voice.
        """
        twin = await self.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError("Twin not found")

        if twin.voice_status != TwinStatus.READY.value:
            raise ValueError("Voice not ready. Please train voice first.")

        if not twin.voice_id:
            raise ValueError("Voice ID not set")

        # Synthesize speech
        config = VoiceSynthesisConfig(
            voice_id=twin.voice_id,
            text=text,
            stability=stability,
            similarity_boost=similarity_boost,
        )

        result = await self.voice_provider.synthesize_speech(config)

        # In production, upload audio_data to S3 and get URL
        # For now, create asset with placeholder
        asset = TwinGeneratedAsset(
            ai_twin_id=twin_id,
            user_id=user_id,
            asset_type="audio",
            input_text=text,
            output_url="",  # Would be S3 URL in production
            duration_seconds=result.duration_seconds or 0,
            status="ready",
            provider=self.voice_provider.provider_name,
            settings={
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        )

        self.db.add(asset)

        # Update twin stats
        twin.audio_count += 1
        if result.duration_seconds:
            twin.total_minutes_generated += result.duration_seconds / 60

        await self.db.commit()
        await self.db.refresh(asset)

        return asset

    # ==================== Helper Methods ====================

    async def update_twin_status(
        self,
        twin_id: uuid.UUID,
    ):
        """
        Update overall twin status based on avatar and voice status.
        """
        result = await self.db.execute(
            select(AiTwin).where(AiTwin.id == twin_id)
        )
        twin = result.scalar_one_or_none()

        if not twin:
            return

        # Determine overall status
        if twin.avatar_status == TwinStatus.READY.value and \
           twin.voice_status == TwinStatus.READY.value:
            twin.status = TwinStatus.READY.value
        elif twin.avatar_status == TwinStatus.ERROR.value or \
             twin.voice_status == TwinStatus.ERROR.value:
            twin.status = TwinStatus.ERROR.value
        elif twin.avatar_status == TwinStatus.TRAINING.value or \
             twin.voice_status == TwinStatus.TRAINING.value:
            twin.status = TwinStatus.TRAINING.value
        else:
            twin.status = TwinStatus.DRAFT.value

        await self.db.commit()
