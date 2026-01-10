"""
Media Transcoder

Video and audio transcoding with preset configurations for different platforms.
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.services.media.processor import MediaProcessor, media_processor

logger = logging.getLogger(__name__)


class TranscodePreset(str, Enum):
    """Transcoding presets for different platforms."""

    # Social Media Platforms
    YOUTUBE_HD = "youtube_hd"
    YOUTUBE_4K = "youtube_4k"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_STORIES = "instagram_stories"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"

    # Podcast
    PODCAST_AUDIO = "podcast_audio"
    PODCAST_VIDEO = "podcast_video"

    # General
    WEB_SD = "web_sd"
    WEB_HD = "web_hd"
    WEB_4K = "web_4k"
    MOBILE_LOW = "mobile_low"
    MOBILE_HIGH = "mobile_high"

    # Audio
    AUDIO_MP3_HIGH = "audio_mp3_high"
    AUDIO_MP3_MEDIUM = "audio_mp3_medium"
    AUDIO_AAC_HIGH = "audio_aac_high"
    AUDIO_WAV = "audio_wav"


@dataclass
class VideoPresetConfig:
    """Configuration for a video transcoding preset."""

    width: int
    height: int
    video_bitrate: str
    audio_bitrate: str
    fps: int
    video_codec: str
    audio_codec: str
    preset: str
    max_duration: Optional[int] = None  # seconds
    aspect_ratio: Optional[str] = None


@dataclass
class AudioPresetConfig:
    """Configuration for an audio transcoding preset."""

    bitrate: str
    sample_rate: int
    channels: int
    codec: str
    format: str


# Video preset configurations
VIDEO_PRESETS: dict[TranscodePreset, VideoPresetConfig] = {
    TranscodePreset.YOUTUBE_HD: VideoPresetConfig(
        width=1920,
        height=1080,
        video_bitrate="8M",
        audio_bitrate="320k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    ),
    TranscodePreset.YOUTUBE_4K: VideoPresetConfig(
        width=3840,
        height=2160,
        video_bitrate="35M",
        audio_bitrate="320k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    ),
    TranscodePreset.YOUTUBE_SHORTS: VideoPresetConfig(
        width=1080,
        height=1920,
        video_bitrate="5M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=60,
        aspect_ratio="9:16",
    ),
    TranscodePreset.TIKTOK: VideoPresetConfig(
        width=1080,
        height=1920,
        video_bitrate="4M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=180,  # 3 minutes
        aspect_ratio="9:16",
    ),
    TranscodePreset.INSTAGRAM_FEED: VideoPresetConfig(
        width=1080,
        height=1080,
        video_bitrate="3.5M",
        audio_bitrate="128k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=60,
        aspect_ratio="1:1",
    ),
    TranscodePreset.INSTAGRAM_REELS: VideoPresetConfig(
        width=1080,
        height=1920,
        video_bitrate="4M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=90,
        aspect_ratio="9:16",
    ),
    TranscodePreset.INSTAGRAM_STORIES: VideoPresetConfig(
        width=1080,
        height=1920,
        video_bitrate="3M",
        audio_bitrate="128k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=15,
        aspect_ratio="9:16",
    ),
    TranscodePreset.TWITTER: VideoPresetConfig(
        width=1280,
        height=720,
        video_bitrate="5M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=140,
    ),
    TranscodePreset.LINKEDIN: VideoPresetConfig(
        width=1920,
        height=1080,
        video_bitrate="8M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=600,  # 10 minutes
    ),
    TranscodePreset.FACEBOOK: VideoPresetConfig(
        width=1280,
        height=720,
        video_bitrate="4M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        max_duration=240,  # 4 minutes
    ),
    TranscodePreset.PODCAST_VIDEO: VideoPresetConfig(
        width=1920,
        height=1080,
        video_bitrate="4M",
        audio_bitrate="256k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    ),
    TranscodePreset.WEB_SD: VideoPresetConfig(
        width=854,
        height=480,
        video_bitrate="1.5M",
        audio_bitrate="128k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="fast",
    ),
    TranscodePreset.WEB_HD: VideoPresetConfig(
        width=1280,
        height=720,
        video_bitrate="3M",
        audio_bitrate="192k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    ),
    TranscodePreset.WEB_4K: VideoPresetConfig(
        width=3840,
        height=2160,
        video_bitrate="20M",
        audio_bitrate="256k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="slow",
    ),
    TranscodePreset.MOBILE_LOW: VideoPresetConfig(
        width=640,
        height=360,
        video_bitrate="800k",
        audio_bitrate="96k",
        fps=24,
        video_codec="libx264",
        audio_codec="aac",
        preset="fast",
    ),
    TranscodePreset.MOBILE_HIGH: VideoPresetConfig(
        width=1280,
        height=720,
        video_bitrate="2.5M",
        audio_bitrate="128k",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    ),
}

# Audio preset configurations
AUDIO_PRESETS: dict[TranscodePreset, AudioPresetConfig] = {
    TranscodePreset.PODCAST_AUDIO: AudioPresetConfig(
        bitrate="192k",
        sample_rate=44100,
        channels=2,
        codec="libmp3lame",
        format="mp3",
    ),
    TranscodePreset.AUDIO_MP3_HIGH: AudioPresetConfig(
        bitrate="320k",
        sample_rate=48000,
        channels=2,
        codec="libmp3lame",
        format="mp3",
    ),
    TranscodePreset.AUDIO_MP3_MEDIUM: AudioPresetConfig(
        bitrate="192k",
        sample_rate=44100,
        channels=2,
        codec="libmp3lame",
        format="mp3",
    ),
    TranscodePreset.AUDIO_AAC_HIGH: AudioPresetConfig(
        bitrate="256k",
        sample_rate=48000,
        channels=2,
        codec="aac",
        format="m4a",
    ),
    TranscodePreset.AUDIO_WAV: AudioPresetConfig(
        bitrate="1411k",  # CD quality
        sample_rate=44100,
        channels=2,
        codec="pcm_s16le",
        format="wav",
    ),
}


class VideoTranscoder:
    """
    Video transcoder with platform-specific presets.

    Provides easy transcoding for different social media platforms
    and web delivery formats.
    """

    def __init__(self, processor: Optional[MediaProcessor] = None):
        self.processor = processor or media_processor

    async def transcode(
        self,
        input_path: str,
        preset: TranscodePreset,
        output_path: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Transcode video to a preset format.

        Args:
            input_path: Path to input video
            preset: Transcoding preset
            output_path: Path for output video
            progress_callback: Optional callback for progress updates

        Returns:
            Path to transcoded video
        """
        if preset not in VIDEO_PRESETS:
            raise ValueError(f"Unknown video preset: {preset}")

        config = VIDEO_PRESETS[preset]

        if output_path is None:
            import tempfile

            output_path = os.path.join(
                tempfile.gettempdir(),
                f"transcoded_{uuid.uuid4().hex}.mp4",
            )

        # Build FFmpeg command
        cmd = await self._build_transcode_command(input_path, output_path, config)

        # Run transcoding
        await self._run_transcode(cmd, progress_callback)

        return output_path

    async def transcode_for_platforms(
        self,
        input_path: str,
        platforms: list[str],
        output_dir: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Transcode video for multiple platforms.

        Args:
            input_path: Path to input video
            platforms: List of platform names
            output_dir: Directory for output files

        Returns:
            Dict mapping platform name to output path
        """
        import tempfile

        if output_dir is None:
            output_dir = tempfile.mkdtemp()

        platform_to_preset = {
            "youtube": TranscodePreset.YOUTUBE_HD,
            "youtube_shorts": TranscodePreset.YOUTUBE_SHORTS,
            "tiktok": TranscodePreset.TIKTOK,
            "instagram": TranscodePreset.INSTAGRAM_FEED,
            "instagram_reels": TranscodePreset.INSTAGRAM_REELS,
            "instagram_stories": TranscodePreset.INSTAGRAM_STORIES,
            "twitter": TranscodePreset.TWITTER,
            "linkedin": TranscodePreset.LINKEDIN,
            "facebook": TranscodePreset.FACEBOOK,
        }

        results = {}
        tasks = []

        for platform in platforms:
            preset = platform_to_preset.get(platform.lower())
            if preset:
                output_path = os.path.join(output_dir, f"{platform}.mp4")
                tasks.append(self._transcode_task(input_path, preset, output_path, platform))

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for platform, result in zip(platforms, completed):
            if isinstance(result, Exception):
                logger.error(f"Transcoding failed for {platform}: {result}")
                results[platform] = None
            else:
                results[platform] = result

        return results

    async def _transcode_task(
        self,
        input_path: str,
        preset: TranscodePreset,
        output_path: str,
        platform: str,
    ) -> str:
        """Internal task for parallel transcoding."""
        return await self.transcode(input_path, preset, output_path)

    async def _build_transcode_command(
        self,
        input_path: str,
        output_path: str,
        config: VideoPresetConfig,
    ) -> list[str]:
        """Build FFmpeg command from config."""
        from shutil import which

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        # Build filter string for scaling
        if config.aspect_ratio:
            # Force aspect ratio with padding
            filter_str = (
                f"scale={config.width}:{config.height}:force_original_aspect_ratio=decrease,"
                f"pad={config.width}:{config.height}:(ow-iw)/2:(oh-ih)/2"
            )
        else:
            filter_str = f"scale={config.width}:{config.height}:force_original_aspect_ratio=decrease"

        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-vf",
            filter_str,
            "-c:v",
            config.video_codec,
            "-b:v",
            config.video_bitrate,
            "-r",
            str(config.fps),
            "-c:a",
            config.audio_codec,
            "-b:a",
            config.audio_bitrate,
            "-preset",
            config.preset,
            "-movflags",
            "+faststart",  # Enable streaming
        ]

        # Add duration limit if specified
        if config.max_duration:
            cmd.extend(["-t", str(config.max_duration)])

        cmd.append(output_path)
        return cmd

    async def _run_transcode(
        self,
        cmd: list[str],
        progress_callback: Optional[callable] = None,
    ) -> None:
        """Run FFmpeg transcoding command."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Transcoding failed: {stderr.decode()}")


class AudioTranscoder:
    """
    Audio transcoder with preset configurations.

    Provides easy transcoding for podcasts and audio delivery.
    """

    def __init__(self, processor: Optional[MediaProcessor] = None):
        self.processor = processor or media_processor

    async def transcode(
        self,
        input_path: str,
        preset: TranscodePreset,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Transcode audio to a preset format.

        Args:
            input_path: Path to input audio
            preset: Transcoding preset
            output_path: Path for output audio

        Returns:
            Path to transcoded audio
        """
        if preset not in AUDIO_PRESETS:
            raise ValueError(f"Unknown audio preset: {preset}")

        config = AUDIO_PRESETS[preset]

        if output_path is None:
            import tempfile

            output_path = os.path.join(
                tempfile.gettempdir(),
                f"transcoded_{uuid.uuid4().hex}.{config.format}",
            )

        cmd = await self._build_transcode_command(input_path, output_path, config)
        await self._run_transcode(cmd)

        return output_path

    async def normalize_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_loudness: float = -16.0,  # LUFS
    ) -> str:
        """
        Normalize audio loudness.

        Args:
            input_path: Path to input audio
            output_path: Path for output audio
            target_loudness: Target loudness in LUFS

        Returns:
            Path to normalized audio
        """
        from shutil import which

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        if output_path is None:
            import tempfile

            ext = os.path.splitext(input_path)[1]
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"normalized_{uuid.uuid4().hex}{ext}",
            )

        # Use loudnorm filter
        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-af",
            f"loudnorm=I={target_loudness}:TP=-1.5:LRA=11",
            output_path,
        ]

        await self._run_transcode(cmd)
        return output_path

    async def remove_silence(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        threshold_db: float = -50.0,
        min_duration: float = 0.5,
    ) -> str:
        """
        Remove silence from audio.

        Args:
            input_path: Path to input audio
            output_path: Path for output audio
            threshold_db: Silence threshold in dB
            min_duration: Minimum silence duration to remove

        Returns:
            Path to processed audio
        """
        from shutil import which

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        if output_path is None:
            import tempfile

            ext = os.path.splitext(input_path)[1]
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"nosilence_{uuid.uuid4().hex}{ext}",
            )

        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-af",
            f"silenceremove=start_periods=1:start_duration={min_duration}:start_threshold={threshold_db}dB:"
            f"detection=peak,aformat=dblp,areverse,"
            f"silenceremove=start_periods=1:start_duration={min_duration}:start_threshold={threshold_db}dB:"
            f"detection=peak,aformat=dblp,areverse",
            output_path,
        ]

        await self._run_transcode(cmd)
        return output_path

    async def add_fade(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        fade_in: float = 0.5,
        fade_out: float = 0.5,
    ) -> str:
        """
        Add fade in/out to audio.

        Args:
            input_path: Path to input audio
            output_path: Path for output audio
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            Path to processed audio
        """
        from shutil import which

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        if output_path is None:
            import tempfile

            ext = os.path.splitext(input_path)[1]
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"faded_{uuid.uuid4().hex}{ext}",
            )

        # Get duration for fade out
        metadata = await self.processor.get_audio_metadata(input_path)
        fade_out_start = metadata.duration - fade_out

        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-af",
            f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}",
            output_path,
        ]

        await self._run_transcode(cmd)
        return output_path

    async def _build_transcode_command(
        self,
        input_path: str,
        output_path: str,
        config: AudioPresetConfig,
    ) -> list[str]:
        """Build FFmpeg command from config."""
        from shutil import which

        ffmpeg_path = which("ffmpeg") or "ffmpeg"

        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-c:a",
            config.codec,
            "-b:a",
            config.bitrate,
            "-ar",
            str(config.sample_rate),
            "-ac",
            str(config.channels),
            output_path,
        ]

        return cmd

    async def _run_transcode(self, cmd: list[str]) -> None:
        """Run FFmpeg transcoding command."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Audio transcoding failed: {stderr.decode()}")


# Singleton instances
video_transcoder = VideoTranscoder()
audio_transcoder = AudioTranscoder()
