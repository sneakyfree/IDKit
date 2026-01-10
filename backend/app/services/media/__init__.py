"""
Media Processing Service

FFmpeg-based media processing for video, audio, and image manipulation.
"""

from app.services.media.processor import (
    MediaProcessor,
    media_processor,
    VideoMetadata,
    AudioMetadata,
    ImageMetadata,
)
from app.services.media.transcoder import (
    VideoTranscoder,
    AudioTranscoder,
    TranscodePreset,
)

__all__ = [
    "MediaProcessor",
    "media_processor",
    "VideoMetadata",
    "AudioMetadata",
    "ImageMetadata",
    "VideoTranscoder",
    "AudioTranscoder",
    "TranscodePreset",
]
