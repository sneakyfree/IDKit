"""
ML Pipeline

Composable pipelines for complex ML workflows.
Chains multiple models and processing steps together.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generic, Optional, TypeVar
from uuid import UUID, uuid4

from app.ml.model_registry import ModelRegistry, ModelType
from app.ml.inference import InferenceEngine

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StageStatus(str, Enum):
    """Pipeline stage status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a pipeline stage."""
    stage_name: str
    status: StageStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result from a complete pipeline run."""
    pipeline_id: UUID
    pipeline_name: str
    status: StageStatus
    stages: list[StageResult]
    final_output: Any = None
    total_duration_ms: float = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PipelineStage(ABC):
    """Base class for pipeline stages."""

    def __init__(self, name: str):
        self.name = name
        self.next_stage: Optional["PipelineStage"] = None

    @abstractmethod
    async def process(self, input_data: Any, context: dict) -> Any:
        """Process input and return output."""
        pass

    def chain(self, next_stage: "PipelineStage") -> "PipelineStage":
        """Chain another stage after this one."""
        self.next_stage = next_stage
        return next_stage


class ModelStage(PipelineStage):
    """Stage that runs a model inference."""

    def __init__(
        self,
        name: str,
        model_name: str,
        engine: InferenceEngine,
        params: Optional[dict] = None,
        input_mapper: Optional[Callable[[Any], Any]] = None,
        output_mapper: Optional[Callable[[Any], Any]] = None,
    ):
        super().__init__(name)
        self.model_name = model_name
        self.engine = engine
        self.params = params or {}
        self.input_mapper = input_mapper
        self.output_mapper = output_mapper

    async def process(self, input_data: Any, context: dict) -> Any:
        """Run model inference."""
        # Map input if mapper provided
        if self.input_mapper:
            input_data = self.input_mapper(input_data)

        # Get model
        model = self.engine.registry.get_by_name(self.model_name)
        if not model:
            raise ValueError(f"Model {self.model_name} not found")

        # Merge params from context
        params = {**self.params, **context.get("params", {})}

        # Run inference
        result = await self.engine.infer(model.id, input_data, params)

        # Map output if mapper provided
        output = result.output
        if self.output_mapper:
            output = self.output_mapper(output)

        return output


class TransformStage(PipelineStage):
    """Stage that transforms data without a model."""

    def __init__(
        self,
        name: str,
        transform_fn: Callable[[Any, dict], Any],
    ):
        super().__init__(name)
        self.transform_fn = transform_fn

    async def process(self, input_data: Any, context: dict) -> Any:
        """Apply transformation."""
        if asyncio.iscoroutinefunction(self.transform_fn):
            return await self.transform_fn(input_data, context)
        return self.transform_fn(input_data, context)


class ConditionalStage(PipelineStage):
    """Stage that conditionally executes based on a condition."""

    def __init__(
        self,
        name: str,
        condition: Callable[[Any, dict], bool],
        if_true: PipelineStage,
        if_false: Optional[PipelineStage] = None,
    ):
        super().__init__(name)
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    async def process(self, input_data: Any, context: dict) -> Any:
        """Execute conditional branch."""
        if self.condition(input_data, context):
            return await self.if_true.process(input_data, context)
        elif self.if_false:
            return await self.if_false.process(input_data, context)
        return input_data


class ParallelStage(PipelineStage):
    """Stage that runs multiple stages in parallel."""

    def __init__(
        self,
        name: str,
        stages: list[PipelineStage],
        combiner: Optional[Callable[[list[Any]], Any]] = None,
    ):
        super().__init__(name)
        self.stages = stages
        self.combiner = combiner or (lambda results: results)

    async def process(self, input_data: Any, context: dict) -> Any:
        """Run stages in parallel."""
        tasks = [
            stage.process(input_data, context)
            for stage in self.stages
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Parallel stage {self.stages[i].name} failed: {result}")
                raise result

        return self.combiner(results)


class LoopStage(PipelineStage):
    """Stage that loops over items and processes each."""

    def __init__(
        self,
        name: str,
        inner_stage: PipelineStage,
        max_concurrency: int = 5,
    ):
        super().__init__(name)
        self.inner_stage = inner_stage
        self.max_concurrency = max_concurrency

    async def process(self, input_data: Any, context: dict) -> Any:
        """Process each item in input."""
        if not isinstance(input_data, (list, tuple)):
            input_data = [input_data]

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item):
            async with semaphore:
                return await self.inner_stage.process(item, context)

        tasks = [process_item(item) for item in input_data]
        return await asyncio.gather(*tasks)


class MLPipeline:
    """
    Composable ML pipeline.

    Chains multiple processing stages together for complex workflows.
    """

    def __init__(
        self,
        name: str,
        engine: InferenceEngine,
    ):
        """
        Initialize pipeline.

        Args:
            name: Pipeline name
            engine: Inference engine for model stages
        """
        self.id = uuid4()
        self.name = name
        self.engine = engine
        self._stages: list[PipelineStage] = []
        self._first_stage: Optional[PipelineStage] = None

    def add_stage(self, stage: PipelineStage) -> "MLPipeline":
        """Add a stage to the pipeline."""
        self._stages.append(stage)

        if self._first_stage is None:
            self._first_stage = stage
        else:
            # Chain to last stage
            self._stages[-2].chain(stage)

        return self

    def add_model(
        self,
        name: str,
        model_name: str,
        params: Optional[dict] = None,
        input_mapper: Optional[Callable] = None,
        output_mapper: Optional[Callable] = None,
    ) -> "MLPipeline":
        """Add a model inference stage."""
        stage = ModelStage(
            name=name,
            model_name=model_name,
            engine=self.engine,
            params=params,
            input_mapper=input_mapper,
            output_mapper=output_mapper,
        )
        return self.add_stage(stage)

    def add_transform(
        self,
        name: str,
        transform_fn: Callable[[Any, dict], Any],
    ) -> "MLPipeline":
        """Add a transform stage."""
        stage = TransformStage(name, transform_fn)
        return self.add_stage(stage)

    def add_conditional(
        self,
        name: str,
        condition: Callable[[Any, dict], bool],
        if_true: PipelineStage,
        if_false: Optional[PipelineStage] = None,
    ) -> "MLPipeline":
        """Add a conditional stage."""
        stage = ConditionalStage(name, condition, if_true, if_false)
        return self.add_stage(stage)

    def add_parallel(
        self,
        name: str,
        stages: list[PipelineStage],
        combiner: Optional[Callable] = None,
    ) -> "MLPipeline":
        """Add parallel processing stages."""
        stage = ParallelStage(name, stages, combiner)
        return self.add_stage(stage)

    async def run(
        self,
        input_data: Any,
        context: Optional[dict] = None,
    ) -> PipelineResult:
        """
        Run the pipeline.

        Args:
            input_data: Initial input
            context: Shared context for all stages

        Returns:
            Pipeline result with all stage results
        """
        context = context or {}
        stages_results: list[StageResult] = []
        current_data = input_data
        start_time = datetime.utcnow()
        total_start = asyncio.get_event_loop().time()

        logger.info(f"Starting pipeline: {self.name}")

        overall_status = StageStatus.COMPLETED

        for stage in self._stages:
            stage_start = asyncio.get_event_loop().time()
            stage_result = StageResult(
                stage_name=stage.name,
                status=StageStatus.RUNNING,
            )

            try:
                logger.debug(f"Running stage: {stage.name}")
                current_data = await stage.process(current_data, context)

                stage_result.status = StageStatus.COMPLETED
                stage_result.output = current_data
                stage_result.duration_ms = (
                    asyncio.get_event_loop().time() - stage_start
                ) * 1000

                logger.debug(
                    f"Stage {stage.name} completed in "
                    f"{stage_result.duration_ms:.2f}ms"
                )

            except Exception as e:
                stage_result.status = StageStatus.FAILED
                stage_result.error = str(e)
                stage_result.duration_ms = (
                    asyncio.get_event_loop().time() - stage_start
                ) * 1000
                overall_status = StageStatus.FAILED

                logger.error(f"Stage {stage.name} failed: {e}")

                # Mark remaining stages as skipped
                for remaining in self._stages[self._stages.index(stage) + 1:]:
                    stages_results.append(StageResult(
                        stage_name=remaining.name,
                        status=StageStatus.SKIPPED,
                    ))
                break

            finally:
                stages_results.append(stage_result)

        total_duration = (asyncio.get_event_loop().time() - total_start) * 1000

        result = PipelineResult(
            pipeline_id=self.id,
            pipeline_name=self.name,
            status=overall_status,
            stages=stages_results,
            final_output=current_data if overall_status == StageStatus.COMPLETED else None,
            total_duration_ms=total_duration,
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )

        logger.info(
            f"Pipeline {self.name} {overall_status.value} "
            f"in {total_duration:.2f}ms"
        )

        return result

    def describe(self) -> dict:
        """Get pipeline description."""
        return {
            "id": str(self.id),
            "name": self.name,
            "stages": [
                {
                    "name": stage.name,
                    "type": stage.__class__.__name__,
                }
                for stage in self._stages
            ],
        }


# =============================================================================
# Pre-built Pipelines
# =============================================================================


def create_avatar_video_pipeline(
    engine: InferenceEngine,
) -> MLPipeline:
    """
    Create pipeline for avatar video generation.

    Input: {text: str, voice_id: str, avatar_id: str}
    Output: {video_url: str}
    """
    pipeline = MLPipeline("avatar_video", engine)

    # Stage 1: Generate speech from text
    pipeline.add_model(
        name="text_to_speech",
        model_name="coqui-xtts",
        input_mapper=lambda x: x["text"],
        output_mapper=lambda audio: {"audio": audio, **{}},
    )

    # Stage 2: Generate lip-sync video
    pipeline.add_model(
        name="lip_sync",
        model_name="sadtalker",
        input_mapper=lambda x: {
            "audio": x["audio"],
            "source_image": x.get("avatar_image"),
        },
    )

    # Stage 3: Enhance video quality
    pipeline.add_model(
        name="enhance_video",
        model_name="gfpgan",
    )

    return pipeline


def create_podcast_pipeline(
    engine: InferenceEngine,
) -> MLPipeline:
    """
    Create pipeline for podcast generation.

    Input: {topic: str, style: str, duration_minutes: int}
    Output: {audio_url: str, transcript: str, chapters: list}
    """
    pipeline = MLPipeline("podcast_generation", engine)

    # Stage 1: Generate script
    pipeline.add_model(
        name="generate_script",
        model_name="mistral-7b",
        input_mapper=lambda x: f"Write a {x['duration_minutes']} minute podcast script about {x['topic']} in a {x['style']} style.",
        params={"max_tokens": 4000},
    )

    # Stage 2: Split into segments
    pipeline.add_transform(
        name="split_segments",
        transform_fn=lambda script, ctx: {
            "segments": script.split("\n\n"),
            "original": script,
        },
    )

    # Stage 3: Generate audio for each segment
    pipeline.add_stage(LoopStage(
        name="generate_audio_segments",
        inner_stage=ModelStage(
            name="tts",
            model_name="coqui-xtts",
            engine=engine,
        ),
        max_concurrency=2,
    ))

    # Stage 4: Combine audio segments
    pipeline.add_transform(
        name="combine_audio",
        transform_fn=lambda segments, ctx: {
            "combined_audio": b"".join(segments),
            "transcript": ctx.get("original_script", ""),
        },
    )

    return pipeline


def create_content_repurpose_pipeline(
    engine: InferenceEngine,
) -> MLPipeline:
    """
    Create pipeline for content repurposing.

    Input: {content: str, source_type: str, target_types: list}
    Output: {repurposed: dict}
    """
    pipeline = MLPipeline("content_repurpose", engine)

    # Stage 1: Analyze content
    pipeline.add_model(
        name="analyze_content",
        model_name="phi-3-mini",
        input_mapper=lambda x: f"Analyze this content and extract key points, quotes, and themes:\n\n{x['content']}",
    )

    # Stage 2: Generate variations in parallel
    def create_variation_stages(engine):
        return [
            ModelStage(
                name="twitter_thread",
                model_name="phi-3-mini",
                engine=engine,
                input_mapper=lambda x: f"Convert to Twitter thread:\n{x}",
            ),
            ModelStage(
                name="linkedin_post",
                model_name="phi-3-mini",
                engine=engine,
                input_mapper=lambda x: f"Convert to LinkedIn post:\n{x}",
            ),
            ModelStage(
                name="short_video_script",
                model_name="phi-3-mini",
                engine=engine,
                input_mapper=lambda x: f"Convert to 60-second video script:\n{x}",
            ),
        ]

    pipeline.add_parallel(
        name="generate_variations",
        stages=create_variation_stages(engine),
        combiner=lambda results: {
            "twitter": results[0],
            "linkedin": results[1],
            "video_script": results[2],
        },
    )

    return pipeline


def create_voice_clone_pipeline(
    engine: InferenceEngine,
) -> MLPipeline:
    """
    Create pipeline for voice cloning.

    Input: {audio_samples: list[bytes], reference_text: str}
    Output: {voice_id: str, sample_audio: bytes}
    """
    pipeline = MLPipeline("voice_clone", engine)

    # Stage 1: Transcribe audio samples
    pipeline.add_stage(LoopStage(
        name="transcribe_samples",
        inner_stage=ModelStage(
            name="whisper",
            model_name="whisper-large",
            engine=engine,
        ),
        max_concurrency=3,
    ))

    # Stage 2: Extract voice characteristics
    pipeline.add_transform(
        name="extract_voice_features",
        transform_fn=lambda transcripts, ctx: {
            "transcripts": transcripts,
            "features": {},  # Would extract voice features
        },
    )

    # Stage 3: Create voice clone
    pipeline.add_model(
        name="clone_voice",
        model_name="coqui-xtts",
        input_mapper=lambda x: {
            "reference_audio": ctx.get("audio_samples", []),
            "text": "This is a sample of the cloned voice.",
        },
    )

    return pipeline
