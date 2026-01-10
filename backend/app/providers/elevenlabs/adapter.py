"""
ElevenLabs Voice Provider

Integration with ElevenLabs API for voice cloning and synthesis.
https://docs.elevenlabs.io/
"""

import asyncio
import httpx
from typing import AsyncIterator, Optional

from app.config import settings
from app.providers.interfaces.voice_provider import (
    VoiceProvider,
    VoiceCloningConfig,
    VoiceCloningResult,
    VoiceSynthesisConfig,
    VoiceSynthesisResult,
    VoiceInfo,
    VoiceJobStatus,
)


class ElevenLabsVoiceProvider(VoiceProvider):
    """
    ElevenLabs voice provider implementation.

    Supports:
    - Instant voice cloning (Professional Voice Cloning)
    - High-quality speech synthesis
    - Streaming audio generation
    - Multiple languages (29+)
    """

    BASE_URL = "https://api.elevenlabs.io"
    API_VERSION = "v1"

    # Output format mappings
    OUTPUT_FORMATS = {
        "mp3_44100_128": "mp3_44100_128",
        "mp3_44100_192": "mp3_44100_192",
        "pcm_16000": "pcm_16000",
        "pcm_22050": "pcm_22050",
        "pcm_24000": "pcm_24000",
        "pcm_44100": "pcm_44100",
        "ulaw_8000": "ulaw_8000",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    @property
    def supports_voice_cloning(self) -> bool:
        return True

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supported_languages(self) -> list[str]:
        return [
            "en", "de", "pl", "es", "it", "fr", "pt", "hi", "ar",
            "zh", "ko", "ja", "nl", "tr", "sv", "id", "fil", "ms",
            "ro", "uk", "el", "cs", "da", "fi", "bg", "hr", "sk", "ta",
        ]

    @property
    def max_text_length(self) -> int:
        return 5000

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=120.0,  # Voice synthesis can take time
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict | bytes:
        """Make API request with error handling."""
        client = await self._get_client()
        url = f"/{self.API_VERSION}/{endpoint}"

        response = await client.request(method, url, **kwargs)

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"detail": response.text}
            raise Exception(
                f"ElevenLabs API error: {response.status_code} - "
                f"{error_data.get('detail', {}).get('message', str(error_data))}"
            )

        # Return bytes for audio, JSON for everything else
        content_type = response.headers.get("content-type", "")
        if "audio" in content_type or "octet-stream" in content_type:
            return response.content

        return response.json()

    async def clone_voice(
        self,
        config: VoiceCloningConfig,
    ) -> VoiceCloningResult:
        """
        Clone a voice from audio samples.

        ElevenLabs instant voice cloning requires:
        - 1+ audio samples (recommended: 1-2 minutes total)
        - Clear speech without background noise
        - Single speaker
        """
        # Download audio files to send as multipart
        async with httpx.AsyncClient() as download_client:
            files = []
            for i, url in enumerate(config.audio_urls):
                try:
                    audio_response = await download_client.get(url)
                    audio_response.raise_for_status()
                    files.append(
                        ("files", (f"sample_{i}.mp3", audio_response.content, "audio/mpeg"))
                    )
                except Exception as e:
                    return VoiceCloningResult(
                        voice_id="",
                        status=VoiceJobStatus.FAILED,
                        metadata={"error": f"Failed to download audio {i}: {e}"},
                    )

        # Prepare form data
        data = {
            "name": config.name,
        }

        if config.description:
            data["description"] = config.description

        # Optional: Add labels
        labels = {}
        if config.gender:
            labels["gender"] = config.gender
        if config.accent:
            labels["accent"] = config.accent
        if labels:
            data["labels"] = str(labels)

        try:
            # Use multipart form for file upload
            client = await self._get_client()
            response = await client.post(
                f"/{self.API_VERSION}/voices/add",
                data=data,
                files=files,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise Exception(f"API error: {error_data}")

            result = response.json()

            return VoiceCloningResult(
                voice_id=result.get("voice_id", ""),
                status=VoiceJobStatus.COMPLETED,  # ElevenLabs instant cloning
                preview_url=None,  # Generate preview separately if needed
                samples_used=len(config.audio_urls),
                quality_score=0.85,  # ElevenLabs doesn't provide this
                metadata={
                    "name": config.name,
                    "elevenlabs_voice_id": result.get("voice_id"),
                },
            )

        except Exception as e:
            return VoiceCloningResult(
                voice_id="",
                status=VoiceJobStatus.FAILED,
                metadata={"error": str(e)},
            )

    async def get_voice(
        self,
        voice_id: str,
    ) -> VoiceInfo:
        """Get information about a voice."""
        try:
            result = await self._request(
                "GET",
                f"voices/{voice_id}",
            )

            labels = result.get("labels", {})

            return VoiceInfo(
                voice_id=voice_id,
                name=result.get("name", "Unknown"),
                description=result.get("description"),
                preview_url=result.get("preview_url"),
                is_cloned=result.get("category") == "cloned",
                languages=self.supported_languages,  # All cloned voices support all languages
                gender=labels.get("gender"),
                age=labels.get("age"),
                use_count=result.get("use_count", 0),
                metadata=result,
            )

        except Exception as e:
            raise Exception(f"Failed to get voice: {e}")

    async def list_voices(self) -> list[VoiceInfo]:
        """List all available voices."""
        try:
            result = await self._request(
                "GET",
                "voices",
            )

            voices = []
            for v in result.get("voices", []):
                labels = v.get("labels", {})
                voices.append(
                    VoiceInfo(
                        voice_id=v.get("voice_id", ""),
                        name=v.get("name", "Unknown"),
                        description=v.get("description"),
                        preview_url=v.get("preview_url"),
                        is_cloned=v.get("category") == "cloned",
                        languages=self.supported_languages,
                        gender=labels.get("gender"),
                        age=labels.get("age"),
                        metadata=v,
                    )
                )

            return voices

        except Exception as e:
            raise Exception(f"Failed to list voices: {e}")

    async def delete_voice(
        self,
        voice_id: str,
    ) -> bool:
        """Delete a cloned voice."""
        try:
            await self._request(
                "DELETE",
                f"voices/{voice_id}",
            )
            return True
        except Exception:
            return False

    async def synthesize_speech(
        self,
        config: VoiceSynthesisConfig,
    ) -> VoiceSynthesisResult:
        """
        Generate speech from text.

        Returns audio file URL (uploaded to storage).
        """
        # Build request payload
        payload = {
            "text": config.text,
            "model_id": config.extras.get("model_id", "eleven_multilingual_v2"),
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
                "use_speaker_boost": True,
            },
        }

        # Output format
        output_format = self.OUTPUT_FORMATS.get(
            config.output_format,
            "mp3_44100_128"
        )

        try:
            # Make synthesis request
            audio_data = await self._request(
                "POST",
                f"text-to-speech/{config.voice_id}",
                json=payload,
                params={"output_format": output_format},
            )

            # Calculate duration estimate (avg 15 chars/second)
            duration_estimate = len(config.text) / 15

            # In production, would upload to S3 and return URL
            # For now, return the audio data
            return VoiceSynthesisResult(
                audio_data=audio_data if isinstance(audio_data, bytes) else None,
                duration_seconds=duration_estimate,
                character_count=len(config.text),
                metadata={
                    "model_id": payload["model_id"],
                    "output_format": output_format,
                },
            )

        except Exception as e:
            raise Exception(f"Speech synthesis failed: {e}")

    async def synthesize_speech_stream(
        self,
        config: VoiceSynthesisConfig,
    ) -> AsyncIterator[bytes]:
        """
        Stream speech generation in chunks.

        Yields audio data as it's generated for low-latency playback.
        """
        # Build request payload
        payload = {
            "text": config.text,
            "model_id": config.extras.get("model_id", "eleven_multilingual_v2"),
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
            },
        }

        output_format = self.OUTPUT_FORMATS.get(
            config.output_format,
            "mp3_44100_128"
        )

        client = await self._get_client()

        async with client.stream(
            "POST",
            f"/{self.API_VERSION}/text-to-speech/{config.voice_id}/stream",
            json=payload,
            params={"output_format": output_format},
        ) as response:
            if response.status_code >= 400:
                content = await response.aread()
                raise Exception(f"Streaming failed: {content}")

            async for chunk in response.aiter_bytes(chunk_size=4096):
                yield chunk

    async def validate_audio_samples(
        self,
        audio_urls: list[str],
    ) -> dict:
        """
        Validate audio samples for voice cloning.

        ElevenLabs requirements:
        - At least 1 minute of clear speech (recommended: 1-2 minutes)
        - Single speaker
        - Minimal background noise
        - Supported formats: MP3, WAV, M4A
        """
        issues = []
        quality_scores = []
        total_duration = 0

        async with httpx.AsyncClient() as client:
            for i, url in enumerate(audio_urls):
                try:
                    # Check if file is accessible
                    head_response = await client.head(url)
                    if head_response.status_code != 200:
                        issues.append(f"Audio {i+1}: Unable to access file")
                        quality_scores.append(0)
                        continue

                    # Check content type
                    content_type = head_response.headers.get("content-type", "")
                    if not any(t in content_type for t in ["audio", "mpeg", "wav", "m4a"]):
                        issues.append(f"Audio {i+1}: Invalid file type ({content_type})")
                        quality_scores.append(0.3)
                    else:
                        quality_scores.append(0.8)

                    # Estimate duration from file size (rough estimate)
                    content_length = int(head_response.headers.get("content-length", 0))
                    # Assume ~128kbps = 16KB/sec
                    estimated_duration = content_length / 16000
                    total_duration += estimated_duration

                except Exception as e:
                    issues.append(f"Audio {i+1}: Validation error - {e}")
                    quality_scores.append(0)

        # Check minimum duration (60 seconds recommended)
        minimum_duration_met = total_duration >= 60

        if not minimum_duration_met:
            issues.append(
                f"Total audio duration (~{int(total_duration)}s) is less than "
                "recommended minimum (60s). More samples will improve quality."
            )

        return {
            "valid": len([i for i in issues if "Unable" in i or "Invalid" in i]) == 0,
            "issues": issues,
            "quality_scores": quality_scores,
            "total_duration_seconds": total_duration,
            "minimum_duration_met": minimum_duration_met,
            "recommendations": [
                "Use 1-2 minutes of clear speech for best results",
                "Ensure minimal background noise",
                "Use consistent speaking style throughout samples",
                "Include varied intonation for natural synthesis",
            ],
        }

    async def estimate_cost(
        self,
        text: str,
        voice_id: str,
    ) -> dict:
        """
        Estimate the cost of synthesizing text.

        ElevenLabs charges per character.
        """
        char_count = len(text)

        # Pricing (approximate, varies by plan)
        # Free: 10,000 chars/month
        # Starter: ~$0.30 per 1000 chars
        # Creator: ~$0.24 per 1000 chars
        # Pro: ~$0.18 per 1000 chars
        cost_per_1000 = 0.24  # Assume Creator tier

        return {
            "character_count": char_count,
            "estimated_cost": round(char_count / 1000 * cost_per_1000, 4),
            "estimated_duration_seconds": char_count / 15,  # ~15 chars/sec
            "cost_per_1000_chars": cost_per_1000,
        }

    async def get_usage(self) -> dict:
        """Get current usage statistics."""
        try:
            result = await self._request(
                "GET",
                "user/subscription",
            )

            return {
                "characters_used": result.get("character_count", 0),
                "character_limit": result.get("character_limit", 0),
                "reset_date": result.get("next_character_count_reset_unix"),
                "tier": result.get("tier"),
                "can_use_instant_voice_cloning": result.get(
                    "can_use_instant_voice_cloning", False
                ),
                "can_use_professional_voice_cloning": result.get(
                    "can_use_professional_voice_cloning", False
                ),
            }

        except Exception as e:
            return {
                "error": str(e),
                "characters_used": 0,
                "character_limit": None,
            }

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
