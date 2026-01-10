"""
GPU Job Dispatcher

Manages GPU job queue and routes jobs to the best available provider.
Supports auto-scaling, priority queuing, and cost optimization.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional
from uuid import UUID

from app.gpu.interfaces import (
    GPUInstance,
    GPUInstanceConfig,
    GPUInstanceStatus,
    GPUJob,
    GPUJobConfig,
    GPUJobPriority,
    GPUJobStatus,
    GPUProvider,
)

logger = logging.getLogger(__name__)


class ProviderSelectionStrategy(str, Enum):
    """Strategy for selecting GPU provider."""
    LOWEST_COST = "lowest_cost"
    FASTEST_AVAILABLE = "fastest_available"
    PREFERRED_PROVIDER = "preferred_provider"
    ROUND_ROBIN = "round_robin"


@dataclass
class ProviderHealth:
    """Health status for a GPU provider."""
    provider_name: str
    is_healthy: bool = True
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    success_rate: float = 1.0
    avg_response_time_ms: float = 0.0
    active_jobs: int = 0
    failed_jobs_last_hour: int = 0


@dataclass
class QueuedJob:
    """A job waiting in the queue."""
    job_config: GPUJobConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def priority_score(self) -> float:
        """Calculate priority score for queue ordering."""
        # Higher priority value = higher priority
        base_score = self.job_config.priority.value * 100

        # Age bonus: +1 point per minute waiting
        age_minutes = (datetime.utcnow() - self.created_at).total_seconds() / 60
        age_bonus = min(age_minutes, 30)  # Cap at 30 points

        # Retry penalty: -5 points per attempt
        retry_penalty = self.attempts * 5

        return base_score + age_bonus - retry_penalty


class GPUDispatcher:
    """
    Central dispatcher for GPU jobs across multiple providers.

    Features:
    - Priority queue with aging
    - Multi-provider support with health monitoring
    - Cost optimization
    - Auto-scaling based on queue depth
    - Retry with exponential backoff
    - WebSocket progress streaming
    """

    def __init__(
        self,
        providers: Optional[dict[str, GPUProvider]] = None,
        selection_strategy: ProviderSelectionStrategy = ProviderSelectionStrategy.LOWEST_COST,
        max_concurrent_jobs: int = 10,
        job_callback: Optional[Callable[[GPUJob], None]] = None,
    ):
        """
        Initialize GPU dispatcher.

        Args:
            providers: Dict of provider name to provider instance
            selection_strategy: How to select provider for jobs
            max_concurrent_jobs: Maximum concurrent jobs
            job_callback: Callback for job status updates
        """
        self.providers = providers or {}
        self.selection_strategy = selection_strategy
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_callback = job_callback

        # Job tracking
        self._queue: list[QueuedJob] = []
        self._active_jobs: dict[str, GPUJob] = {}
        self._completed_jobs: dict[str, GPUJob] = {}

        # Provider health
        self._provider_health: dict[str, ProviderHealth] = {}
        for name in self.providers:
            self._provider_health[name] = ProviderHealth(provider_name=name)

        # Instance pool for reuse
        self._instance_pool: dict[str, list[GPUInstance]] = {}

        # Background tasks
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

    def add_provider(self, name: str, provider: GPUProvider) -> None:
        """Add a GPU provider."""
        self.providers[name] = provider
        self._provider_health[name] = ProviderHealth(provider_name=name)
        self._instance_pool[name] = []

    def remove_provider(self, name: str) -> None:
        """Remove a GPU provider."""
        if name in self.providers:
            del self.providers[name]
            del self._provider_health[name]

    async def start(self) -> None:
        """Start the dispatcher background tasks."""
        if self._running:
            return

        self._running = True
        self._process_task = asyncio.create_task(self._process_queue_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("GPU dispatcher started")

    async def stop(self) -> None:
        """Stop the dispatcher."""
        self._running = False

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("GPU dispatcher stopped")

    async def submit_job(
        self,
        job_config: GPUJobConfig,
        preferred_provider: Optional[str] = None,
    ) -> GPUJob:
        """
        Submit a job to the queue.

        Args:
            job_config: Job configuration
            preferred_provider: Optional preferred provider

        Returns:
            Initial job status
        """
        if preferred_provider:
            job_config.labels["preferred_provider"] = preferred_provider

        queued = QueuedJob(job_config=job_config)
        self._queue.append(queued)

        # Sort queue by priority
        self._queue.sort(key=lambda x: x.priority_score, reverse=True)

        job = GPUJob(
            job_id=job_config.job_id,
            config=job_config,
            status=GPUJobStatus.QUEUED,
            provider="pending",
            created_at=datetime.utcnow(),
        )

        logger.info(
            f"Job {job_config.job_id} queued with priority {job_config.priority.name}"
        )

        return job

    async def get_job(self, job_id: str) -> Optional[GPUJob]:
        """Get job by ID."""
        # Check active jobs
        if job_id in self._active_jobs:
            return self._active_jobs[job_id]

        # Check completed jobs
        if job_id in self._completed_jobs:
            return self._completed_jobs[job_id]

        # Check queue
        for queued in self._queue:
            if queued.job_config.job_id == job_id:
                return GPUJob(
                    job_id=job_id,
                    config=queued.job_config,
                    status=GPUJobStatus.QUEUED,
                    provider="pending",
                    created_at=queued.created_at,
                )

        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        # Remove from queue
        for i, queued in enumerate(self._queue):
            if queued.job_config.job_id == job_id:
                del self._queue[i]
                logger.info(f"Job {job_id} removed from queue")
                return True

        # Cancel active job
        if job_id in self._active_jobs:
            job = self._active_jobs[job_id]
            provider = self.providers.get(job.provider)
            if provider:
                await provider.cancel_job(job_id)
            job.status = GPUJobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            self._completed_jobs[job_id] = job
            del self._active_jobs[job_id]
            logger.info(f"Job {job_id} cancelled")
            return True

        return False

    async def _process_queue_loop(self) -> None:
        """Background loop to process job queue."""
        while self._running:
            try:
                await self._process_queue()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)

    async def _process_queue(self) -> None:
        """Process pending jobs in queue."""
        if not self._queue:
            return

        if len(self._active_jobs) >= self.max_concurrent_jobs:
            return

        # Get next job from queue
        queued = self._queue[0]

        # Check if we can process this job
        available_capacity = self.max_concurrent_jobs - len(self._active_jobs)
        if available_capacity <= 0:
            return

        # Select provider
        provider_name = await self._select_provider(queued.job_config)
        if not provider_name:
            logger.warning(f"No provider available for job {queued.job_config.job_id}")
            return

        provider = self.providers[provider_name]

        # Remove from queue
        self._queue.pop(0)

        # Start job
        try:
            queued.attempts += 1
            queued.last_attempt = datetime.utcnow()

            # Check for available instance in pool
            instance_id = await self._get_pooled_instance(
                provider_name,
                queued.job_config.instance_config,
            )

            job = await provider.run_job(queued.job_config, instance_id)
            job.provider = provider_name

            self._active_jobs[job.job_id] = job
            self._provider_health[provider_name].active_jobs += 1

            logger.info(
                f"Job {job.job_id} started on {provider_name} "
                f"(instance: {job.instance_id})"
            )

            # Start monitoring task
            asyncio.create_task(self._monitor_job(job))

            if self.job_callback:
                self.job_callback(job)

        except Exception as e:
            logger.error(f"Failed to start job {queued.job_config.job_id}: {e}")
            queued.last_error = str(e)

            # Retry if under max retries
            if queued.attempts < queued.job_config.max_retries:
                self._queue.append(queued)
                self._queue.sort(key=lambda x: x.priority_score, reverse=True)
            else:
                # Mark as failed
                failed_job = GPUJob(
                    job_id=queued.job_config.job_id,
                    config=queued.job_config,
                    status=GPUJobStatus.FAILED,
                    provider=provider_name,
                    error_message=str(e),
                    retry_count=queued.attempts,
                    created_at=queued.created_at,
                    completed_at=datetime.utcnow(),
                )
                self._completed_jobs[failed_job.job_id] = failed_job

                if self.job_callback:
                    self.job_callback(failed_job)

    async def _select_provider(
        self,
        job_config: GPUJobConfig,
    ) -> Optional[str]:
        """Select best provider for job."""
        # Check for preferred provider
        preferred = job_config.labels.get("preferred_provider")
        if preferred and preferred in self.providers:
            health = self._provider_health.get(preferred)
            if health and health.is_healthy:
                return preferred

        # Filter healthy providers
        healthy_providers = [
            name for name, health in self._provider_health.items()
            if health.is_healthy and name in self.providers
        ]

        if not healthy_providers:
            return None

        if self.selection_strategy == ProviderSelectionStrategy.LOWEST_COST:
            return await self._select_lowest_cost(healthy_providers, job_config)
        elif self.selection_strategy == ProviderSelectionStrategy.FASTEST_AVAILABLE:
            return await self._select_fastest(healthy_providers)
        elif self.selection_strategy == ProviderSelectionStrategy.ROUND_ROBIN:
            return self._select_round_robin(healthy_providers)
        else:
            return healthy_providers[0]

    async def _select_lowest_cost(
        self,
        providers: list[str],
        job_config: GPUJobConfig,
    ) -> str:
        """Select provider with lowest cost for job requirements."""
        best_provider = None
        best_price = float("inf")

        for name in providers:
            provider = self.providers[name]
            try:
                offers = await provider.list_available_gpus(job_config.instance_config)
                if offers:
                    price = offers[0].get("price_per_hour", float("inf"))
                    if price < best_price:
                        best_price = price
                        best_provider = name
            except Exception as e:
                logger.warning(f"Failed to get offers from {name}: {e}")

        return best_provider or providers[0]

    async def _select_fastest(self, providers: list[str]) -> str:
        """Select provider with fastest response time."""
        # Sort by average response time
        sorted_providers = sorted(
            providers,
            key=lambda p: self._provider_health[p].avg_response_time_ms,
        )
        return sorted_providers[0]

    def _select_round_robin(self, providers: list[str]) -> str:
        """Select provider using round-robin."""
        # Sort by active jobs (least busy first)
        sorted_providers = sorted(
            providers,
            key=lambda p: self._provider_health[p].active_jobs,
        )
        return sorted_providers[0]

    async def _get_pooled_instance(
        self,
        provider_name: str,
        config: GPUInstanceConfig,
    ) -> Optional[str]:
        """Get an available instance from pool."""
        pool = self._instance_pool.get(provider_name, [])

        for instance in pool:
            if instance.status == GPUInstanceStatus.RUNNING:
                # Check if specs match
                if (
                    instance.gpu_spec
                    and instance.gpu_spec.vram_gb >= config.min_vram_gb
                    and instance.gpu_count >= config.gpu_count
                ):
                    return instance.instance_id

        return None

    async def _monitor_job(self, job: GPUJob) -> None:
        """Monitor job progress until completion."""
        provider = self.providers.get(job.provider)
        if not provider:
            return

        try:
            async for update in provider.stream_job_progress(job.job_id):
                # Update job state
                job.status = update.status
                job.progress = update.progress
                job.progress_message = update.progress_message
                job.output_urls = update.output_urls
                job.result_data = update.result_data
                job.error_message = update.error_message

                if self.job_callback:
                    self.job_callback(job)

                if update.status in (
                    GPUJobStatus.COMPLETED,
                    GPUJobStatus.FAILED,
                    GPUJobStatus.CANCELLED,
                    GPUJobStatus.TIMEOUT,
                ):
                    break

        except Exception as e:
            logger.error(f"Error monitoring job {job.job_id}: {e}")
            job.status = GPUJobStatus.FAILED
            job.error_message = str(e)

        finally:
            # Move to completed
            job.completed_at = datetime.utcnow()

            if job.job_id in self._active_jobs:
                del self._active_jobs[job.job_id]

            self._completed_jobs[job.job_id] = job
            self._provider_health[job.provider].active_jobs -= 1

            # Update success rate
            health = self._provider_health[job.provider]
            if job.status == GPUJobStatus.FAILED:
                health.failed_jobs_last_hour += 1
                health.success_rate = max(0.5, health.success_rate - 0.05)
            else:
                health.success_rate = min(1.0, health.success_rate + 0.01)

            logger.info(
                f"Job {job.job_id} completed with status {job.status.value}"
            )

            # Return instance to pool if reusable
            if job.instance_id and job.status == GPUJobStatus.COMPLETED:
                await self._return_instance_to_pool(job.provider, job.instance_id)

    async def _return_instance_to_pool(
        self,
        provider_name: str,
        instance_id: str,
    ) -> None:
        """Return instance to pool for reuse."""
        provider = self.providers.get(provider_name)
        if not provider:
            return

        try:
            instance = await provider.get_instance(instance_id)
            if instance.status == GPUInstanceStatus.RUNNING:
                self._instance_pool.setdefault(provider_name, []).append(instance)
                logger.debug(f"Instance {instance_id} returned to pool")
        except Exception as e:
            logger.warning(f"Failed to return instance to pool: {e}")

    async def _health_check_loop(self) -> None:
        """Background loop for provider health checks."""
        while self._running:
            try:
                for name, provider in self.providers.items():
                    await self._check_provider_health(name, provider)
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(30)

    async def _check_provider_health(
        self,
        name: str,
        provider: GPUProvider,
    ) -> None:
        """Check health of a provider."""
        health = self._provider_health[name]
        start_time = datetime.utcnow()

        try:
            # Try to list available GPUs as health check
            await provider.list_available_gpus()

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            health.is_healthy = True
            health.last_check = datetime.utcnow()
            health.last_error = None
            health.avg_response_time_ms = (
                health.avg_response_time_ms * 0.8 + response_time * 0.2
            )

        except Exception as e:
            health.is_healthy = False
            health.last_check = datetime.utcnow()
            health.last_error = str(e)
            logger.warning(f"Provider {name} health check failed: {e}")

    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        return {
            "queue_length": len(self._queue),
            "active_jobs": len(self._active_jobs),
            "completed_jobs": len(self._completed_jobs),
            "provider_health": {
                name: {
                    "is_healthy": health.is_healthy,
                    "success_rate": health.success_rate,
                    "active_jobs": health.active_jobs,
                    "avg_response_time_ms": health.avg_response_time_ms,
                }
                for name, health in self._provider_health.items()
            },
        }

    async def estimate_wait_time(
        self,
        priority: GPUJobPriority = GPUJobPriority.NORMAL,
    ) -> dict:
        """Estimate wait time for a new job."""
        jobs_ahead = sum(
            1 for q in self._queue
            if q.job_config.priority.value >= priority.value
        )

        # Estimate based on average job duration (assume 10 min avg)
        avg_job_duration_minutes = 10
        estimated_minutes = (jobs_ahead / max(self.max_concurrent_jobs, 1)) * avg_job_duration_minutes

        return {
            "jobs_ahead": jobs_ahead,
            "estimated_wait_minutes": estimated_minutes,
            "active_jobs": len(self._active_jobs),
            "available_capacity": self.max_concurrent_jobs - len(self._active_jobs),
        }
