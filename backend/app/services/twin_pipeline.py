"""
Twin Pipeline

Content generation pipeline using AI Twin.
Script → Voice → Video integration.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.heygen_client import HeyGenClient, HeyGenError
from app.integrations.elevenlabs_client import ElevenLabsClient, ElevenLabsError
from app.schemas.twin import (
    AITwin,
    TwinContent,
    TwinStatus,
    VoiceSettings,
)
from app.services.twin_service import TwinService


class TwinPipeline:
    """
    Content generation pipeline using AI Twin.
    
    Pipeline stages:
    1. Script generation (Content Agent or user-provided)
    2. Voice synthesis (ElevenLabs)
    3. Video generation (HeyGen)
    4. Quality verification
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.twin_service = TwinService(db)
        self._heygen: Optional[HeyGenClient] = None
        self._elevenlabs: Optional[ElevenLabsClient] = None

    @property
    def heygen(self) -> HeyGenClient:
        if not self._heygen:
            try:
                self._heygen = HeyGenClient()
            except ValueError:
                pass
        return self._heygen

    @property
    def elevenlabs(self) -> ElevenLabsClient:
        if not self._elevenlabs:
            try:
                self._elevenlabs = ElevenLabsClient()
            except ValueError:
                pass
        return self._elevenlabs

    async def generate_content(
        self,
        twin_id: UUID,
        user_id: UUID,
        script: str,
        content_type: str = "video",
        language: str = "en",
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        voice_settings: Optional[VoiceSettings] = None,
    ) -> TwinContent:
        """
        Generate content using the AI Twin.
        
        Full pipeline: Script → Voice → Video
        """
        # Get the twin
        twin = await self.twin_service.get_twin(twin_id, user_id)
        if not twin:
            raise ValueError(f"Twin {twin_id} not found")

        if twin.status != TwinStatus.READY:
            raise ValueError(f"Twin is not ready (status: {twin.status.value})")

        # Create content record
        content = TwinContent(
            content_id=uuid4(),
            twin_id=twin_id,
            user_id=user_id,
            content_type=content_type,
            script=script,
            language=language,
            status="processing",
            current_step="voice_synthesis",
            progress_percent=10.0,
        )

        # Save initial record
        await self._save_content(content)

        try:
            # Step 1: Generate voice audio
            content.current_step = "voice_synthesis"
            content.progress_percent = 20.0
            await self._update_content(content)

            audio_url = await self._generate_voice(
                twin=twin,
                script=script,
                voice_settings=voice_settings,
            )
            content.audio_url = audio_url
            content.progress_percent = 50.0
            await self._update_content(content)

            # Step 2: Generate video (if requested)
            if content_type == "video":
                content.current_step = "video_generation"
                content.progress_percent = 60.0
                await self._update_content(content)

                video_result = await self._generate_video(
                    twin=twin,
                    audio_url=audio_url,
                    aspect_ratio=aspect_ratio,
                )
                content.video_url = video_result.get("video_url")
                content.heygen_video_id = video_result.get("video_id")
                content.duration_seconds = video_result.get("duration")
                content.resolution = resolution

            # Mark complete
            content.status = "completed"
            content.current_step = None
            content.progress_percent = 100.0
            content.completed_at = datetime.utcnow()
            await self._update_content(content)

            # Increment twin counters
            await self._increment_counters(twin, content_type)

        except (HeyGenError, ElevenLabsError) as e:
            content.status = "failed"
            content.error = str(e)
            await self._update_content(content)
            raise

        return content

    async def generate_audio_only(
        self,
        twin_id: UUID,
        user_id: UUID,
        script: str,
        voice_settings: Optional[VoiceSettings] = None,
    ) -> TwinContent:
        """Generate audio only (no video)."""
        return await self.generate_content(
            twin_id=twin_id,
            user_id=user_id,
            script=script,
            content_type="audio",
            voice_settings=voice_settings,
        )

    async def _generate_voice(
        self,
        twin: AITwin,
        script: str,
        voice_settings: Optional[VoiceSettings] = None,
    ) -> str:
        """Generate voice audio using ElevenLabs."""
        if not twin.elevenlabs_voice_id:
            raise ValueError("Twin does not have a voice clone")

        settings = voice_settings or twin.voice_settings

        # Generate audio
        audio_bytes = await self.elevenlabs.synthesize_speech(
            voice_id=twin.elevenlabs_voice_id,
            text=script,
            stability=settings.stability,
            similarity_boost=settings.similarity_boost,
            style=settings.style,
            use_speaker_boost=settings.use_speaker_boost,
        )

        # Save to temp file and upload
        # In production, would upload to S3/GCS
        audio_id = uuid4()
        temp_path = f"/tmp/audio_{audio_id}.mp3"
        
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Return URL (placeholder - would be cloud storage URL)
        return f"https://storage.idkit.com/audio/{audio_id}.mp3"

    async def _generate_video(
        self,
        twin: AITwin,
        audio_url: str,
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """Generate video using HeyGen."""
        if not twin.heygen_avatar_id:
            raise ValueError("Twin does not have an avatar")

        # Start video generation
        result = await self.heygen.generate_video(
            avatar_id=twin.heygen_avatar_id,
            script="",  # Not needed when using audio_url
            audio_url=audio_url,
            background=twin.avatar_settings.background_type,
            aspect_ratio=aspect_ratio,
        )

        video_id = result.get("video_id")
        if not video_id:
            raise HeyGenError("No video_id returned from HeyGen")

        # Wait for completion
        completed = await self.heygen.wait_for_video(
            video_id=video_id,
            timeout_seconds=300,
        )

        return {
            "video_id": video_id,
            "video_url": completed.get("video_url"),
            "duration": completed.get("duration"),
        }

    async def get_content(
        self,
        content_id: UUID,
        user_id: UUID,
    ) -> Optional[TwinContent]:
        """Get content by ID."""
        from app.models.twin import TwinContentRecord

        from sqlalchemy import select
        result = await self.db.execute(
            select(TwinContentRecord).where(
                TwinContentRecord.id == content_id,
                TwinContentRecord.user_id == user_id,
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._record_to_content(record)

    async def get_content_for_twin(
        self,
        twin_id: UUID,
        user_id: UUID,
        limit: int = 50,
    ) -> List[TwinContent]:
        """Get all content generated by a twin."""
        from app.models.twin import TwinContentRecord

        from sqlalchemy import select
        result = await self.db.execute(
            select(TwinContentRecord).where(
                TwinContentRecord.twin_id == twin_id,
                TwinContentRecord.user_id == user_id,
            ).order_by(
                TwinContentRecord.created_at.desc()
            ).limit(limit)
        )
        records = result.scalars().all()

        return [self._record_to_content(r) for r in records]

    async def get_pipeline_status(
        self,
        content_id: UUID,
    ) -> Dict[str, Any]:
        """Get current pipeline status."""
        from app.models.twin import TwinContentRecord

        from sqlalchemy import select
        result = await self.db.execute(
            select(TwinContentRecord).where(
                TwinContentRecord.id == content_id,
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return {"error": "Content not found"}

        # Estimate remaining time
        remaining = None
        if record.status == "processing":
            if record.current_step == "voice_synthesis":
                remaining = 30  # ~30s for voice
            elif record.current_step == "video_generation":
                remaining = 120  # ~2min for video

        return {
            "content_id": str(record.id),
            "status": record.status,
            "current_step": record.current_step,
            "progress_percent": record.progress_percent,
            "estimated_remaining_seconds": remaining,
            "output_url": record.video_url or record.audio_url,
        }

    async def _save_content(self, content: TwinContent) -> None:
        """Save content to database."""
        from app.models.twin import TwinContentRecord

        record = TwinContentRecord(
            id=content.content_id,
            twin_id=content.twin_id,
            user_id=content.user_id,
            content_type=content.content_type,
            script=content.script,
            language=content.language,
            status=content.status,
            current_step=content.current_step,
            progress_percent=content.progress_percent,
        )

        self.db.add(record)
        await self.db.flush()

    async def _update_content(self, content: TwinContent) -> None:
        """Update content in database."""
        from app.models.twin import TwinContentRecord

        from sqlalchemy import select
        result = await self.db.execute(
            select(TwinContentRecord).where(
                TwinContentRecord.id == content.content_id
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.status = content.status
            record.current_step = content.current_step
            record.progress_percent = content.progress_percent
            record.video_url = content.video_url
            record.audio_url = content.audio_url
            record.heygen_video_id = content.heygen_video_id
            record.duration_seconds = content.duration_seconds
            record.resolution = content.resolution
            record.error = content.error
            record.completed_at = content.completed_at

            await self.db.flush()

    async def _increment_counters(
        self,
        twin: AITwin,
        content_type: str,
    ) -> None:
        """Increment twin usage counters."""
        from app.models.twin import AITwinRecord

        from sqlalchemy import select
        result = await self.db.execute(
            select(AITwinRecord).where(AITwinRecord.id == twin.twin_id)
        )
        record = result.scalar_one_or_none()

        if record:
            if content_type == "video":
                record.total_videos_generated = (
                    record.total_videos_generated or 0
                ) + 1
            else:
                record.total_audio_generated = (
                    record.total_audio_generated or 0
                ) + 1

            await self.db.flush()

    def _record_to_content(self, record: Any) -> TwinContent:
        """Convert database record to TwinContent."""
        return TwinContent(
            content_id=record.id,
            twin_id=record.twin_id,
            user_id=record.user_id,
            content_type=record.content_type,
            script=record.script,
            language=record.language,
            video_url=record.video_url,
            audio_url=record.audio_url,
            thumbnail_url=record.thumbnail_url,
            duration_seconds=record.duration_seconds,
            resolution=record.resolution,
            file_size=record.file_size,
            status=record.status,
            current_step=record.current_step,
            progress_percent=record.progress_percent or 0.0,
            error=record.error,
            heygen_video_id=record.heygen_video_id,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )
