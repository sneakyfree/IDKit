"""
Inference Engine

Unified inference engine for running ML models.
Handles batching, GPU memory management, and async execution.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID, uuid4

from app.ml.model_registry import ModelInfo, ModelRegistry, ModelType

logger = logging.getLogger(__name__)

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class InferenceStatus(str, Enum):
    """Inference request status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    # Batching
    batch_size: int = 1
    max_batch_wait_ms: int = 100

    # Memory management
    max_memory_fraction: float = 0.9
    auto_offload: bool = True

    # Execution
    timeout_seconds: int = 300
    max_retries: int = 2

    # Quality
    precision: str = "fp16"  # fp32, fp16, bf16, int8
    use_flash_attention: bool = True

    # Device
    device: str = "cuda"
    device_id: int = 0


@dataclass
class InferenceRequest:
    """A single inference request."""
    id: UUID = field(default_factory=uuid4)
    model_id: UUID = field(default_factory=uuid4)
    input_data: Any = None
    params: dict = field(default_factory=dict)
    priority: int = 0
    status: InferenceStatus = InferenceStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class InferenceResult:
    """Result of an inference request."""
    request_id: UUID
    model_id: UUID
    output: Any
    inference_time_ms: float
    tokens_generated: Optional[int] = None
    metadata: dict = field(default_factory=dict)


class BaseInferenceHandler(ABC, Generic[InputT, OutputT]):
    """Base class for model-specific inference handlers."""

    @abstractmethod
    async def preprocess(self, input_data: InputT) -> Any:
        """Preprocess input data for the model."""
        pass

    @abstractmethod
    async def inference(self, preprocessed: Any, params: dict) -> Any:
        """Run model inference."""
        pass

    @abstractmethod
    async def postprocess(self, model_output: Any) -> OutputT:
        """Postprocess model output."""
        pass


class TextGenerationHandler(BaseInferenceHandler[str, str]):
    """Handler for text generation models."""

    def __init__(self, model: Any, tokenizer: Any):
        self.model = model
        self.tokenizer = tokenizer

    async def preprocess(self, input_data: str) -> Any:
        """Tokenize input text."""
        return self.tokenizer(
            input_data,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )

    async def inference(self, preprocessed: Any, params: dict) -> Any:
        """Generate text."""
        generation_params = {
            "max_new_tokens": params.get("max_tokens", 256),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "do_sample": params.get("do_sample", True),
            "pad_token_id": self.tokenizer.pad_token_id,
        }

        # This would be actual model inference
        # output = self.model.generate(**preprocessed, **generation_params)
        output = {"generated_ids": None}  # Placeholder
        return output

    async def postprocess(self, model_output: Any) -> str:
        """Decode generated tokens."""
        # output_text = self.tokenizer.decode(model_output["generated_ids"][0])
        output_text = "Generated text placeholder"
        return output_text


class TTSHandler(BaseInferenceHandler[str, bytes]):
    """Handler for text-to-speech models."""

    def __init__(self, model: Any):
        self.model = model

    async def preprocess(self, input_data: str) -> Any:
        """Prepare text for TTS."""
        # Clean and normalize text
        return {"text": input_data.strip()}

    async def inference(self, preprocessed: Any, params: dict) -> Any:
        """Synthesize speech."""
        # This would call the actual TTS model
        return {"audio": None, "sample_rate": 22050}

    async def postprocess(self, model_output: Any) -> bytes:
        """Convert to audio bytes."""
        # Would convert numpy array to wav bytes
        return b""


class ImageGenerationHandler(BaseInferenceHandler[str, bytes]):
    """Handler for image generation models."""

    def __init__(self, model: Any):
        self.model = model

    async def preprocess(self, input_data: str) -> Any:
        """Prepare prompt for image generation."""
        return {"prompt": input_data}

    async def inference(self, preprocessed: Any, params: dict) -> Any:
        """Generate image."""
        generation_params = {
            "num_inference_steps": params.get("steps", 30),
            "guidance_scale": params.get("guidance_scale", 7.5),
            "width": params.get("width", 1024),
            "height": params.get("height", 1024),
        }
        # This would call the actual diffusion model
        return {"image": None}

    async def postprocess(self, model_output: Any) -> bytes:
        """Convert to image bytes."""
        # Would convert PIL Image to PNG bytes
        return b""


class InferenceEngine:
    """
    Central engine for running ML inference.

    Features:
    - Request queue with priority
    - Automatic batching
    - GPU memory management
    - Model loading/unloading
    - Performance monitoring
    """

    def __init__(
        self,
        registry: ModelRegistry,
        config: Optional[InferenceConfig] = None,
    ):
        """
        Initialize inference engine.

        Args:
            registry: Model registry instance
            config: Engine configuration
        """
        self.registry = registry
        self.config = config or InferenceConfig()

        # Request management
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active_requests: dict[UUID, InferenceRequest] = {}
        self._completed_requests: dict[UUID, InferenceRequest] = {}

        # Model handlers
        self._handlers: dict[UUID, BaseInferenceHandler] = {}

        # Background tasks
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_inference_time_ms = 0

    async def start(self) -> None:
        """Start the inference engine."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("Inference engine started")

    async def stop(self) -> None:
        """Stop the inference engine."""
        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Inference engine stopped")

    async def infer(
        self,
        model_id: UUID,
        input_data: Any,
        params: Optional[dict] = None,
        priority: int = 0,
        timeout: Optional[float] = None,
    ) -> InferenceResult:
        """
        Run inference on a model.

        Args:
            model_id: Model to use
            input_data: Input data for inference
            params: Model-specific parameters
            priority: Request priority (higher = more urgent)
            timeout: Optional timeout override

        Returns:
            Inference result
        """
        request = InferenceRequest(
            model_id=model_id,
            input_data=input_data,
            params=params or {},
            priority=priority,
        )

        # Add to queue (negative priority for PriorityQueue ordering)
        await self._queue.put((-priority, request))
        self._active_requests[request.id] = request

        # Wait for completion
        timeout = timeout or self.config.timeout_seconds
        start_time = time.time()

        while request.status not in (InferenceStatus.COMPLETED, InferenceStatus.FAILED):
            if time.time() - start_time > timeout:
                request.status = InferenceStatus.CANCELLED
                raise TimeoutError(f"Inference request {request.id} timed out")
            await asyncio.sleep(0.1)

        if request.status == InferenceStatus.FAILED:
            raise RuntimeError(f"Inference failed: {request.error}")

        return InferenceResult(
            request_id=request.id,
            model_id=model_id,
            output=request.result,
            inference_time_ms=(request.completed_at - request.started_at).total_seconds() * 1000
            if request.completed_at and request.started_at
            else 0,
        )

    async def infer_batch(
        self,
        model_id: UUID,
        inputs: list[Any],
        params: Optional[dict] = None,
    ) -> list[InferenceResult]:
        """
        Run batch inference.

        Args:
            model_id: Model to use
            inputs: List of inputs
            params: Shared parameters

        Returns:
            List of results
        """
        tasks = [
            self.infer(model_id, input_data, params)
            for input_data in inputs
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def stream_infer(
        self,
        model_id: UUID,
        input_data: Any,
        params: Optional[dict] = None,
    ):
        """
        Stream inference results (for text generation).

        Args:
            model_id: Model to use
            input_data: Input data
            params: Parameters

        Yields:
            Partial results as they're generated
        """
        model = self.registry.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        handler = await self._get_handler(model_id)
        preprocessed = await handler.preprocess(input_data)

        # For streaming, we'd use a streaming-capable model
        # This is a simplified implementation
        params = params or {}
        params["stream"] = True

        # Would yield tokens as they're generated
        yield {"text": "Streaming ", "done": False}
        yield {"text": "response ", "done": False}
        yield {"text": "placeholder", "done": True}

    async def _process_queue(self) -> None:
        """Process inference queue."""
        while self._running:
            try:
                # Get next request
                _, request = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )

                await self._execute_request(request)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    async def _execute_request(self, request: InferenceRequest) -> None:
        """Execute a single inference request."""
        request.status = InferenceStatus.PROCESSING
        request.started_at = datetime.utcnow()

        try:
            # Ensure model is loaded
            model = self.registry.get(request.model_id)
            if not model:
                raise ValueError(f"Model {request.model_id} not found")

            if not self.registry.is_loaded(request.model_id):
                await self.registry.load(request.model_id, self.config.device)

            # Get or create handler
            handler = await self._get_handler(request.model_id)

            # Run inference pipeline
            start_time = time.perf_counter()

            preprocessed = await handler.preprocess(request.input_data)
            model_output = await handler.inference(preprocessed, request.params)
            result = await handler.postprocess(model_output)

            inference_time = (time.perf_counter() - start_time) * 1000

            # Update request
            request.result = result
            request.status = InferenceStatus.COMPLETED
            request.completed_at = datetime.utcnow()

            # Update metrics
            self._total_requests += 1
            self._total_inference_time_ms += inference_time

            logger.debug(
                f"Inference completed for request {request.id} "
                f"in {inference_time:.2f}ms"
            )

        except Exception as e:
            request.status = InferenceStatus.FAILED
            request.error = str(e)
            request.completed_at = datetime.utcnow()
            logger.error(f"Inference failed for request {request.id}: {e}")

        finally:
            # Move to completed
            if request.id in self._active_requests:
                del self._active_requests[request.id]
            self._completed_requests[request.id] = request

    async def _get_handler(self, model_id: UUID) -> BaseInferenceHandler:
        """Get or create inference handler for model."""
        if model_id in self._handlers:
            return self._handlers[model_id]

        model = self.registry.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        loaded_model = self.registry.get_loaded_model(model_id)

        # Create appropriate handler based on model type
        if model.model_type == ModelType.TEXT_GENERATION:
            handler = TextGenerationHandler(loaded_model, loaded_model)
        elif model.model_type in (ModelType.TEXT_TO_SPEECH, ModelType.VOICE_CLONING):
            handler = TTSHandler(loaded_model)
        elif model.model_type == ModelType.IMAGE_GENERATION:
            handler = ImageGenerationHandler(loaded_model)
        else:
            # Default handler that just passes through
            handler = self._create_default_handler(loaded_model)

        self._handlers[model_id] = handler
        return handler

    def _create_default_handler(self, model: Any) -> BaseInferenceHandler:
        """Create a default passthrough handler."""

        class DefaultHandler(BaseInferenceHandler):
            def __init__(self, model):
                self.model = model

            async def preprocess(self, input_data):
                return input_data

            async def inference(self, preprocessed, params):
                return preprocessed

            async def postprocess(self, model_output):
                return model_output

        return DefaultHandler(model)

    def get_request(self, request_id: UUID) -> Optional[InferenceRequest]:
        """Get request by ID."""
        if request_id in self._active_requests:
            return self._active_requests[request_id]
        return self._completed_requests.get(request_id)

    def get_queue_length(self) -> int:
        """Get current queue length."""
        return self._queue.qsize()

    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            "running": self._running,
            "queue_length": self._queue.qsize(),
            "active_requests": len(self._active_requests),
            "completed_requests": len(self._completed_requests),
            "total_requests": self._total_requests,
            "total_inference_time_ms": self._total_inference_time_ms,
            "avg_inference_time_ms": (
                self._total_inference_time_ms / self._total_requests
                if self._total_requests > 0
                else 0
            ),
            "loaded_handlers": len(self._handlers),
        }

    async def warm_up(self, model_id: UUID) -> None:
        """
        Warm up a model with a dummy inference.

        Useful for reducing cold start latency.
        """
        model = self.registry.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Load model if not loaded
        if not self.registry.is_loaded(model_id):
            await self.registry.load(model_id, self.config.device)

        # Run dummy inference based on model type
        dummy_inputs = {
            ModelType.TEXT_GENERATION: "Hello, world!",
            ModelType.TEXT_TO_SPEECH: "Test audio.",
            ModelType.IMAGE_GENERATION: "A test image",
            ModelType.SPEECH_TO_TEXT: b"",  # Would be audio bytes
        }

        dummy_input = dummy_inputs.get(model.model_type, "test")

        try:
            await self.infer(model_id, dummy_input, timeout=60)
            logger.info(f"Model {model.name} warmed up successfully")
        except Exception as e:
            logger.warning(f"Warm-up failed for {model.name}: {e}")
