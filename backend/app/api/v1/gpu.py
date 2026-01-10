"""
GPU API Endpoints

REST API for GPU job management and provider operations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class GPUSpecResponse(BaseModel):
    """GPU specification."""
    name: str
    vram_gb: float
    cuda_cores: Optional[int] = None
    tensor_cores: Optional[int] = None


class GPUOfferResponse(BaseModel):
    """Available GPU offer."""
    offer_id: Optional[str] = None
    gpu_type_id: Optional[str] = None
    provider: str
    gpu_name: str
    gpu_count: int
    vram_gb: float
    ram_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    price_per_hour: float
    spot_price: Optional[float] = None
    on_demand_price: Optional[float] = None
    is_spot: bool = True
    region: Optional[str] = None
    reliability: Optional[float] = None


class GPUInstanceRequest(BaseModel):
    """Request to create a GPU instance."""
    min_vram_gb: float = Field(default=16.0, ge=1.0)
    gpu_count: int = Field(default=1, ge=1, le=8)
    preferred_gpus: list[str] = Field(default=["A100", "H100", "RTX 4090", "RTX 3090"])
    min_ram_gb: float = Field(default=32.0, ge=1.0)
    min_disk_gb: float = Field(default=50.0, ge=10.0)
    min_cpu_cores: int = Field(default=4, ge=1)
    docker_image: str = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"
    docker_command: Optional[str] = None
    environment: dict[str, str] = Field(default_factory=dict)
    ports: list[int] = Field(default_factory=list)
    persistent_disk_gb: Optional[float] = None
    max_price_per_hour: Optional[float] = None
    use_spot: bool = True
    max_runtime_hours: float = Field(default=4.0, ge=0.5, le=24.0)
    labels: dict[str, str] = Field(default_factory=dict)
    provider: Optional[str] = None


class GPUInstanceResponse(BaseModel):
    """GPU instance response."""
    instance_id: str
    provider: str
    status: str
    host: Optional[str] = None
    port: Optional[int] = None
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = None
    gpu_name: Optional[str] = None
    gpu_count: int = 1
    vram_gb: Optional[float] = None
    ram_gb: float = 0.0
    disk_gb: float = 0.0
    cpu_cores: int = 0
    price_per_hour: float = 0.0
    total_cost: float = 0.0
    public_ip: Optional[str] = None
    region: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None


class GPUJobRequest(BaseModel):
    """Request to submit a GPU job."""
    job_type: str = Field(default="inference", description="Type: inference, training, generation")
    script_url: Optional[str] = None
    command: Optional[str] = None
    input_urls: list[str] = Field(default_factory=list)
    output_path: str = "/outputs"
    model_name: Optional[str] = None
    model_url: Optional[str] = None
    instance_config: Optional[GPUInstanceRequest] = None
    instance_id: Optional[str] = Field(None, description="Use existing instance")
    priority: str = Field(default="normal", description="low, normal, high, urgent")
    webhook_url: Optional[str] = None
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)
    max_retries: int = Field(default=2, ge=0, le=5)
    labels: dict[str, str] = Field(default_factory=dict)
    provider: Optional[str] = Field(None, description="Preferred provider")


class GPUJobResponse(BaseModel):
    """GPU job response."""
    job_id: str
    status: str
    provider: str
    instance_id: Optional[str] = None
    progress: int = 0
    progress_message: Optional[str] = None
    output_urls: list[str] = Field(default_factory=list)
    result_data: dict = Field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    total_cost: float = 0.0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""
    queue_length: int
    active_jobs: int
    completed_jobs: int
    provider_health: dict[str, dict]


class WaitTimeEstimate(BaseModel):
    """Wait time estimate response."""
    jobs_ahead: int
    estimated_wait_minutes: float
    active_jobs: int
    available_capacity: int


class CostEstimate(BaseModel):
    """Cost estimate response."""
    estimated_cost: float
    price_per_hour: float
    gpu: str
    duration_hours: float
    provider: str


class AccountBalance(BaseModel):
    """Account balance response."""
    balance: float
    currency: str
    provider: str
    current_spend_per_hour: Optional[float] = None


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def get_gpu_dispatcher():
    """Get GPU dispatcher instance (dependency injection placeholder)."""
    # In production, this would return the actual dispatcher instance
    # from app state or dependency injection
    from app.gpu import GPUDispatcher
    from app.gpu.vastai import VastAIProvider
    from app.gpu.runpod import RunPodProvider
    from app.config import settings

    # Initialize providers
    providers = {}

    if hasattr(settings, 'VASTAI_API_KEY') and settings.VASTAI_API_KEY:
        providers['vastai'] = VastAIProvider(settings.VASTAI_API_KEY)

    if hasattr(settings, 'RUNPOD_API_KEY') and settings.RUNPOD_API_KEY:
        providers['runpod'] = RunPodProvider(settings.RUNPOD_API_KEY)

    return GPUDispatcher(providers=providers)


def convert_priority(priority_str: str) -> int:
    """Convert priority string to GPUJobPriority."""
    from app.gpu import GPUJobPriority

    priority_map = {
        "low": GPUJobPriority.LOW,
        "normal": GPUJobPriority.NORMAL,
        "high": GPUJobPriority.HIGH,
        "urgent": GPUJobPriority.URGENT,
    }
    return priority_map.get(priority_str.lower(), GPUJobPriority.NORMAL)


# --------------------------------------------------------------------------
# GPU Offer Endpoints
# --------------------------------------------------------------------------

@router.get("/offers", response_model=list[GPUOfferResponse])
async def list_gpu_offers(
    min_vram_gb: float = Query(default=16.0, ge=1.0),
    gpu_count: int = Query(default=1, ge=1),
    max_price_per_hour: Optional[float] = Query(default=None),
    use_spot: bool = Query(default=True),
    provider: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List available GPU offers from all providers.

    Returns offers sorted by price, matching the specified requirements.
    """
    from app.gpu import GPUInstanceConfig

    dispatcher = get_gpu_dispatcher()

    config = GPUInstanceConfig(
        min_vram_gb=min_vram_gb,
        gpu_count=gpu_count,
        max_price_per_hour=max_price_per_hour,
        use_spot=use_spot,
    )

    all_offers = []

    providers_to_query = [provider] if provider else list(dispatcher.providers.keys())

    for prov_name in providers_to_query:
        if prov_name not in dispatcher.providers:
            continue

        try:
            offers = await dispatcher.providers[prov_name].list_available_gpus(config)
            all_offers.extend(offers)
        except Exception as e:
            # Log but don't fail
            pass

    # Sort by price and limit
    all_offers.sort(key=lambda x: x.get("price_per_hour", float("inf")))
    all_offers = all_offers[:limit]

    return [GPUOfferResponse(**offer) for offer in all_offers]


@router.get("/offers/estimate", response_model=CostEstimate)
async def estimate_job_cost(
    min_vram_gb: float = Query(default=16.0, ge=1.0),
    gpu_count: int = Query(default=1, ge=1),
    duration_hours: float = Query(default=1.0, ge=0.1, le=24.0),
    use_spot: bool = Query(default=True),
    provider: Optional[str] = Query(default=None),
):
    """Estimate cost for running a GPU job."""
    from app.gpu import GPUInstanceConfig

    dispatcher = get_gpu_dispatcher()

    config = GPUInstanceConfig(
        min_vram_gb=min_vram_gb,
        gpu_count=gpu_count,
        use_spot=use_spot,
    )

    providers_to_query = [provider] if provider else list(dispatcher.providers.keys())

    for prov_name in providers_to_query:
        if prov_name not in dispatcher.providers:
            continue

        try:
            estimate = await dispatcher.providers[prov_name].estimate_cost(
                config, duration_hours
            )
            if "error" not in estimate:
                return CostEstimate(
                    **estimate,
                    provider=prov_name,
                )
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="No providers available for estimate")


# --------------------------------------------------------------------------
# Instance Management Endpoints
# --------------------------------------------------------------------------

@router.post("/instances", response_model=GPUInstanceResponse)
async def create_instance(
    request: GPUInstanceRequest,
):
    """
    Create a new GPU instance.

    The instance will be created on the specified or best available provider.
    """
    from app.gpu import GPUInstanceConfig

    dispatcher = get_gpu_dispatcher()

    config = GPUInstanceConfig(
        min_vram_gb=request.min_vram_gb,
        gpu_count=request.gpu_count,
        preferred_gpus=request.preferred_gpus,
        min_ram_gb=request.min_ram_gb,
        min_disk_gb=request.min_disk_gb,
        min_cpu_cores=request.min_cpu_cores,
        docker_image=request.docker_image,
        docker_command=request.docker_command,
        environment=request.environment,
        ports=request.ports,
        persistent_disk_gb=request.persistent_disk_gb,
        max_price_per_hour=request.max_price_per_hour,
        use_spot=request.use_spot,
        max_runtime_hours=request.max_runtime_hours,
        labels=request.labels,
    )

    provider_name = request.provider or next(iter(dispatcher.providers.keys()), None)

    if not provider_name or provider_name not in dispatcher.providers:
        raise HTTPException(status_code=400, detail="No GPU provider available")

    try:
        provider = dispatcher.providers[provider_name]
        instance = await provider.create_instance(config)

        return GPUInstanceResponse(
            instance_id=instance.instance_id,
            provider=instance.provider,
            status=instance.status.value,
            host=instance.host,
            port=instance.port,
            ssh_host=instance.ssh_host,
            ssh_port=instance.ssh_port,
            gpu_name=instance.gpu_spec.name if instance.gpu_spec else None,
            gpu_count=instance.gpu_count,
            vram_gb=instance.gpu_spec.vram_gb if instance.gpu_spec else None,
            ram_gb=instance.ram_gb,
            disk_gb=instance.disk_gb,
            cpu_cores=instance.cpu_cores,
            price_per_hour=instance.price_per_hour,
            total_cost=instance.total_cost,
            public_ip=instance.public_ip,
            region=instance.region,
            created_at=instance.created_at,
            started_at=instance.started_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}", response_model=GPUInstanceResponse)
async def get_instance(
    instance_id: str,
    provider: str = Query(..., description="Provider name"),
):
    """Get instance status and details."""
    dispatcher = get_gpu_dispatcher()

    if provider not in dispatcher.providers:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")

    try:
        instance = await dispatcher.providers[provider].get_instance(instance_id)

        return GPUInstanceResponse(
            instance_id=instance.instance_id,
            provider=instance.provider,
            status=instance.status.value,
            host=instance.host,
            port=instance.port,
            ssh_host=instance.ssh_host,
            ssh_port=instance.ssh_port,
            gpu_name=instance.gpu_spec.name if instance.gpu_spec else None,
            gpu_count=instance.gpu_count,
            vram_gb=instance.gpu_spec.vram_gb if instance.gpu_spec else None,
            ram_gb=instance.ram_gb,
            disk_gb=instance.disk_gb,
            cpu_cores=instance.cpu_cores,
            price_per_hour=instance.price_per_hour,
            total_cost=instance.total_cost,
            public_ip=instance.public_ip,
            region=instance.region,
            created_at=instance.created_at,
            started_at=instance.started_at,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/instances/{instance_id}/stop")
async def stop_instance(
    instance_id: str,
    provider: str = Query(..., description="Provider name"),
):
    """Stop a GPU instance (but keep it allocated)."""
    dispatcher = get_gpu_dispatcher()

    if provider not in dispatcher.providers:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")

    success = await dispatcher.providers[provider].stop_instance(instance_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop instance")

    return {"status": "stopped", "instance_id": instance_id}


@router.delete("/instances/{instance_id}")
async def destroy_instance(
    instance_id: str,
    provider: str = Query(..., description="Provider name"),
):
    """Destroy a GPU instance completely."""
    dispatcher = get_gpu_dispatcher()

    if provider not in dispatcher.providers:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")

    success = await dispatcher.providers[provider].destroy_instance(instance_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to destroy instance")

    return {"status": "destroyed", "instance_id": instance_id}


# --------------------------------------------------------------------------
# Job Management Endpoints
# --------------------------------------------------------------------------

@router.post("/jobs", response_model=GPUJobResponse)
async def submit_job(
    request: GPUJobRequest,
):
    """
    Submit a GPU job to the queue.

    Jobs are processed based on priority and availability.
    """
    from app.gpu import GPUJobConfig, GPUInstanceConfig

    dispatcher = get_gpu_dispatcher()

    # Build instance config if provided
    instance_config = None
    if request.instance_config:
        ic = request.instance_config
        instance_config = GPUInstanceConfig(
            min_vram_gb=ic.min_vram_gb,
            gpu_count=ic.gpu_count,
            preferred_gpus=ic.preferred_gpus,
            min_ram_gb=ic.min_ram_gb,
            min_disk_gb=ic.min_disk_gb,
            min_cpu_cores=ic.min_cpu_cores,
            docker_image=ic.docker_image,
            docker_command=ic.docker_command,
            environment=ic.environment,
            ports=ic.ports,
            persistent_disk_gb=ic.persistent_disk_gb,
            max_price_per_hour=ic.max_price_per_hour,
            use_spot=ic.use_spot,
            max_runtime_hours=ic.max_runtime_hours,
            labels=ic.labels,
        )
    else:
        instance_config = GPUInstanceConfig()

    job_config = GPUJobConfig(
        job_type=request.job_type,
        script_url=request.script_url,
        command=request.command,
        input_urls=request.input_urls,
        output_path=request.output_path,
        model_name=request.model_name,
        model_url=request.model_url,
        instance_config=instance_config,
        priority=convert_priority(request.priority),
        webhook_url=request.webhook_url,
        timeout_seconds=request.timeout_seconds,
        max_retries=request.max_retries,
        labels=request.labels,
    )

    try:
        job = await dispatcher.submit_job(job_config, preferred_provider=request.provider)

        return GPUJobResponse(
            job_id=job.job_id,
            status=job.status.value,
            provider=job.provider,
            instance_id=job.instance_id,
            progress=job.progress,
            progress_message=job.progress_message,
            output_urls=job.output_urls,
            result_data=job.result_data,
            error_message=job.error_message,
            retry_count=job.retry_count,
            total_cost=job.total_cost,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=GPUJobResponse)
async def get_job(
    job_id: str,
):
    """Get job status and results."""
    dispatcher = get_gpu_dispatcher()

    job = await dispatcher.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return GPUJobResponse(
        job_id=job.job_id,
        status=job.status.value,
        provider=job.provider,
        instance_id=job.instance_id,
        progress=job.progress,
        progress_message=job.progress_message,
        output_urls=job.output_urls,
        result_data=job.result_data,
        error_message=job.error_message,
        retry_count=job.retry_count,
        total_cost=job.total_cost,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
):
    """Cancel a queued or running job."""
    dispatcher = get_gpu_dispatcher()

    success = await dispatcher.cancel_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or cannot be cancelled")

    return {"status": "cancelled", "job_id": job_id}


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    tail: int = Query(default=100, ge=1, le=1000),
):
    """Get logs for a job."""
    dispatcher = get_gpu_dispatcher()

    job = await dispatcher.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.provider not in dispatcher.providers:
        raise HTTPException(status_code=400, detail="Provider not available")

    try:
        logs = await dispatcher.providers[job.provider].get_logs(job_id, tail)
        return {"job_id": job_id, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Queue & Stats Endpoints
# --------------------------------------------------------------------------

@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Get queue statistics and provider health."""
    dispatcher = get_gpu_dispatcher()

    stats = dispatcher.get_queue_stats()

    return QueueStatsResponse(**stats)


@router.get("/queue/wait-time", response_model=WaitTimeEstimate)
async def estimate_wait_time(
    priority: str = Query(default="normal"),
):
    """Estimate wait time for a new job."""
    dispatcher = get_gpu_dispatcher()

    estimate = await dispatcher.estimate_wait_time(convert_priority(priority))

    return WaitTimeEstimate(**estimate)


# --------------------------------------------------------------------------
# Provider Endpoints
# --------------------------------------------------------------------------

@router.get("/providers")
async def list_providers():
    """List available GPU providers and their status."""
    dispatcher = get_gpu_dispatcher()

    providers = []
    for name in dispatcher.providers:
        health = dispatcher._provider_health.get(name)
        providers.append({
            "name": name,
            "is_healthy": health.is_healthy if health else False,
            "success_rate": health.success_rate if health else 0,
            "active_jobs": health.active_jobs if health else 0,
            "supports_spot": dispatcher.providers[name].supports_spot_instances,
            "supports_persistent_disk": dispatcher.providers[name].supports_persistent_disk,
        })

    return {"providers": providers}


@router.get("/providers/{provider}/balance", response_model=AccountBalance)
async def get_provider_balance(
    provider: str,
):
    """Get account balance for a provider."""
    dispatcher = get_gpu_dispatcher()

    if provider not in dispatcher.providers:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")

    try:
        balance = await dispatcher.providers[provider].get_account_balance()
        return AccountBalance(**balance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
