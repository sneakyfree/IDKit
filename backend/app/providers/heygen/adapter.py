"""
HeyGen Avatar Provider

Integration with HeyGen API for avatar creation and video generation.
https://docs.heygen.com/
"""

import asyncio
import httpx
from typing import AsyncIterator, Optional

from app.config import settings
from app.providers.interfaces.avatar_provider import (
    AvatarProvider,
    AvatarTrainingConfig,
    AvatarTrainingResult,
    AvatarGenerationConfig,
    AvatarGenerationResult,
    AvatarJobStatus,
    LiveSessionConfig,
    LiveSession,
)


class HeyGenAvatarProvider(AvatarProvider):
    """
    HeyGen avatar provider implementation.

    Supports:
    - Photo avatar creation
    - Video generation with lip-sync
    - Live streaming (Interactive Avatar)
    - Custom backgrounds
    """

    BASE_URL = "https://api.heygen.com"
    API_VERSION = "v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.heygen_api_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "heygen"

    @property
    def supports_live_streaming(self) -> bool:
        return True

    @property
    def supports_custom_backgrounds(self) -> bool:
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "X-Api-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Make API request with error handling."""
        client = await self._get_client()
        url = f"/{self.API_VERSION}/{endpoint}"

        response = await client.request(method, url, **kwargs)

        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            raise Exception(
                f"HeyGen API error: {response.status_code} - "
                f"{error_data.get('error', {}).get('message', 'Unknown error')}"
            )

        return response.json()

    async def create_avatar(
        self,
        config: AvatarTrainingConfig,
    ) -> AvatarTrainingResult:
        """
        Create a photo avatar from uploaded images.

        HeyGen supports instant photo avatars and trained photo avatars.
        """
        # Prepare the training payload
        payload = {
            "name": config.name,
            "image_urls": config.photo_urls,
        }

        # Add video URLs if provided (for motion training)
        if config.video_urls:
            payload["video_urls"] = config.video_urls

        # HeyGen uses different endpoints for different avatar types
        # Using Photo Avatar (Instant) for MVP
        try:
            result = await self._request(
                "POST",
                "photo_avatar",
                json=payload,
            )

            avatar_data = result.get("data", {})

            return AvatarTrainingResult(
                avatar_id=avatar_data.get("avatar_id", ""),
                status=self._map_status(avatar_data.get("status", "pending")),
                preview_url=avatar_data.get("preview_url"),
                metadata={
                    "heygen_avatar_id": avatar_data.get("avatar_id"),
                    "avatar_type": "photo_avatar",
                },
            )

        except Exception as e:
            return AvatarTrainingResult(
                avatar_id="",
                status=AvatarJobStatus.FAILED,
                metadata={"error": str(e)},
            )

    async def get_avatar_status(
        self,
        avatar_id: str,
    ) -> AvatarTrainingResult:
        """Get avatar training/creation status."""
        try:
            result = await self._request(
                "GET",
                f"photo_avatar/{avatar_id}",
            )

            avatar_data = result.get("data", {})

            return AvatarTrainingResult(
                avatar_id=avatar_id,
                status=self._map_status(avatar_data.get("status", "pending")),
                preview_url=avatar_data.get("preview_url"),
                metadata=avatar_data,
            )

        except Exception as e:
            return AvatarTrainingResult(
                avatar_id=avatar_id,
                status=AvatarJobStatus.FAILED,
                metadata={"error": str(e)},
            )

    async def delete_avatar(
        self,
        avatar_id: str,
    ) -> bool:
        """Delete an avatar."""
        try:
            await self._request(
                "DELETE",
                f"photo_avatar/{avatar_id}",
            )
            return True
        except Exception:
            return False

    async def generate_video(
        self,
        config: AvatarGenerationConfig,
    ) -> AvatarGenerationResult:
        """
        Generate a video with the avatar speaking.

        Supports both text-to-speech and audio input.
        """
        # Build video generation payload
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": config.avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": self._build_voice_config(config),
                    "background": self._build_background_config(config),
                }
            ],
            "dimension": self._get_dimension(config.aspect_ratio, config.resolution),
        }

        # Add emotion/expression if specified
        if config.emotion != "neutral":
            payload["video_inputs"][0]["character"]["emotion"] = config.emotion

        try:
            result = await self._request(
                "POST",
                "video/generate",
                json=payload,
            )

            job_data = result.get("data", {})

            return AvatarGenerationResult(
                job_id=job_data.get("video_id", ""),
                status=AvatarJobStatus.PROCESSING,
                progress=0,
                metadata={
                    "heygen_video_id": job_data.get("video_id"),
                },
            )

        except Exception as e:
            return AvatarGenerationResult(
                job_id="",
                status=AvatarJobStatus.FAILED,
                error_message=str(e),
            )

    async def get_video_status(
        self,
        job_id: str,
    ) -> AvatarGenerationResult:
        """Get video generation status."""
        try:
            result = await self._request(
                "GET",
                f"video/{job_id}",
            )

            video_data = result.get("data", {})
            status = self._map_status(video_data.get("status", "pending"))

            return AvatarGenerationResult(
                job_id=job_id,
                status=status,
                video_url=video_data.get("video_url") if status == AvatarJobStatus.COMPLETED else None,
                thumbnail_url=video_data.get("thumbnail_url"),
                duration_seconds=video_data.get("duration"),
                progress=self._estimate_progress(status),
                error_message=video_data.get("error") if status == AvatarJobStatus.FAILED else None,
                metadata=video_data,
            )

        except Exception as e:
            return AvatarGenerationResult(
                job_id=job_id,
                status=AvatarJobStatus.FAILED,
                error_message=str(e),
            )

    # ==================== Live Streaming ====================

    async def start_live_session(
        self,
        config: LiveSessionConfig,
    ) -> LiveSession:
        """
        Start an Interactive Avatar session for live streaming.
        """
        payload = {
            "avatar_id": config.avatar_id,
            "quality": config.quality,
        }

        if config.voice_id:
            payload["voice_id"] = config.voice_id

        try:
            result = await self._request(
                "POST",
                "interactive_avatar/session/start",
                json=payload,
            )

            session_data = result.get("data", {})

            return LiveSession(
                session_id=session_data.get("session_id", ""),
                rtmp_url=session_data.get("rtmp_url", ""),
                stream_key=session_data.get("stream_key", ""),
                playback_url=session_data.get("playback_url", ""),
                status="active",
                avatar_id=config.avatar_id,
                created_at=session_data.get("created_at", ""),
                metadata=session_data,
            )

        except Exception as e:
            raise Exception(f"Failed to start live session: {e}")

    async def send_live_text(
        self,
        session_id: str,
        text: str,
    ) -> bool:
        """Send text for the live avatar to speak."""
        try:
            await self._request(
                "POST",
                f"interactive_avatar/session/{session_id}/speak",
                json={"text": text},
            )
            return True
        except Exception:
            return False

    async def end_live_session(
        self,
        session_id: str,
    ) -> dict:
        """End a live streaming session."""
        try:
            result = await self._request(
                "POST",
                f"interactive_avatar/session/{session_id}/stop",
            )
            return result.get("data", {})
        except Exception as e:
            return {"error": str(e)}

    # ==================== Helper Methods ====================

    def _map_status(self, heygen_status: str) -> AvatarJobStatus:
        """Map HeyGen status to our status enum."""
        status_map = {
            "pending": AvatarJobStatus.PENDING,
            "processing": AvatarJobStatus.PROCESSING,
            "completed": AvatarJobStatus.COMPLETED,
            "failed": AvatarJobStatus.FAILED,
            "success": AvatarJobStatus.COMPLETED,
            "error": AvatarJobStatus.FAILED,
        }
        return status_map.get(heygen_status.lower(), AvatarJobStatus.PENDING)

    def _estimate_progress(self, status: AvatarJobStatus) -> int:
        """Estimate progress based on status."""
        progress_map = {
            AvatarJobStatus.PENDING: 0,
            AvatarJobStatus.PROCESSING: 50,
            AvatarJobStatus.COMPLETED: 100,
            AvatarJobStatus.FAILED: 0,
        }
        return progress_map.get(status, 0)

    def _build_voice_config(self, config: AvatarGenerationConfig) -> dict:
        """Build voice configuration for video generation."""
        if config.audio_url:
            return {
                "type": "audio",
                "audio_url": config.audio_url,
            }
        else:
            return {
                "type": "text",
                "input_text": config.text or "",
                "voice_id": config.voice_id or "en-US-JennyNeural",
            }

    def _build_background_config(self, config: AvatarGenerationConfig) -> dict:
        """Build background configuration."""
        if config.background_type == "transparent":
            return {"type": "transparent"}
        elif config.background_type == "image" and config.background_url:
            return {
                "type": "image",
                "url": config.background_url,
            }
        else:
            return {
                "type": "color",
                "value": config.background_color or "#ffffff",
            }

    def _get_dimension(self, aspect_ratio: str, resolution: str) -> dict:
        """Get video dimensions based on aspect ratio and resolution."""
        resolutions = {
            "720p": {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (720, 720)},
            "1080p": {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)},
            "4k": {"16:9": (3840, 2160), "9:16": (2160, 3840), "1:1": (2160, 2160)},
        }

        dims = resolutions.get(resolution, resolutions["1080p"])
        width, height = dims.get(aspect_ratio, dims["16:9"])

        return {"width": width, "height": height}

    async def validate_media(
        self,
        media_urls: list[str],
        media_type: str,
    ) -> dict:
        """Validate media files for avatar training."""
        # HeyGen has specific requirements:
        # - Photos: Clear frontal face, good lighting, neutral expression
        # - Minimum resolution: 512x512
        # - Supported formats: JPG, PNG

        issues = []
        quality_scores = []

        for url in media_urls:
            # In production, would analyze each image
            # For now, return optimistic validation
            quality_scores.append(0.8)

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "quality_scores": quality_scores,
            "recommendations": [
                "Use clear, well-lit frontal photos",
                "Avoid glasses and heavy makeup",
                "Neutral expression works best",
            ],
        }

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
