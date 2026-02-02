"""
HeyGen API Client

Integration with HeyGen for Avatar IV video generation.
https://docs.heygen.com/
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import httpx


class HeyGenError(Exception):
    """HeyGen API error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class HeyGenClient:
    """
    Client for HeyGen Avatar IV API.
    
    Features:
    - Create personalized avatars from video samples
    - Generate talking head videos
    - Async video generation with webhooks
    """

    BASE_URL = "https://api.heygen.com/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        callback_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY", "")
        self.callback_url = callback_url or os.getenv("HEYGEN_CALLBACK_URL", "")
        
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY is required")

    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_avatar(
        self,
        video_url: str,
        name: str,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Create a personalized avatar from a video sample.
        
        Args:
            video_url: URL to the video sample (min 2 minutes recommended)
            name: Name for the avatar
            user_id: Optional user reference
            
        Returns:
            Avatar creation response with avatar_id
        """
        payload = {
            "video_url": video_url,
            "avatar_name": name,
            "is_instant": False,  # Use high-quality processing
        }

        if self.callback_url:
            payload["callback_url"] = f"{self.callback_url}/avatar"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/avatars/train",
                headers=self._headers(),
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise HeyGenError(
                    f"Failed to create avatar: {response.text}",
                    response.status_code,
                )

            return response.json()

    async def get_avatar_status(
        self,
        avatar_id: str,
    ) -> Dict[str, Any]:
        """
        Check avatar training status.
        
        Returns:
            Status response with training progress
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/avatars/{avatar_id}/status",
                headers=self._headers(),
                timeout=30.0,
            )

            if response.status_code != 200:
                raise HeyGenError(
                    f"Failed to get avatar status: {response.text}",
                    response.status_code,
                )

            return response.json()

    async def generate_video(
        self,
        avatar_id: str,
        script: str,
        voice_id: Optional[str] = None,
        audio_url: Optional[str] = None,
        background: str = "transparent",
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """
        Generate a video using the avatar.
        
        Args:
            avatar_id: HeyGen avatar ID
            script: Text script for the video
            voice_id: Optional voice ID (use HeyGen voice or provide audio)
            audio_url: Pre-generated audio URL (from ElevenLabs)
            background: Background type
            aspect_ratio: Video aspect ratio
            
        Returns:
            Video generation response with video_id
        """
        # Build video input
        video_inputs = [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal",
            },
            "background": {
                "type": background,
            },
        }]

        # Use either pre-generated audio or text-to-speech
        if audio_url:
            video_inputs[0]["voice"] = {
                "type": "audio",
                "audio_url": audio_url,
            }
        elif voice_id:
            video_inputs[0]["voice"] = {
                "type": "text",
                "input_text": script,
                "voice_id": voice_id,
            }
        else:
            # Use default voice with script
            video_inputs[0]["voice"] = {
                "type": "text",
                "input_text": script,
                "voice_id": "default",
            }

        payload = {
            "video_inputs": video_inputs,
            "dimension": self._get_dimension(aspect_ratio),
        }

        if self.callback_url:
            payload["callback_url"] = f"{self.callback_url}/video"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/videos/generate",
                headers=self._headers(),
                json=payload,
                timeout=60.0,
            )

            if response.status_code not in (200, 201):
                raise HeyGenError(
                    f"Failed to generate video: {response.text}",
                    response.status_code,
                )

            return response.json()

    async def get_video_status(
        self,
        video_id: str,
    ) -> Dict[str, Any]:
        """
        Check video generation status.
        
        Returns:
            Status with progress, state, and video_url when complete
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/videos/{video_id}/status",
                headers=self._headers(),
                timeout=30.0,
            )

            if response.status_code != 200:
                raise HeyGenError(
                    f"Failed to get video status: {response.text}",
                    response.status_code,
                )

            return response.json()

    async def wait_for_video(
        self,
        video_id: str,
        timeout_seconds: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """
        Poll until video is complete.
        
        Args:
            video_id: Video generation ID
            timeout_seconds: Max wait time
            poll_interval: Seconds between polls
            
        Returns:
            Completed video response with URL
        """
        start = datetime.utcnow()
        
        while True:
            status = await self.get_video_status(video_id)
            
            if status.get("state") == "completed":
                return status
            elif status.get("state") == "failed":
                raise HeyGenError(
                    f"Video generation failed: {status.get('error', 'Unknown error')}"
                )
            
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > timeout_seconds:
                raise HeyGenError("Video generation timed out")
            
            await asyncio.sleep(poll_interval)

    async def list_avatars(self) -> Dict[str, Any]:
        """List all available avatars."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/avatars",
                headers=self._headers(),
                timeout=30.0,
            )

            if response.status_code != 200:
                raise HeyGenError(
                    f"Failed to list avatars: {response.text}",
                    response.status_code,
                )

            return response.json()

    async def delete_avatar(self, avatar_id: str) -> bool:
        """Delete an avatar."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/avatars/{avatar_id}",
                headers=self._headers(),
                timeout=30.0,
            )

            return response.status_code == 200

    def _get_dimension(self, aspect_ratio: str) -> Dict[str, int]:
        """Convert aspect ratio to dimensions."""
        dimensions = {
            "16:9": {"width": 1920, "height": 1080},
            "9:16": {"width": 1080, "height": 1920},
            "1:1": {"width": 1080, "height": 1080},
            "4:3": {"width": 1440, "height": 1080},
        }
        return dimensions.get(aspect_ratio, dimensions["16:9"])
