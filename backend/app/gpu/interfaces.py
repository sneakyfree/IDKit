"""
GPU Provider Interface

Abstract interface for GPU rental providers (Vast.ai, RunPod, Lambda Labs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional
import uuid


class GPUInstanceStatus(str, Enum):
    """Status states for GPU instances."""
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class GPUJobStatus(str, Enum):
    """Status states for GPU jobs."""
    QUEUED = "queued"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class GPUJobPriority(int, Enum):
    """Priority levels for GPU jobs."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


@dataclass
class GPUSpec:
    """Specifications for a GPU."""
    name: str  # e.g., "RTX 4090", "A100"
    vram_gb: float
    cuda_cores: Optional[int] = None
    tensor_cores: Optional[int] = None
    compute_capability: Optional[str] = None
    memory_bandwidth_gbps: Optional[float] = None


@dataclass
class GPUInstanceConfig:
    """Configuration for requesting a GPU instance."""
    # Required specs
    min_vram_gb: float = 16.0
    gpu_count: int = 1

    # Preferred GPU models (in order of preference)
    preferred_gpus: list[str] = field(default_factory=lambda: [
        "A100", "H100", "RTX 4090", "RTX 3090", "A6000"
    ])

    # Instance requirements
    min_ram_gb: float = 32.0
    min_disk_gb: float = 50.0
    min_cpu_cores: int = 4

    # Docker image
    docker_image: str = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"
    docker_command: Optional[str] = None

    # Environment
    environment: dict[str, str] = field(default_factory=dict)

    # Networking
    ports: list[int] = field(default_factory=list)

    # Disk
    persistent_disk_gb: Optional[float] = None

    # Cost constraints
    max_price_per_hour: Optional[float] = None

    # Spot vs on-demand
    use_spot: bool = True

    # Timeout
    max_runtime_hours: float = 4.0

    # Labels for filtering
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class GPUInstance:
    """Represents a running GPU instance."""
    instance_id: str
    provider: str
    status: GPUInstanceStatus

    # Connection info
    host: Optional[str] = None
    port: Optional[int] = None
    ssh_port: Optional[int] = None
    ssh_host: Optional[str] = None

    # Specs
    gpu_spec: Optional[GPUSpec] = None
    gpu_count: int = 1
    ram_gb: float = 0.0
    disk_gb: float = 0.0
    cpu_cores: int = 0

    # Cost tracking
    price_per_hour: float = 0.0
    total_cost: float = 0.0

    # Timing
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    # Additional info
    region: Optional[str] = None
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None

    # Provider-specific metadata
    metadata: dict = field(default_factory=dict)


@dataclass
class GPUJobConfig:
    """Configuration for a GPU job."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Job type
    job_type: str = "inference"  # 'inference', 'training', 'generation'

    # Script or command to run
    script_url: Optional[str] = None
    command: Optional[str] = None

    # Input/output
    input_urls: list[str] = field(default_factory=list)
    output_path: str = "/outputs"

    # Model info
    model_name: Optional[str] = None
    model_url: Optional[str] = None

    # GPU requirements
    instance_config: GPUInstanceConfig = field(default_factory=GPUInstanceConfig)

    # Priority
    priority: GPUJobPriority = GPUJobPriority.NORMAL

    # Callback
    webhook_url: Optional[str] = None

    # Timeout
    timeout_seconds: int = 3600

    # Retry
    max_retries: int = 2

    # Job metadata
    user_id: Optional[str] = None
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class GPUJob:
    """Represents a GPU job."""
    job_id: str
    config: GPUJobConfig
    status: GPUJobStatus
    provider: str

    # Instance assignment
    instance_id: Optional[str] = None
    instance: Optional[GPUInstance] = None

    # Progress
    progress: int = 0  # 0-100
    progress_message: Optional[str] = None

    # Results
    output_urls: list[str] = field(default_factory=list)
    result_data: dict = field(default_factory=dict)

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0

    # Cost tracking
    total_cost: float = 0.0

    # Timing
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Logs
    logs_url: Optional[str] = None

    # Provider-specific metadata
    metadata: dict = field(default_factory=dict)


class GPUProvider(ABC):
    """
    Abstract interface for GPU rental providers.

    Implement this interface to add support for new GPU providers
    (Vast.ai, RunPod, Lambda Labs, etc.)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def supports_spot_instances(self) -> bool:
        """Whether this provider supports spot/interruptible instances."""
        pass

    @property
    @abstractmethod
    def supports_persistent_disk(self) -> bool:
        """Whether this provider supports persistent storage."""
        pass

    @abstractmethod
    async def list_available_gpus(
        self,
        config: Optional[GPUInstanceConfig] = None,
    ) -> list[dict]:
        """
        List available GPU offers matching the config.

        Args:
            config: Optional filter config

        Returns:
            List of available GPU offers with specs and pricing
        """
        pass

    @abstractmethod
    async def create_instance(
        self,
        config: GPUInstanceConfig,
    ) -> GPUInstance:
        """
        Create a new GPU instance.

        Args:
            config: Instance configuration

        Returns:
            Created instance info
        """
        pass

    @abstractmethod
    async def get_instance(
        self,
        instance_id: str,
    ) -> GPUInstance:
        """
        Get instance status and details.

        Args:
            instance_id: Instance ID

        Returns:
            Instance info
        """
        pass

    @abstractmethod
    async def stop_instance(
        self,
        instance_id: str,
    ) -> bool:
        """
        Stop an instance (but keep it allocated).

        Args:
            instance_id: Instance ID

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def destroy_instance(
        self,
        instance_id: str,
    ) -> bool:
        """
        Destroy an instance completely.

        Args:
            instance_id: Instance ID

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def run_job(
        self,
        job_config: GPUJobConfig,
        instance_id: Optional[str] = None,
    ) -> GPUJob:
        """
        Run a job on a GPU instance.

        If instance_id is not provided, will create a new instance.

        Args:
            job_config: Job configuration
            instance_id: Optional existing instance to use

        Returns:
            Job info
        """
        pass

    @abstractmethod
    async def get_job_status(
        self,
        job_id: str,
    ) -> GPUJob:
        """
        Get job status and results.

        Args:
            job_id: Job ID

        Returns:
            Job info
        """
        pass

    @abstractmethod
    async def cancel_job(
        self,
        job_id: str,
    ) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            Success status
        """
        pass

    async def stream_job_progress(
        self,
        job_id: str,
        poll_interval: float = 5.0,
    ) -> AsyncIterator[GPUJob]:
        """
        Stream job progress updates.

        Default implementation polls get_job_status.
        Override for webhook-based providers.

        Args:
            job_id: Job ID to monitor
            poll_interval: Seconds between status checks

        Yields:
            Progress updates until completion
        """
        import asyncio

        while True:
            job = await self.get_job_status(job_id)
            yield job

            if job.status in (
                GPUJobStatus.COMPLETED,
                GPUJobStatus.FAILED,
                GPUJobStatus.CANCELLED,
                GPUJobStatus.TIMEOUT,
            ):
                break

            await asyncio.sleep(poll_interval)

    async def get_logs(
        self,
        job_id: str,
        tail: int = 100,
    ) -> str:
        """
        Get job logs.

        Args:
            job_id: Job ID
            tail: Number of lines from end

        Returns:
            Log content
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support log retrieval"
        )

    async def get_account_balance(self) -> dict:
        """
        Get account balance and usage info.

        Returns:
            Balance and usage data
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support balance queries"
        )

    async def estimate_cost(
        self,
        config: GPUInstanceConfig,
        duration_hours: float,
    ) -> dict:
        """
        Estimate cost for running an instance.

        Args:
            config: Instance config
            duration_hours: Estimated runtime

        Returns:
            Cost estimate with breakdown
        """
        offers = await self.list_available_gpus(config)
        if not offers:
            return {"error": "No matching GPUs available"}

        best_offer = offers[0]
        return {
            "estimated_cost": best_offer.get("price_per_hour", 0) * duration_hours,
            "price_per_hour": best_offer.get("price_per_hour", 0),
            "gpu": best_offer.get("gpu_name", "Unknown"),
            "duration_hours": duration_hours,
        }
