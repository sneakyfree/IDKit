"""
IDKit GPU Workers

Self-hosted GPU workers for ML inference tasks.
Supports avatar generation, voice cloning, and text generation.
"""

from worker.base import BaseWorker, WorkerConfig, JobStatus
from worker.avatar import AvatarWorker
from worker.voice import VoiceWorker
from worker.llm import LLMWorker

__all__ = [
    "BaseWorker",
    "WorkerConfig",
    "JobStatus",
    "AvatarWorker",
    "VoiceWorker",
    "LLMWorker",
]
