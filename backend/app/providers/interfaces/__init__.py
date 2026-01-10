"""Provider interfaces."""

from app.providers.interfaces.avatar_provider import AvatarProvider, AvatarGenerationResult
from app.providers.interfaces.voice_provider import VoiceProvider, VoiceSynthesisResult

__all__ = [
    "AvatarProvider",
    "AvatarGenerationResult",
    "VoiceProvider",
    "VoiceSynthesisResult",
]
