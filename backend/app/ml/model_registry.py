"""
Model Registry

Central registry for managing ML models, their versions, and deployment status.
Supports both cloud-based and self-hosted models.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of ML models supported."""
    # Avatar/Video
    AVATAR_GENERATION = "avatar_generation"
    LIP_SYNC = "lip_sync"
    FACE_SWAP = "face_swap"
    VIDEO_ENHANCEMENT = "video_enhancement"

    # Voice
    VOICE_CLONING = "voice_cloning"
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"
    VOICE_CONVERSION = "voice_conversion"

    # Text/NLP
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONTENT_MODERATION = "content_moderation"

    # Image
    IMAGE_GENERATION = "image_generation"
    IMAGE_ENHANCEMENT = "image_enhancement"
    BACKGROUND_REMOVAL = "background_removal"
    STYLE_TRANSFER = "style_transfer"

    # Audio
    AUDIO_ENHANCEMENT = "audio_enhancement"
    MUSIC_GENERATION = "music_generation"
    AUDIO_SEPARATION = "audio_separation"


class ModelStatus(str, Enum):
    """Model deployment status."""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DEPRECATED = "deprecated"


class ModelSource(str, Enum):
    """Where the model is hosted."""
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    CUSTOM_URL = "custom_url"


@dataclass
class ModelRequirements:
    """Hardware requirements for a model."""
    min_vram_gb: float = 0.0
    recommended_vram_gb: float = 0.0
    min_ram_gb: float = 0.0
    disk_space_gb: float = 0.0
    requires_gpu: bool = True
    supported_gpus: list[str] = field(default_factory=list)
    cuda_version: Optional[str] = None
    python_version: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about a registered model."""
    id: UUID
    name: str
    model_type: ModelType
    version: str
    description: str = ""

    # Source information
    source: ModelSource = ModelSource.HUGGINGFACE
    source_path: str = ""  # HuggingFace ID, S3 path, or local path

    # Requirements
    requirements: ModelRequirements = field(default_factory=ModelRequirements)

    # Status
    status: ModelStatus = ModelStatus.AVAILABLE
    local_path: Optional[str] = None
    loaded_at: Optional[datetime] = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    license: str = ""
    author: str = ""
    paper_url: Optional[str] = None
    model_card_url: Optional[str] = None

    # Performance metrics
    inference_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    # Configuration
    config: dict = field(default_factory=dict)
    default_params: dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ModelRegistry:
    """
    Central registry for ML models.

    Manages model discovery, downloading, loading, and versioning.
    """

    # Pre-configured open-source models
    BUILTIN_MODELS: dict[str, dict] = {
        # Avatar/Video Models
        "sadtalker": {
            "name": "SadTalker",
            "model_type": ModelType.LIP_SYNC,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "vinthony/SadTalker",
            "description": "Audio-driven talking face generation",
            "requirements": ModelRequirements(
                min_vram_gb=4.0,
                recommended_vram_gb=8.0,
                disk_space_gb=5.0,
            ),
            "license": "MIT",
        },
        "wav2lip": {
            "name": "Wav2Lip",
            "model_type": ModelType.LIP_SYNC,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "numz/wav2lip_studio",
            "description": "Lip-sync from audio to video",
            "requirements": ModelRequirements(
                min_vram_gb=2.0,
                recommended_vram_gb=4.0,
                disk_space_gb=1.0,
            ),
            "license": "Apache-2.0",
        },
        "gfpgan": {
            "name": "GFPGAN",
            "model_type": ModelType.VIDEO_ENHANCEMENT,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "TencentARC/GFPGAN",
            "description": "Face restoration and enhancement",
            "requirements": ModelRequirements(
                min_vram_gb=2.0,
                recommended_vram_gb=4.0,
                disk_space_gb=1.0,
            ),
            "license": "Apache-2.0",
        },

        # Voice Models
        "coqui-xtts": {
            "name": "Coqui XTTS",
            "model_type": ModelType.VOICE_CLONING,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "coqui/XTTS-v2",
            "description": "Multilingual voice cloning and TTS",
            "requirements": ModelRequirements(
                min_vram_gb=4.0,
                recommended_vram_gb=6.0,
                disk_space_gb=3.0,
            ),
            "license": "MPL-2.0",
        },
        "tortoise-tts": {
            "name": "Tortoise TTS",
            "model_type": ModelType.TEXT_TO_SPEECH,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "jbetker/tortoise-tts-v2",
            "description": "High-quality multi-voice TTS",
            "requirements": ModelRequirements(
                min_vram_gb=6.0,
                recommended_vram_gb=10.0,
                disk_space_gb=4.0,
            ),
            "license": "Apache-2.0",
        },
        "bark": {
            "name": "Bark",
            "model_type": ModelType.TEXT_TO_SPEECH,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "suno/bark",
            "description": "Generative audio model with emotions",
            "requirements": ModelRequirements(
                min_vram_gb=4.0,
                recommended_vram_gb=8.0,
                disk_space_gb=5.0,
            ),
            "license": "MIT",
        },
        "whisper-large": {
            "name": "Whisper Large",
            "model_type": ModelType.SPEECH_TO_TEXT,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "openai/whisper-large-v3",
            "description": "Speech recognition and transcription",
            "requirements": ModelRequirements(
                min_vram_gb=4.0,
                recommended_vram_gb=6.0,
                disk_space_gb=3.0,
            ),
            "license": "MIT",
        },

        # Text/NLP Models
        "llama-3-8b": {
            "name": "Llama 3 8B",
            "model_type": ModelType.TEXT_GENERATION,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "meta-llama/Meta-Llama-3-8B-Instruct",
            "description": "Meta's latest instruction-tuned LLM",
            "requirements": ModelRequirements(
                min_vram_gb=16.0,
                recommended_vram_gb=24.0,
                disk_space_gb=16.0,
            ),
            "license": "Llama 3 Community",
        },
        "mistral-7b": {
            "name": "Mistral 7B",
            "model_type": ModelType.TEXT_GENERATION,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "mistralai/Mistral-7B-Instruct-v0.2",
            "description": "Efficient instruction-tuned model",
            "requirements": ModelRequirements(
                min_vram_gb=14.0,
                recommended_vram_gb=16.0,
                disk_space_gb=14.0,
            ),
            "license": "Apache-2.0",
        },
        "phi-3-mini": {
            "name": "Phi-3 Mini",
            "model_type": ModelType.TEXT_GENERATION,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "microsoft/Phi-3-mini-4k-instruct",
            "description": "Compact but capable LLM",
            "requirements": ModelRequirements(
                min_vram_gb=6.0,
                recommended_vram_gb=8.0,
                disk_space_gb=8.0,
            ),
            "license": "MIT",
        },

        # Image Models
        "sdxl": {
            "name": "Stable Diffusion XL",
            "model_type": ModelType.IMAGE_GENERATION,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "stabilityai/stable-diffusion-xl-base-1.0",
            "description": "High-resolution image generation",
            "requirements": ModelRequirements(
                min_vram_gb=8.0,
                recommended_vram_gb=12.0,
                disk_space_gb=10.0,
            ),
            "license": "CreativeML Open RAIL++-M",
        },
        "rembg": {
            "name": "RemBG",
            "model_type": ModelType.BACKGROUND_REMOVAL,
            "source": ModelSource.HUGGINGFACE,
            "source_path": "briaai/RMBG-1.4",
            "description": "Background removal from images",
            "requirements": ModelRequirements(
                min_vram_gb=2.0,
                recommended_vram_gb=4.0,
                disk_space_gb=1.0,
            ),
            "license": "Apache-2.0",
        },
    }

    def __init__(
        self,
        models_dir: str = "/var/lib/idkit/models",
        cache_dir: str = "/var/cache/idkit/models",
    ):
        """
        Initialize model registry.

        Args:
            models_dir: Directory for persistent model storage
            cache_dir: Directory for model cache
        """
        self.models_dir = Path(models_dir)
        self.cache_dir = Path(cache_dir)
        self._models: dict[UUID, ModelInfo] = {}
        self._models_by_name: dict[str, UUID] = {}
        self._loaded_models: dict[UUID, Any] = {}

        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Register builtin models
        self._register_builtin_models()

    def _register_builtin_models(self) -> None:
        """Register all builtin models."""
        for key, config in self.BUILTIN_MODELS.items():
            model = ModelInfo(
                id=uuid4(),
                name=config["name"],
                model_type=config["model_type"],
                version="latest",
                description=config.get("description", ""),
                source=config.get("source", ModelSource.HUGGINGFACE),
                source_path=config.get("source_path", ""),
                requirements=config.get("requirements", ModelRequirements()),
                license=config.get("license", ""),
                tags=[key],
            )
            self._models[model.id] = model
            self._models_by_name[key] = model.id

    def register(
        self,
        name: str,
        model_type: ModelType,
        source: ModelSource,
        source_path: str,
        version: str = "latest",
        description: str = "",
        requirements: Optional[ModelRequirements] = None,
        config: Optional[dict] = None,
    ) -> ModelInfo:
        """
        Register a new model.

        Args:
            name: Model name
            model_type: Type of model
            source: Where model is hosted
            source_path: Path to model
            version: Model version
            description: Model description
            requirements: Hardware requirements
            config: Model configuration

        Returns:
            Registered model info
        """
        model = ModelInfo(
            id=uuid4(),
            name=name,
            model_type=model_type,
            version=version,
            description=description,
            source=source,
            source_path=source_path,
            requirements=requirements or ModelRequirements(),
            config=config or {},
        )

        self._models[model.id] = model
        self._models_by_name[name.lower().replace(" ", "-")] = model.id

        logger.info(f"Registered model: {name} ({model.id})")
        return model

    def get(self, model_id: UUID) -> Optional[ModelInfo]:
        """Get model by ID."""
        return self._models.get(model_id)

    def get_by_name(self, name: str) -> Optional[ModelInfo]:
        """Get model by name."""
        model_id = self._models_by_name.get(name.lower().replace(" ", "-"))
        if model_id:
            return self._models.get(model_id)
        return None

    def list_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
    ) -> list[ModelInfo]:
        """List all registered models."""
        models = list(self._models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if status:
            models = [m for m in models if m.status == status]

        return models

    def list_by_type(self, model_type: ModelType) -> list[ModelInfo]:
        """List models by type."""
        return [m for m in self._models.values() if m.model_type == model_type]

    async def download(
        self,
        model_id: UUID,
        force: bool = False,
    ) -> str:
        """
        Download model to local storage.

        Args:
            model_id: Model ID
            force: Force re-download even if exists

        Returns:
            Local path to model
        """
        model = self._models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        local_path = self.models_dir / str(model_id)

        if local_path.exists() and not force:
            model.local_path = str(local_path)
            model.status = ModelStatus.READY
            return str(local_path)

        model.status = ModelStatus.DOWNLOADING
        logger.info(f"Downloading model {model.name} from {model.source_path}")

        try:
            if model.source == ModelSource.HUGGINGFACE:
                await self._download_from_huggingface(model, local_path)
            elif model.source == ModelSource.S3:
                await self._download_from_s3(model, local_path)
            elif model.source == ModelSource.LOCAL:
                # Already local, just verify
                if not Path(model.source_path).exists():
                    raise FileNotFoundError(f"Local model not found: {model.source_path}")
                model.local_path = model.source_path
            else:
                await self._download_from_url(model, local_path)

            model.local_path = str(local_path)
            model.status = ModelStatus.READY
            model.updated_at = datetime.utcnow()

            logger.info(f"Model {model.name} downloaded to {local_path}")
            return str(local_path)

        except Exception as e:
            model.status = ModelStatus.ERROR
            logger.error(f"Failed to download model {model.name}: {e}")
            raise

    async def _download_from_huggingface(
        self,
        model: ModelInfo,
        local_path: Path,
    ) -> None:
        """Download model from HuggingFace Hub."""
        try:
            from huggingface_hub import snapshot_download

            snapshot_download(
                repo_id=model.source_path,
                local_dir=str(local_path),
                cache_dir=str(self.cache_dir),
            )
        except ImportError:
            raise RuntimeError("huggingface_hub not installed")

    async def _download_from_s3(
        self,
        model: ModelInfo,
        local_path: Path,
    ) -> None:
        """
        Download model from S3.

        Supports both single files and directory structures.
        source_path format: s3://bucket/prefix or bucket/prefix
        """
        import asyncio

        try:
            import aioboto3
        except ImportError:
            raise RuntimeError("aioboto3 not installed. Run: pip install aioboto3")

        from app.config import settings

        # Parse S3 path
        s3_path = model.source_path
        if s3_path.startswith("s3://"):
            s3_path = s3_path[5:]

        parts = s3_path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 path format: {model.source_path}")

        bucket_name = parts[0]
        prefix = parts[1]

        # Create local directory
        local_path.mkdir(parents=True, exist_ok=True)

        session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=getattr(settings, "aws_region", "us-east-1"),
        )

        async with session.client("s3") as s3_client:
            # List all objects under the prefix
            paginator = s3_client.get_paginator("list_objects_v2")
            total_size = 0
            downloaded_size = 0

            # First pass: calculate total size
            objects_to_download = []
            async for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    size = obj["Size"]
                    total_size += size
                    objects_to_download.append((key, size))

            if not objects_to_download:
                raise ValueError(f"No objects found at s3://{bucket_name}/{prefix}")

            logger.info(
                f"Downloading {len(objects_to_download)} files "
                f"({total_size / (1024*1024):.1f} MB) for model {model.name}"
            )

            # Second pass: download files
            for key, size in objects_to_download:
                # Compute relative path from prefix
                relative_path = key[len(prefix):].lstrip("/")
                if not relative_path:
                    # Single file, use the filename from key
                    relative_path = key.split("/")[-1]

                file_path = local_path / relative_path

                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Download file
                try:
                    await s3_client.download_file(bucket_name, key, str(file_path))
                    downloaded_size += size

                    progress = (downloaded_size / total_size) * 100 if total_size > 0 else 100
                    logger.debug(
                        f"Downloaded {relative_path} ({progress:.1f}% complete)"
                    )

                except Exception as e:
                    logger.error(f"Failed to download {key}: {e}")
                    raise

            logger.info(f"Successfully downloaded model {model.name} to {local_path}")

    async def _download_from_url(
        self,
        model: ModelInfo,
        local_path: Path,
    ) -> None:
        """Download model from URL."""
        import httpx

        local_path.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient() as client:
            response = await client.get(model.source_path)
            response.raise_for_status()

            file_path = local_path / "model.bin"
            file_path.write_bytes(response.content)

    async def load(
        self,
        model_id: UUID,
        device: str = "cuda",
    ) -> Any:
        """
        Load model into memory.

        Args:
            model_id: Model ID
            device: Device to load to (cuda, cpu)

        Returns:
            Loaded model instance
        """
        if model_id in self._loaded_models:
            return self._loaded_models[model_id]

        model = self._models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        if not model.local_path:
            await self.download(model_id)

        model.status = ModelStatus.LOADING
        logger.info(f"Loading model {model.name}")

        try:
            # Model loading is type-specific
            loaded = await self._load_model(model, device)
            self._loaded_models[model_id] = loaded

            model.status = ModelStatus.READY
            model.loaded_at = datetime.utcnow()

            logger.info(f"Model {model.name} loaded successfully")
            return loaded

        except Exception as e:
            model.status = ModelStatus.ERROR
            logger.error(f"Failed to load model {model.name}: {e}")
            raise

    async def _load_model(
        self,
        model: ModelInfo,
        device: str,
    ) -> Any:
        """Load model based on type."""
        # This would be implemented per model type
        # For now, return a placeholder
        return {"model": model.name, "device": device, "path": model.local_path}

    def unload(self, model_id: UUID) -> bool:
        """
        Unload model from memory.

        Args:
            model_id: Model ID

        Returns:
            True if unloaded
        """
        if model_id not in self._loaded_models:
            return False

        del self._loaded_models[model_id]

        model = self._models.get(model_id)
        if model:
            model.loaded_at = None

        logger.info(f"Model {model_id} unloaded")
        return True

    def is_loaded(self, model_id: UUID) -> bool:
        """Check if model is loaded."""
        return model_id in self._loaded_models

    def get_loaded_model(self, model_id: UUID) -> Optional[Any]:
        """Get loaded model instance."""
        return self._loaded_models.get(model_id)

    def get_stats(self) -> dict:
        """Get registry statistics."""
        return {
            "total_models": len(self._models),
            "loaded_models": len(self._loaded_models),
            "by_type": {
                mt.value: len(self.list_by_type(mt))
                for mt in ModelType
            },
            "by_status": {
                ms.value: len([m for m in self._models.values() if m.status == ms])
                for ms in ModelStatus
            },
        }
