"""
Podcast Clip Extractor Service

Smart clip extraction using AI to identify viral-worthy moments
and generate social media optimized video clips.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.podcast import (
    PodcastEpisode,
    PodcastClip,
    PodcastStatus,
)


class ClipHighlight:
    """Represents a highlight segment identified for clipping."""

    def __init__(
        self,
        title: str,
        start_seconds: int,
        end_seconds: int,
        quote: Optional[str] = None,
        description: Optional[str] = None,
        virality_score: float = 0.0,
        tags: Optional[List[str]] = None,
    ):
        self.title = title
        self.start_seconds = start_seconds
        self.end_seconds = end_seconds
        self.quote = quote
        self.description = description
        self.virality_score = virality_score
        self.tags = tags or []

    @property
    def duration(self) -> int:
        return self.end_seconds - self.start_seconds


class PodcastClipExtractor:
    """
    Smart clip extraction service.

    Uses AI to analyze podcast transcripts and identify
    the best moments for short-form social media clips.
    """

    # Ideal clip durations per platform
    PLATFORM_DURATIONS = {
        "tiktok": (15, 60),    # 15-60 seconds
        "reels": (15, 90),     # 15-90 seconds
        "shorts": (15, 60),    # 15-60 seconds
        "twitter": (15, 140),  # 15-140 seconds
        "linkedin": (30, 120), # 30-120 seconds
    }

    # Content types that make good clips
    CLIP_TYPES = [
        "surprising_insight",
        "quotable_moment",
        "emotional_peak",
        "actionable_advice",
        "controversial_take",
        "story_climax",
        "funny_moment",
        "expertise_display",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    async def extract_clips(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        target_count: int = 5,
        target_platforms: Optional[List[str]] = None,
        min_duration: int = 15,
        max_duration: int = 60,
    ) -> List[PodcastClip]:
        """
        Extract best clips from a podcast episode.

        Args:
            episode_id: Episode to extract clips from
            user_id: Owner user ID
            target_count: Number of clips to extract
            target_platforms: Target social platforms
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds

        Returns:
            List of created PodcastClip records
        """
        if target_platforms is None:
            target_platforms = ["tiktok", "reels", "shorts"]

        # Get episode with script/transcript
        result = await self.db.execute(
            select(PodcastEpisode).where(
                PodcastEpisode.id == episode_id,
                PodcastEpisode.user_id == user_id,
            )
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Episode not found")

        # Use transcript if available, otherwise use script
        content = episode.transcript or episode.script
        if not content:
            raise ValueError("Episode has no content to extract clips from")

        # Analyze content for highlights
        highlights = await self._analyze_content(
            content=content,
            episode_duration=episode.duration_seconds or self._estimate_duration(content),
            target_count=target_count,
            min_duration=min_duration,
            max_duration=max_duration,
        )

        # Create clip records
        clips = []
        for highlight in highlights:
            clip = PodcastClip(
                episode_id=episode_id,
                user_id=user_id,
                title=highlight.title,
                description=highlight.description,
                start_time_seconds=highlight.start_seconds,
                end_time_seconds=highlight.end_seconds,
                quote_text=highlight.quote,
                target_platforms=target_platforms,
                status=PodcastStatus.DRAFT.value,
            )
            self.db.add(clip)
            clips.append(clip)

        await self.db.commit()

        for clip in clips:
            await self.db.refresh(clip)

        return clips

    async def _analyze_content(
        self,
        content: str,
        episode_duration: int,
        target_count: int,
        min_duration: int,
        max_duration: int,
    ) -> List[ClipHighlight]:
        """
        Use AI to analyze content and identify clip-worthy moments.
        """
        client = await self._get_llm_client()

        prompt = f"""Analyze this podcast content and identify the {target_count} most clip-worthy moments for social media.

CONTENT:
{content[:6000]}

REQUIREMENTS:
- Each clip should be {min_duration}-{max_duration} seconds
- Episode total duration: ~{episode_duration} seconds
- Target platforms: TikTok, Instagram Reels, YouTube Shorts

For each clip moment, identify:
1. Title: Catchy, scroll-stopping title (max 50 chars)
2. Quote: The best verbatim quote from this segment
3. Description: Brief context (1-2 sentences)
4. Position: Approximate percentage through the episode (0-100)
5. Type: One of [{', '.join(self.CLIP_TYPES)}]
6. Virality_score: 1-10 rating of how shareable this clip would be

CRITERIA FOR GOOD CLIPS:
- Surprising insights or counterintuitive takes
- Quotable one-liners or soundbites
- Emotional moments (humor, inspiration, controversy)
- Actionable advice in bite-sized format
- Story climaxes or reveals
- Expert knowledge displays

Return as JSON array:
[
  {{
    "title": "...",
    "quote": "...",
    "description": "...",
    "position": 25,
    "type": "surprising_insight",
    "virality_score": 8
  }}
]"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral content expert who identifies the most shareable moments from podcasts. You have deep knowledge of what performs well on TikTok, Reels, and Shorts.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        # Parse response
        import json

        highlights = []
        try:
            content_response = response.choices[0].message.content
            # Extract JSON from response
            if "[" in content_response:
                json_start = content_response.index("[")
                json_end = content_response.rindex("]") + 1
                raw_highlights = json.loads(content_response[json_start:json_end])

                for h in raw_highlights:
                    position = h.get("position", 50)
                    if isinstance(position, str):
                        position = float(position.strip("%"))

                    # Convert position to timestamps
                    center_time = int((position / 100) * episode_duration)
                    clip_duration = (min_duration + max_duration) // 2

                    highlight = ClipHighlight(
                        title=h.get("title", "Untitled Clip"),
                        start_seconds=max(0, center_time - clip_duration // 2),
                        end_seconds=min(episode_duration, center_time + clip_duration // 2),
                        quote=h.get("quote"),
                        description=h.get("description"),
                        virality_score=float(h.get("virality_score", 5)),
                        tags=[h.get("type", "general")],
                    )
                    highlights.append(highlight)

        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback to evenly distributed clips
            pass

        # Ensure we have enough clips (fill with evenly spaced if needed)
        while len(highlights) < target_count:
            i = len(highlights)
            position = (i + 1) / (target_count + 1)
            center_time = int(position * episode_duration)
            clip_duration = (min_duration + max_duration) // 2

            highlights.append(ClipHighlight(
                title=f"Highlight {i + 1}",
                start_seconds=max(0, center_time - clip_duration // 2),
                end_seconds=min(episode_duration, center_time + clip_duration // 2),
                virality_score=5.0,
            ))

        # Sort by virality score (highest first)
        highlights.sort(key=lambda h: h.virality_score, reverse=True)

        return highlights[:target_count]

    async def generate_clip_assets(
        self,
        clip_id: uuid.UUID,
        user_id: uuid.UUID,
        include_captions: bool = True,
        caption_style: str = "animated",
    ) -> PodcastClip:
        """
        Generate video/audio assets for a clip.

        Args:
            clip_id: Clip to generate assets for
            user_id: Owner user ID
            include_captions: Add burned-in captions
            caption_style: Caption animation style

        Returns:
            Updated clip with asset URLs
        """
        # Get clip with episode
        result = await self.db.execute(
            select(PodcastClip).where(
                PodcastClip.id == clip_id,
                PodcastClip.user_id == user_id,
            )
        )
        clip = result.scalar_one_or_none()
        if not clip:
            raise ValueError("Clip not found")

        # Get parent episode
        result = await self.db.execute(
            select(PodcastEpisode).where(PodcastEpisode.id == clip.episode_id)
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Parent episode not found")

        # Generate audio clip
        if episode.audio_url:
            audio_url = await self._extract_audio_segment(
                source_url=episode.audio_url,
                start_seconds=clip.start_time_seconds,
                end_seconds=clip.end_time_seconds,
            )
            clip.audio_url = audio_url

        # Generate video clip
        if episode.video_url:
            video_url = await self._extract_video_segment(
                source_url=episode.video_url,
                start_seconds=clip.start_time_seconds,
                end_seconds=clip.end_time_seconds,
                add_captions=include_captions,
                caption_style=caption_style,
            )
            clip.video_url = video_url

        # Generate captions from transcript/script
        if include_captions:
            captions = await self._generate_captions(
                content=episode.transcript or episode.script,
                start_seconds=clip.start_time_seconds,
                end_seconds=clip.end_time_seconds,
            )
            clip.captions = captions

        # Generate thumbnail
        if episode.video_url or episode.thumbnail_url:
            thumbnail_url = await self._generate_thumbnail(
                video_url=episode.video_url,
                fallback_url=episode.thumbnail_url,
                timestamp=clip.start_time_seconds + 5,
            )
            clip.thumbnail_url = thumbnail_url

        clip.status = PodcastStatus.READY.value
        await self.db.commit()
        await self.db.refresh(clip)

        return clip

    async def _extract_audio_segment(
        self,
        source_url: str,
        start_seconds: int,
        end_seconds: int,
    ) -> Optional[str]:
        """
        Extract audio segment from source file.

        Downloads source, extracts segment with FFmpeg, uploads to S3.
        """
        import tempfile
        import os
        import aiohttp
        from app.services.media.processor import media_processor
        from app.utils.storage import storage_service

        try:
            # Download source audio to temp file
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download audio: {response.status}")
                        return None

                    # Determine file extension from content-type or URL
                    content_type = response.headers.get("Content-Type", "")
                    if "mp3" in content_type or source_url.endswith(".mp3"):
                        ext = ".mp3"
                    elif "wav" in content_type or source_url.endswith(".wav"):
                        ext = ".wav"
                    elif "m4a" in content_type or source_url.endswith(".m4a"):
                        ext = ".m4a"
                    else:
                        ext = ".mp3"

                    # Create temp file for source
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_src:
                        tmp_src.write(await response.read())
                        source_path = tmp_src.name

            # Extract segment using MediaProcessor
            clip_path = await media_processor.clip_audio(
                audio_path=source_path,
                start_time=float(start_seconds),
                end_time=float(end_seconds),
            )

            # Upload to S3
            clip_id = uuid.uuid4().hex
            s3_key = f"podcast-clips/audio/{clip_id}{ext}"

            with open(clip_path, "rb") as f:
                clip_url = await storage_service.upload_file(
                    file=f,
                    key=s3_key,
                    content_type=f"audio/{ext[1:]}",
                )

            # Cleanup temp files
            os.unlink(source_path)
            os.unlink(clip_path)

            return clip_url

        except Exception as e:
            logger.error(f"Audio segment extraction failed: {e}")
            return None

    async def _extract_video_segment(
        self,
        source_url: str,
        start_seconds: int,
        end_seconds: int,
        add_captions: bool = True,
        caption_style: str = "animated",
    ) -> Optional[str]:
        """
        Extract and process video segment.

        Includes optional caption burning with style.
        For social-optimized clips:
        - Crop to 9:16 aspect ratio
        - Add animated captions
        - Enhance audio
        """
        import tempfile
        import os
        import aiohttp
        from app.services.media.processor import media_processor
        from app.utils.storage import storage_service

        try:
            # Download source video to temp file
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download video: {response.status}")
                        return None

                    # Determine file extension
                    content_type = response.headers.get("Content-Type", "")
                    if "mp4" in content_type or source_url.endswith(".mp4"):
                        ext = ".mp4"
                    elif "webm" in content_type or source_url.endswith(".webm"):
                        ext = ".webm"
                    elif "mov" in content_type or source_url.endswith(".mov"):
                        ext = ".mov"
                    else:
                        ext = ".mp4"

                    # Create temp file for source
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_src:
                        tmp_src.write(await response.read())
                        source_path = tmp_src.name

            temp_files = [source_path]

            # Step 1: Extract clip segment
            clip_path = await media_processor.clip_video(
                video_path=source_path,
                start_time=float(start_seconds),
                end_time=float(end_seconds),
            )
            temp_files.append(clip_path)

            # Step 2: Resize to 9:16 vertical format for social media
            # TikTok/Reels/Shorts optimal: 1080x1920
            vertical_path = await media_processor.resize_video(
                video_path=clip_path,
                width=1080,
                height=1920,
                maintain_aspect=True,
            )
            temp_files.append(vertical_path)

            final_path = vertical_path

            # Step 3: Add captions if requested and available
            if add_captions:
                # Generate captions for this segment
                captions_content = await self._generate_captions(
                    content="",  # Will be replaced with actual transcript
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                )

                if captions_content:
                    # Write captions to temp SRT file
                    with tempfile.NamedTemporaryFile(
                        suffix=".srt", delete=False, mode="w"
                    ) as tmp_srt:
                        tmp_srt.write(captions_content)
                        srt_path = tmp_srt.name
                    temp_files.append(srt_path)

                    # Define caption style based on style parameter
                    style_map = {
                        "animated": "FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1",
                        "bold": "FontName=Impact,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3",
                        "minimal": "FontName=Helvetica,FontSize=20,PrimaryColour=&H00FFFFFF,BorderStyle=0",
                        "karaoke": "FontName=Arial,FontSize=26,PrimaryColour=&H0000FFFF,SecondaryColour=&H00FFFFFF,BorderStyle=1",
                    }
                    style = style_map.get(caption_style, style_map["animated"])

                    # Burn subtitles into video
                    subtitled_path = await media_processor.add_subtitles(
                        video_path=vertical_path,
                        subtitles_path=srt_path,
                        style=style,
                    )
                    temp_files.append(subtitled_path)
                    final_path = subtitled_path

            # Upload to S3
            clip_id = uuid.uuid4().hex
            s3_key = f"podcast-clips/video/{clip_id}.mp4"

            with open(final_path, "rb") as f:
                clip_url = await storage_service.upload_file(
                    file=f,
                    key=s3_key,
                    content_type="video/mp4",
                )

            # Cleanup all temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

            return clip_url

        except Exception as e:
            logger.error(f"Video segment extraction failed: {e}")
            return None

    async def _generate_captions(
        self,
        content: str,
        start_seconds: int,
        end_seconds: int,
    ) -> Optional[str]:
        """
        Generate SRT/VTT captions for the clip segment.
        """
        if not content:
            return None

        # Estimate which portion of content corresponds to clip
        words = content.split()
        total_duration = self._estimate_duration(content)

        words_per_second = len(words) / total_duration if total_duration > 0 else 2.5
        start_word = int(start_seconds * words_per_second)
        end_word = int(end_seconds * words_per_second)

        clip_words = words[start_word:end_word]

        # Generate simple SRT format
        # In production, use Whisper for accurate timestamps
        srt_lines = []
        chunk_size = 8  # words per caption
        clip_duration = end_seconds - start_seconds

        for i in range(0, len(clip_words), chunk_size):
            chunk = clip_words[i:i + chunk_size]
            caption_text = " ".join(chunk)

            # Calculate timing
            start_time = (i / len(clip_words)) * clip_duration
            end_time = min(((i + chunk_size) / len(clip_words)) * clip_duration, clip_duration)

            srt_lines.append(f"{len(srt_lines) + 1}")
            srt_lines.append(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}")
            srt_lines.append(caption_text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def _generate_thumbnail(
        self,
        video_url: Optional[str],
        fallback_url: Optional[str],
        timestamp: int,
    ) -> Optional[str]:
        """
        Generate thumbnail for clip.

        Extracts frame from video at specified timestamp, or uses fallback.
        """
        import tempfile
        import os
        import aiohttp
        from app.services.media.processor import media_processor
        from app.utils.storage import storage_service

        # If no video URL, return fallback
        if not video_url:
            return fallback_url

        try:
            # Download video to temp file
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to download video for thumbnail: {response.status}")
                        return fallback_url

                    # Determine file extension
                    content_type = response.headers.get("Content-Type", "")
                    if "mp4" in content_type or video_url.endswith(".mp4"):
                        ext = ".mp4"
                    elif "webm" in content_type or video_url.endswith(".webm"):
                        ext = ".webm"
                    elif "mov" in content_type or video_url.endswith(".mov"):
                        ext = ".mov"
                    else:
                        ext = ".mp4"

                    # Create temp file for source
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_src:
                        tmp_src.write(await response.read())
                        source_path = tmp_src.name

            # Generate thumbnail at specified timestamp
            # Use 720x1280 for vertical social media thumbnails
            thumbnail_path = await media_processor.generate_thumbnail(
                video_path=source_path,
                timestamp=float(timestamp),
                width=720,
                height=1280,
            )

            # Upload to S3
            thumb_id = uuid.uuid4().hex
            s3_key = f"podcast-clips/thumbnails/{thumb_id}.jpg"

            with open(thumbnail_path, "rb") as f:
                thumb_url = await storage_service.upload_file(
                    file=f,
                    key=s3_key,
                    content_type="image/jpeg",
                )

            # Cleanup temp files
            os.unlink(source_path)
            os.unlink(thumbnail_path)

            return thumb_url

        except Exception as e:
            logger.warning(f"Thumbnail generation failed, using fallback: {e}")
            return fallback_url

    def _estimate_duration(self, content: str) -> int:
        """Estimate duration from word count (150 wpm average)."""
        words = len(content.split())
        return int((words / 150) * 60)

    async def suggest_clip_titles(
        self,
        clip_id: uuid.UUID,
        user_id: uuid.UUID,
        count: int = 5,
    ) -> List[str]:
        """
        Generate alternative title suggestions for a clip.
        """
        result = await self.db.execute(
            select(PodcastClip).where(
                PodcastClip.id == clip_id,
                PodcastClip.user_id == user_id,
            )
        )
        clip = result.scalar_one_or_none()
        if not clip:
            raise ValueError("Clip not found")

        client = await self._get_llm_client()

        prompt = f"""Generate {count} alternative, scroll-stopping titles for this podcast clip.

Current title: {clip.title or 'Untitled'}
Quote: {clip.quote_text or 'N/A'}
Description: {clip.description or 'N/A'}

Requirements:
- Max 50 characters each
- Curiosity-inducing or controversial
- Works for TikTok/Reels/Shorts
- Avoid clickbait that doesn't deliver

Return as JSON array of strings."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral content copywriter specializing in short-form video titles.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.8,
        )

        import json
        try:
            content = response.choices[0].message.content
            if "[" in content:
                json_start = content.index("[")
                json_end = content.rindex("]") + 1
                titles = json.loads(content[json_start:json_end])
                return titles[:count]
        except (json.JSONDecodeError, ValueError):
            pass

        return [clip.title or "Untitled"] * count
