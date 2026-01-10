"""
Media Processor

Core media processing utilities using FFmpeg for video/audio analysis and manipulation.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video file metadata."""

    duration: float  # seconds
    width: int
    height: int
    fps: float
    bitrate: int  # bits per second
    codec: str
    format: str
    file_size: int
    has_audio: bool
    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_channels: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    rotation: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def aspect_ratio(self) -> str:
        """Get aspect ratio as string."""
        from math import gcd

        divisor = gcd(self.width, self.height)
        return f"{self.width // divisor}:{self.height // divisor}"

    @property
    def resolution(self) -> str:
        """Get resolution string."""
        return f"{self.width}x{self.height}"

    @property
    def duration_formatted(self) -> str:
        """Get duration as HH:MM:SS."""
        return str(timedelta(seconds=int(self.duration)))


@dataclass
class AudioMetadata:
    """Audio file metadata."""

    duration: float  # seconds
    codec: str
    bitrate: int
    channels: int
    sample_rate: int
    format: str
    file_size: int
    extra: dict = field(default_factory=dict)

    @property
    def duration_formatted(self) -> str:
        """Get duration as HH:MM:SS."""
        return str(timedelta(seconds=int(self.duration)))


@dataclass
class ImageMetadata:
    """Image file metadata."""

    width: int
    height: int
    format: str
    file_size: int
    color_space: Optional[str] = None
    has_alpha: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def aspect_ratio(self) -> str:
        """Get aspect ratio as string."""
        from math import gcd

        divisor = gcd(self.width, self.height)
        return f"{self.width // divisor}:{self.height // divisor}"


class MediaProcessor:
    """
    Media processing service using FFmpeg.

    Features:
    - Video/audio metadata extraction
    - Thumbnail generation
    - Video clipping and trimming
    - Audio extraction
    - Waveform generation
    - Format conversion
    - Resolution scaling
    """

    def __init__(self):
        self._ffmpeg_path = self._find_ffmpeg()
        self._ffprobe_path = self._find_ffprobe()
        self._temp_dir = tempfile.gettempdir()

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable."""
        path = shutil.which("ffmpeg")
        if not path:
            logger.warning("FFmpeg not found in PATH")
            return "ffmpeg"
        return path

    def _find_ffprobe(self) -> str:
        """Find FFprobe executable."""
        path = shutil.which("ffprobe")
        if not path:
            logger.warning("FFprobe not found in PATH")
            return "ffprobe"
        return path

    @property
    def is_available(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                [self._ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception:
            return False

    async def get_video_metadata(self, file_path: str) -> VideoMetadata:
        """Extract metadata from a video file."""
        probe_data = await self._probe_file(file_path)

        video_stream = next(
            (s for s in probe_data.get("streams", []) if s["codec_type"] == "video"),
            None,
        )
        audio_stream = next(
            (s for s in probe_data.get("streams", []) if s["codec_type"] == "audio"),
            None,
        )
        format_data = probe_data.get("format", {})

        if not video_stream:
            raise ValueError("No video stream found")

        # Parse FPS
        fps_parts = video_stream.get("r_frame_rate", "0/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 0

        # Get rotation from side data
        rotation = 0
        for side_data in video_stream.get("side_data_list", []):
            if "rotation" in side_data:
                rotation = int(side_data["rotation"])

        metadata = VideoMetadata(
            duration=float(format_data.get("duration", 0)),
            width=video_stream.get("width", 0),
            height=video_stream.get("height", 0),
            fps=round(fps, 2),
            bitrate=int(format_data.get("bit_rate", 0)),
            codec=video_stream.get("codec_name", "unknown"),
            format=format_data.get("format_name", "unknown"),
            file_size=int(format_data.get("size", 0)),
            has_audio=audio_stream is not None,
            rotation=rotation,
        )

        if audio_stream:
            metadata.audio_codec = audio_stream.get("codec_name")
            metadata.audio_bitrate = int(audio_stream.get("bit_rate", 0))
            metadata.audio_channels = audio_stream.get("channels")
            metadata.audio_sample_rate = int(audio_stream.get("sample_rate", 0))

        return metadata

    async def get_audio_metadata(self, file_path: str) -> AudioMetadata:
        """Extract metadata from an audio file."""
        probe_data = await self._probe_file(file_path)

        audio_stream = next(
            (s for s in probe_data.get("streams", []) if s["codec_type"] == "audio"),
            None,
        )
        format_data = probe_data.get("format", {})

        if not audio_stream:
            raise ValueError("No audio stream found")

        return AudioMetadata(
            duration=float(format_data.get("duration", 0)),
            codec=audio_stream.get("codec_name", "unknown"),
            bitrate=int(audio_stream.get("bit_rate", format_data.get("bit_rate", 0))),
            channels=audio_stream.get("channels", 2),
            sample_rate=int(audio_stream.get("sample_rate", 44100)),
            format=format_data.get("format_name", "unknown"),
            file_size=int(format_data.get("size", 0)),
        )

    async def get_image_metadata(self, file_path: str) -> ImageMetadata:
        """Extract metadata from an image file."""
        probe_data = await self._probe_file(file_path)

        video_stream = next(
            (s for s in probe_data.get("streams", []) if s["codec_type"] == "video"),
            None,
        )
        format_data = probe_data.get("format", {})

        if not video_stream:
            raise ValueError("No image data found")

        return ImageMetadata(
            width=video_stream.get("width", 0),
            height=video_stream.get("height", 0),
            format=format_data.get("format_name", "unknown"),
            file_size=int(format_data.get("size", 0)),
            color_space=video_stream.get("color_space"),
            has_alpha=video_stream.get("pix_fmt", "").endswith("a"),
        )

    async def generate_thumbnail(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        timestamp: float = 0,
        width: int = 320,
        height: int = 180,
    ) -> str:
        """
        Generate a thumbnail from a video.

        Args:
            video_path: Path to input video
            output_path: Path for output thumbnail (auto-generated if None)
            timestamp: Time in seconds to extract frame
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            Path to generated thumbnail
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"thumb_{uuid.uuid4().hex}.jpg",
            )

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-ss",
            str(timestamp),
            "-i",
            video_path,
            "-vframes",
            "1",
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-q:v",
            "2",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def generate_thumbnails_grid(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        columns: int = 4,
        rows: int = 4,
        width: int = 160,
    ) -> str:
        """
        Generate a grid of thumbnails from a video.

        Args:
            video_path: Path to input video
            output_path: Path for output image
            columns: Number of columns in grid
            rows: Number of rows in grid
            width: Width of each thumbnail

        Returns:
            Path to generated grid image
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"grid_{uuid.uuid4().hex}.jpg",
            )

        metadata = await self.get_video_metadata(video_path)
        interval = metadata.duration / (columns * rows)

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps=1/{interval},scale={width}:-1,tile={columns}x{rows}",
            "-frames:v",
            "1",
            "-q:v",
            "2",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        format: str = "mp3",
        bitrate: str = "192k",
    ) -> str:
        """
        Extract audio from a video file.

        Args:
            video_path: Path to input video
            output_path: Path for output audio
            format: Output format (mp3, aac, wav, etc.)
            bitrate: Audio bitrate

        Returns:
            Path to extracted audio
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"audio_{uuid.uuid4().hex}.{format}",
            )

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "libmp3lame" if format == "mp3" else "aac",
            "-ab",
            bitrate,
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def clip_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Extract a clip from a video.

        Args:
            video_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output clip

        Returns:
            Path to extracted clip
        """
        if output_path is None:
            ext = os.path.splitext(video_path)[1] or ".mp4"
            output_path = os.path.join(
                self._temp_dir,
                f"clip_{uuid.uuid4().hex}{ext}",
            )

        duration = end_time - start_time

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-ss",
            str(start_time),
            "-i",
            video_path,
            "-t",
            str(duration),
            "-c",
            "copy",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def clip_audio(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Extract a clip from an audio file.

        Args:
            audio_path: Path to input audio
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output clip

        Returns:
            Path to extracted clip
        """
        if output_path is None:
            ext = os.path.splitext(audio_path)[1] or ".mp3"
            output_path = os.path.join(
                self._temp_dir,
                f"clip_{uuid.uuid4().hex}{ext}",
            )

        duration = end_time - start_time

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-ss",
            str(start_time),
            "-i",
            audio_path,
            "-t",
            str(duration),
            "-c",
            "copy",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def generate_waveform(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        width: int = 1920,
        height: int = 200,
        color: str = "0x6366f1",
        background: str = "0x1f2937",
    ) -> str:
        """
        Generate a waveform visualization image from audio.

        Args:
            audio_path: Path to input audio
            output_path: Path for output image
            width: Image width
            height: Image height
            color: Waveform color (hex)
            background: Background color (hex)

        Returns:
            Path to generated waveform image
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"waveform_{uuid.uuid4().hex}.png",
            )

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            audio_path,
            "-filter_complex",
            f"showwavespic=s={width}x{height}:colors={color}",
            "-frames:v",
            "1",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def generate_waveform_data(
        self,
        audio_path: str,
        samples: int = 100,
    ) -> list[float]:
        """
        Generate waveform data as a list of amplitude values.

        Args:
            audio_path: Path to input audio
            samples: Number of data points to generate

        Returns:
            List of amplitude values (0.0 to 1.0)
        """
        # Get audio duration
        metadata = await self.get_audio_metadata(audio_path)

        # Generate raw amplitude data
        temp_file = os.path.join(self._temp_dir, f"wave_{uuid.uuid4().hex}.txt")

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            audio_path,
            "-af",
            f"aresample={samples},astats=metadata=1:reset=1",
            "-f",
            "null",
            "-",
        ]

        # For simplicity, we'll use a different approach - sampling the audio
        # at regular intervals and getting peak values
        interval = metadata.duration / samples
        amplitudes = []

        for i in range(samples):
            timestamp = i * interval
            try:
                # Get volume at this timestamp
                cmd = [
                    self._ffmpeg_path,
                    "-ss",
                    str(timestamp),
                    "-t",
                    str(interval),
                    "-i",
                    audio_path,
                    "-af",
                    "volumedetect",
                    "-f",
                    "null",
                    "-",
                ]
                result = await self._run_ffmpeg(cmd, capture_stderr=True)

                # Parse max volume from output
                for line in result.split("\n"):
                    if "max_volume" in line:
                        # Parse value like "max_volume: -5.2 dB"
                        parts = line.split(":")
                        if len(parts) >= 2:
                            db_value = float(parts[1].strip().split()[0])
                            # Convert dB to linear (0-1 range)
                            # 0 dB = 1.0, -60 dB = ~0.001
                            amplitude = 10 ** (db_value / 20) if db_value > -60 else 0
                            amplitudes.append(min(amplitude, 1.0))
                            break
                else:
                    amplitudes.append(0.5)  # Default if not found
            except Exception:
                amplitudes.append(0.5)

        return amplitudes

    async def concat_videos(
        self,
        video_paths: list[str],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Concatenate multiple videos into one.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video

        Returns:
            Path to concatenated video
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"concat_{uuid.uuid4().hex}.mp4",
            )

        # Create concat file
        concat_file = os.path.join(self._temp_dir, f"concat_{uuid.uuid4().hex}.txt")
        with open(concat_file, "w") as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",
            output_path,
        ]

        try:
            await self._run_ffmpeg(cmd)
            return output_path
        finally:
            os.unlink(concat_file)

    async def concat_audio(
        self,
        audio_paths: list[str],
        output_path: Optional[str] = None,
        format: str = "mp3",
    ) -> str:
        """
        Concatenate multiple audio files into one.

        Args:
            audio_paths: List of audio file paths
            output_path: Path for output audio
            format: Output format

        Returns:
            Path to concatenated audio
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"concat_{uuid.uuid4().hex}.{format}",
            )

        # Create concat file
        concat_file = os.path.join(self._temp_dir, f"concat_{uuid.uuid4().hex}.txt")
        with open(concat_file, "w") as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",
            output_path,
        ]

        try:
            await self._run_ffmpeg(cmd)
            return output_path
        finally:
            os.unlink(concat_file)

    async def add_audio_to_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None,
        replace_audio: bool = True,
    ) -> str:
        """
        Add or replace audio in a video.

        Args:
            video_path: Path to input video
            audio_path: Path to audio file
            output_path: Path for output video
            replace_audio: If True, replace existing audio. If False, mix.

        Returns:
            Path to output video
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"merged_{uuid.uuid4().hex}.mp4",
            )

        if replace_audio:
            cmd = [
                self._ffmpeg_path,
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                output_path,
            ]
        else:
            # Mix audio tracks
            cmd = [
                self._ffmpeg_path,
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-filter_complex",
                "[0:a][1:a]amerge=inputs=2[a]",
                "-c:v",
                "copy",
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-shortest",
                output_path,
            ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def resize_video(
        self,
        video_path: str,
        width: int,
        height: int,
        output_path: Optional[str] = None,
        maintain_aspect: bool = True,
    ) -> str:
        """
        Resize a video to specified dimensions.

        Args:
            video_path: Path to input video
            width: Target width
            height: Target height
            output_path: Path for output video
            maintain_aspect: Maintain aspect ratio with padding

        Returns:
            Path to resized video
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"resized_{uuid.uuid4().hex}.mp4",
            )

        if maintain_aspect:
            filter_str = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        else:
            filter_str = f"scale={width}:{height}"

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            video_path,
            "-vf",
            filter_str,
            "-c:a",
            "copy",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def add_subtitles(
        self,
        video_path: str,
        subtitles_path: str,
        output_path: Optional[str] = None,
        style: Optional[str] = None,
    ) -> str:
        """
        Burn subtitles into a video.

        Args:
            video_path: Path to input video
            subtitles_path: Path to SRT/ASS subtitle file
            output_path: Path for output video
            style: Optional ASS style string

        Returns:
            Path to output video with subtitles
        """
        if output_path is None:
            output_path = os.path.join(
                self._temp_dir,
                f"subtitled_{uuid.uuid4().hex}.mp4",
            )

        # Escape special characters in path
        escaped_path = subtitles_path.replace(":", "\\:").replace("'", "\\'")

        filter_str = f"subtitles='{escaped_path}'"
        if style:
            filter_str += f":force_style='{style}'"

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            video_path,
            "-vf",
            filter_str,
            "-c:a",
            "copy",
            output_path,
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def convert_video(
        self,
        input_path: str,
        output_path: str,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        video_bitrate: Optional[str] = None,
        audio_bitrate: str = "128k",
        preset: str = "medium",
    ) -> str:
        """
        Convert video to a different format/codec.

        Args:
            input_path: Path to input video
            output_path: Path for output video
            video_codec: Video codec (libx264, libx265, libvpx-vp9)
            audio_codec: Audio codec (aac, mp3, opus)
            video_bitrate: Video bitrate (e.g., "2M")
            audio_bitrate: Audio bitrate
            preset: Encoding preset (ultrafast, fast, medium, slow)

        Returns:
            Path to converted video
        """
        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-c:v",
            video_codec,
            "-c:a",
            audio_codec,
            "-preset",
            preset,
            "-ab",
            audio_bitrate,
        ]

        if video_bitrate:
            cmd.extend(["-b:v", video_bitrate])

        cmd.append(output_path)

        await self._run_ffmpeg(cmd)
        return output_path

    async def _probe_file(self, file_path: str) -> dict:
        """Run ffprobe to get file metadata."""
        cmd = [
            self._ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {stderr.decode()}")

        return json.loads(stdout.decode())

    async def _run_ffmpeg(
        self,
        cmd: list[str],
        capture_stderr: bool = False,
    ) -> str:
        """Run an FFmpeg command."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

        if capture_stderr:
            return stderr.decode()
        return stdout.decode()


# Singleton instance
media_processor = MediaProcessor()
