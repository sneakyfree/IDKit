"""
IDKit Machine Learning Infrastructure

Self-hosted open-source AI models for avatar generation, voice cloning,
and text generation. Supports both local GPU and cloud GPU providers.
"""

from app.ml.model_registry import (
    ModelRegistry,
    ModelInfo,
    ModelType,
    ModelStatus,
    ModelSource,
    ModelRequirements,
)
from app.ml.inference import (
    InferenceEngine,
    InferenceConfig,
    InferenceRequest,
    InferenceResult,
    InferenceStatus,
    BaseInferenceHandler,
)
from app.ml.pipeline import (
    MLPipeline,
    PipelineStage,
    PipelineResult,
    StageResult,
    StageStatus,
    ModelStage,
    TransformStage,
    ConditionalStage,
    ParallelStage,
    LoopStage,
    # Pre-built pipelines
    create_avatar_video_pipeline,
    create_podcast_pipeline,
    create_content_repurpose_pipeline,
    create_voice_clone_pipeline,
)

__all__ = [
    # Model Registry
    "ModelRegistry",
    "ModelInfo",
    "ModelType",
    "ModelStatus",
    "ModelSource",
    "ModelRequirements",
    # Inference Engine
    "InferenceEngine",
    "InferenceConfig",
    "InferenceRequest",
    "InferenceResult",
    "InferenceStatus",
    "BaseInferenceHandler",
    # Pipeline
    "MLPipeline",
    "PipelineStage",
    "PipelineResult",
    "StageResult",
    "StageStatus",
    "ModelStage",
    "TransformStage",
    "ConditionalStage",
    "ParallelStage",
    "LoopStage",
    # Pre-built pipelines
    "create_avatar_video_pipeline",
    "create_podcast_pipeline",
    "create_content_repurpose_pipeline",
    "create_voice_clone_pipeline",
]
