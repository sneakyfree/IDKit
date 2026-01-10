"""
Podcast Generator Service

End-to-end podcast episode generation.
Topic → Script → Audio → Video → Distribution
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.ai_twin import AiTwin, VoiceConfig, AvatarConfig
from app.models.podcast import (
    Podcast,
    PodcastEpisode,
    PodcastClip,
    PodcastStatus,
)
from app.services.podcast.script_generator import PodcastScriptGenerator
from app.providers.elevenlabs.adapter import ElevenLabsVoiceProvider
from app.providers.heygen.adapter import HeyGenAvatarProvider
from app.providers.interfaces.voice_provider import VoiceSynthesisConfig
from app.providers.interfaces.avatar_provider import AvatarGenerationConfig, AvatarJobStatus
from app.utils.storage import storage_service

logger = logging.getLogger(__name__)


class PodcastGenerator:
    """
    End-to-end podcast episode generation.

    Orchestrates script generation, audio synthesis,
    video creation, and clip extraction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.script_generator = PodcastScriptGenerator(db)

    async def generate_episode(
        self,
        podcast_id: uuid.UUID,
        topic: str,
        user_id: uuid.UUID,
        style: str = "conversational",
        duration_target: int = 600,  # 10 minutes
        use_ai_twin: bool = False,
        ai_twin_id: Optional[uuid.UUID] = None,
        generate_video: bool = True,
        auto_generate_clips: bool = True,
    ) -> PodcastEpisode:
        """
        One-click episode generation.

        Args:
            podcast_id: Parent podcast ID
            topic: Episode topic
            user_id: Owner user ID
            style: Script style
            duration_target: Target duration in seconds
            use_ai_twin: Whether to use AI Twin for audio
            ai_twin_id: Specific AI Twin ID
            generate_video: Generate video version
            auto_generate_clips: Auto-extract clips

        Returns:
            Generated PodcastEpisode
        """
        # Verify podcast exists and belongs to user
        result = await self.db.execute(
            select(Podcast).where(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id,
            )
        )
        podcast = result.scalar_one_or_none()
        if not podcast:
            raise ValueError("Podcast not found")

        # Get next episode number
        episode_count = await self.db.execute(
            select(func.count(PodcastEpisode.id)).where(
                PodcastEpisode.podcast_id == podcast_id
            )
        )
        next_episode = (episode_count.scalar() or 0) + 1

        # Create episode in generating state
        episode = PodcastEpisode(
            podcast_id=podcast_id,
            user_id=user_id,
            title=f"Episode {next_episode}: {topic}",
            episode_number=next_episode,
            status=PodcastStatus.GENERATING.value,
            host_type="ai_twin" if use_ai_twin else "user",
            ai_twin_id=ai_twin_id,
            ai_generated=True,
            generation_prompt=topic,
        )
        self.db.add(episode)
        await self.db.flush()

        try:
            # Step 1: Generate script
            script_result = await self.script_generator.generate(
                topic=topic,
                style=style,
                duration_target=duration_target,
                brand_voice_id=podcast.brand_voice_id,
                include_intro=bool(podcast.intro_script),
                include_outro=bool(podcast.outro_script),
            )

            episode.script = script_result["content"]
            episode.duration_seconds = script_result["estimated_duration"]

            # Parse chapters from sections
            chapters = []
            current_time = 0
            for section in script_result["sections"]:
                # Estimate section duration based on word count
                section_words = len(section["content"].split())
                section_duration = int((section_words / 150) * 60)

                chapters.append({
                    "title": section["title"],
                    "start": current_time,
                    "end": current_time + section_duration,
                })
                current_time += section_duration

            episode.chapters = chapters

            # Step 2: Generate show notes
            episode.show_notes = await self.script_generator.generate_show_notes(
                script=script_result["content"],
                topic=topic,
            )

            # Step 3: Generate audio (if using AI Twin)
            if use_ai_twin and ai_twin_id:
                audio_result = await self._generate_audio(
                    script=script_result["content"],
                    ai_twin_id=ai_twin_id,
                )
                episode.audio_url = audio_result.get("audio_url")
                episode.duration_seconds = audio_result.get("duration")

            # Step 4: Generate video (if requested and audio exists)
            if generate_video and episode.audio_url:
                video_result = await self._generate_video(
                    audio_url=episode.audio_url,
                    script=script_result["content"],
                    ai_twin_id=ai_twin_id if use_ai_twin else None,
                )
                episode.video_url = video_result.get("video_url")
                episode.thumbnail_url = video_result.get("thumbnail_url")

            # Update status
            if use_ai_twin:
                episode.status = PodcastStatus.READY.value
            else:
                # Script ready, awaiting user recording
                episode.status = PodcastStatus.DRAFT.value

            await self.db.commit()
            await self.db.refresh(episode)

            # Step 5: Auto-generate clips (async task in production)
            if auto_generate_clips and episode.audio_url:
                await self.generate_clips(
                    episode_id=episode.id,
                    user_id=user_id,
                    clip_count=5,
                )

            return episode

        except Exception as e:
            episode.status = PodcastStatus.DRAFT.value
            await self.db.commit()
            raise

    async def generate_clips(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        clip_count: int = 5,
        clip_duration: int = 60,
    ) -> List[PodcastClip]:
        """
        Auto-extract best clips from an episode.

        Uses AI to identify high-value segments.
        """
        # Get episode
        result = await self.db.execute(
            select(PodcastEpisode).where(
                PodcastEpisode.id == episode_id,
                PodcastEpisode.user_id == user_id,
            )
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Episode not found")

        if not episode.script:
            raise ValueError("Episode has no script to extract clips from")

        # Analyze script for highlights
        highlights = await self._find_highlights(
            script=episode.script,
            transcript=episode.transcript,
            count=clip_count,
            clip_duration=clip_duration,
        )

        clips = []
        for i, highlight in enumerate(highlights):
            clip = PodcastClip(
                episode_id=episode_id,
                user_id=user_id,
                title=highlight.get("title", f"Clip {i + 1}"),
                description=highlight.get("description"),
                start_time_seconds=highlight.get("start", i * clip_duration),
                end_time_seconds=highlight.get("end", (i + 1) * clip_duration),
                quote_text=highlight.get("quote"),
                status=PodcastStatus.DRAFT.value,
            )
            self.db.add(clip)
            clips.append(clip)

        await self.db.commit()

        for clip in clips:
            await self.db.refresh(clip)

        return clips

    async def create_clip(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        start_time: int,
        end_time: int,
        title: Optional[str] = None,
    ) -> PodcastClip:
        """Manually create a clip from an episode."""
        # Verify episode
        result = await self.db.execute(
            select(PodcastEpisode).where(
                PodcastEpisode.id == episode_id,
                PodcastEpisode.user_id == user_id,
            )
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Episode not found")

        clip = PodcastClip(
            episode_id=episode_id,
            user_id=user_id,
            title=title or f"Clip from {episode.title}",
            start_time_seconds=start_time,
            end_time_seconds=end_time,
            status=PodcastStatus.DRAFT.value,
        )
        self.db.add(clip)
        await self.db.commit()
        await self.db.refresh(clip)

        return clip

    async def _generate_audio(
        self,
        script: str,
        ai_twin_id: uuid.UUID,
    ) -> dict:
        """
        Generate audio from script using AI Twin voice.

        Integrates with ElevenLabs for voice synthesis.
        """
        # Fetch the AI Twin with voice configuration
        result = await self.db.execute(
            select(AiTwin).options(
                selectinload(AiTwin.voice_config)
            ).where(AiTwin.id == ai_twin_id)
        )
        ai_twin = result.scalar_one_or_none()

        if not ai_twin:
            logger.warning(f"AI Twin {ai_twin_id} not found for audio generation")
            return {
                "audio_url": None,
                "duration": len(script.split()) // 150 * 60,
            }

        if not ai_twin.voice_id:
            logger.warning(f"AI Twin {ai_twin_id} has no cloned voice")
            return {
                "audio_url": None,
                "duration": len(script.split()) // 150 * 60,
            }

        # Initialize voice provider
        voice_provider = ElevenLabsVoiceProvider()

        # Build synthesis config from AI Twin's voice settings
        voice_config = ai_twin.voice_config
        synthesis_config = VoiceSynthesisConfig(
            voice_id=ai_twin.voice_id,
            text=script,
            stability=voice_config.stability if voice_config else 0.5,
            similarity_boost=voice_config.similarity_boost if voice_config else 0.75,
            style=voice_config.style if voice_config else 0.0,
            output_format="mp3_44100_128",
            extras={
                "model_id": voice_config.model_id if voice_config and voice_config.model_id else "eleven_multilingual_v2",
            },
        )

        try:
            # Generate audio via ElevenLabs
            synthesis_result = await voice_provider.synthesize_speech(synthesis_config)

            if not synthesis_result.audio_data:
                logger.error("ElevenLabs returned no audio data")
                return {
                    "audio_url": None,
                    "duration": len(script.split()) // 150 * 60,
                }

            # Upload audio to S3
            file_key = f"podcasts/episodes/{uuid.uuid4()}/audio.mp3"
            audio_url = await storage_service.upload_file(
                file_data=synthesis_result.audio_data,
                file_key=file_key,
                content_type="audio/mpeg",
                metadata={
                    "ai_twin_id": str(ai_twin_id),
                    "voice_id": ai_twin.voice_id,
                    "character_count": str(synthesis_result.character_count),
                },
            )

            logger.info(
                f"Generated audio for AI Twin {ai_twin_id}: "
                f"{synthesis_result.duration_seconds:.1f}s, "
                f"{synthesis_result.character_count} chars"
            )

            return {
                "audio_url": audio_url,
                "duration": synthesis_result.duration_seconds,
                "character_count": synthesis_result.character_count,
            }

        except Exception as e:
            logger.error(f"Audio generation failed for AI Twin {ai_twin_id}: {e}")
            return {
                "audio_url": None,
                "duration": len(script.split()) // 150 * 60,
                "error": str(e),
            }

    async def _generate_video(
        self,
        audio_url: str,
        script: str,
        ai_twin_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """
        Generate video from audio.

        Uses HeyGen for avatar video with AI Twin, or returns placeholder
        for waveform visualization (to be implemented with FFmpeg).
        """
        if not ai_twin_id:
            # No AI Twin - would generate waveform video
            # This could be implemented with FFmpeg in the future
            logger.info("No AI Twin specified, skipping avatar video generation")
            return {
                "video_url": None,
                "thumbnail_url": None,
            }

        # Fetch the AI Twin with avatar configuration
        result = await self.db.execute(
            select(AiTwin).options(
                selectinload(AiTwin.avatar_config)
            ).where(AiTwin.id == ai_twin_id)
        )
        ai_twin = result.scalar_one_or_none()

        if not ai_twin:
            logger.warning(f"AI Twin {ai_twin_id} not found for video generation")
            return {
                "video_url": None,
                "thumbnail_url": None,
            }

        if not ai_twin.avatar_id:
            logger.warning(f"AI Twin {ai_twin_id} has no avatar configured")
            return {
                "video_url": None,
                "thumbnail_url": None,
            }

        # Initialize avatar provider
        avatar_provider = HeyGenAvatarProvider()

        # Build generation config from AI Twin's avatar settings
        avatar_config = ai_twin.avatar_config
        generation_config = AvatarGenerationConfig(
            avatar_id=ai_twin.avatar_id,
            audio_url=audio_url,
            script=script,
            background_type=avatar_config.background_type if avatar_config else "color",
            background_value=avatar_config.background_value if avatar_config else "#1a1a2e",
            aspect_ratio=avatar_config.aspect_ratio if avatar_config else "16:9",
            resolution=avatar_config.resolution if avatar_config else "1080p",
            emotion="neutral",
        )

        try:
            # Start video generation job
            generation_result = await avatar_provider.generate_video(generation_config)

            if generation_result.status == AvatarJobStatus.FAILED:
                logger.error(
                    f"HeyGen video generation failed: {generation_result.error_message}"
                )
                return {
                    "video_url": None,
                    "thumbnail_url": None,
                    "error": generation_result.error_message,
                }

            # Poll for completion (with timeout)
            job_id = generation_result.job_id
            max_wait_seconds = 600  # 10 minutes max
            poll_interval = 10  # Check every 10 seconds
            elapsed = 0

            while elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                status_result = await avatar_provider.get_video_status(job_id)

                if status_result.status == AvatarJobStatus.COMPLETED:
                    logger.info(
                        f"Generated video for AI Twin {ai_twin_id}: "
                        f"{status_result.duration_seconds:.1f}s"
                    )
                    return {
                        "video_url": status_result.video_url,
                        "thumbnail_url": status_result.thumbnail_url,
                        "duration": status_result.duration_seconds,
                    }

                if status_result.status == AvatarJobStatus.FAILED:
                    logger.error(
                        f"HeyGen video job {job_id} failed: {status_result.error_message}"
                    )
                    return {
                        "video_url": None,
                        "thumbnail_url": None,
                        "error": status_result.error_message,
                    }

                logger.debug(
                    f"Video generation job {job_id} in progress: "
                    f"{status_result.progress}%"
                )

            # Timeout reached
            logger.warning(f"Video generation timed out after {max_wait_seconds}s")
            return {
                "video_url": None,
                "thumbnail_url": None,
                "error": "Video generation timed out",
                "job_id": job_id,  # Allow retry/polling later
            }

        except Exception as e:
            logger.error(f"Video generation failed for AI Twin {ai_twin_id}: {e}")
            return {
                "video_url": None,
                "thumbnail_url": None,
                "error": str(e),
            }

    async def _find_highlights(
        self,
        script: str,
        transcript: Optional[str],
        count: int,
        clip_duration: int,
    ) -> List[dict]:
        """
        Use AI to find the best clip-worthy moments.
        """
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        prompt = f"""Analyze this podcast script and identify the {count} most clip-worthy moments.

Script:
{script[:4000]}

For each moment, provide:
1. A catchy title (max 50 chars)
2. Brief description
3. The best quote from that segment
4. Approximate position (as percentage through the episode)

These clips will be used for TikTok, Reels, and Shorts, so look for:
- Surprising insights
- Quotable moments
- Emotional peaks
- Actionable advice
- Controversial or debate-worthy takes

Format as JSON array."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a podcast editor identifying viral-worthy clips.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        # Parse response
        import json

        try:
            content = response.choices[0].message.content
            # Try to extract JSON from response
            if "[" in content:
                json_start = content.index("[")
                json_end = content.rindex("]") + 1
                highlights = json.loads(content[json_start:json_end])
            else:
                highlights = []
        except (json.JSONDecodeError, ValueError):
            # Fallback to evenly spaced clips
            highlights = []

        # Convert percentages to timestamps
        total_duration = len(script.split()) // 150 * 60  # Estimate total duration

        result = []
        for i, h in enumerate(highlights[:count]):
            position = h.get("position", (i + 1) / (count + 1))
            if isinstance(position, str):
                position = float(position.strip("%")) / 100

            start = int(position * total_duration)
            result.append({
                "title": h.get("title", f"Highlight {i + 1}"),
                "description": h.get("description"),
                "quote": h.get("quote"),
                "start": max(0, start - clip_duration // 2),
                "end": min(total_duration, start + clip_duration // 2),
            })

        # Fill remaining slots if needed
        while len(result) < count:
            i = len(result)
            position = (i + 1) / (count + 1)
            start = int(position * total_duration)
            result.append({
                "title": f"Clip {i + 1}",
                "start": max(0, start - clip_duration // 2),
                "end": min(total_duration, start + clip_duration // 2),
            })

        return result
