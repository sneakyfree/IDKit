"""
GPU Provider Infrastructure

Manages GPU rental providers (Vast.ai, RunPod, Lambda Labs) for
AI workloads like avatar generation, voice cloning, and model inference.
"""

from app.gpu.interfaces import (
    GPUInstance,
    GPUInstanceConfig,
    GPUInstanceStatus,
    GPUJob,
    GPUJobConfig,
    GPUJobPriority,
    GPUJobStatus,
    GPUProvider,
    GPUSpec,
)
from app.gpu.dispatcher import GPUDispatcher
from app.gpu.vastai.adapter import VastAIProvider
from app.gpu.runpod.adapter import RunPodProvider
from app.gpu.lambda_labs.adapter import LambdaLabsProvider

__all__ = [
    # Core interfaces
    "GPUDispatcher",
    "GPUInstance",
    "GPUInstanceConfig",
    "GPUInstanceStatus",
    "GPUJob",
    "GPUJobConfig",
    "GPUJobPriority",
    "GPUJobStatus",
    "GPUProvider",
    "GPUSpec",
    # Provider implementations
    "VastAIProvider",
    "RunPodProvider",
    "LambdaLabsProvider",
]
