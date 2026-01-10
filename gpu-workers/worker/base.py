"""
Base GPU Worker

Abstract base class for all GPU workers with common functionality.
"""

import asyncio
import json
import logging
import os
import signal
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

import aiohttp
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkerConfig:
    """Worker configuration."""
    # Identity
    worker_id: str = field(default_factory=lambda: str(uuid4()))
    worker_type: str = "base"

    # Backend connection
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    api_key: str = os.getenv("WORKER_API_KEY", "")

    # Redis for job queue
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Job processing
    job_queue: str = "gpu_jobs"
    max_concurrent_jobs: int = 1
    job_timeout: int = 600  # 10 minutes
    heartbeat_interval: int = 30

    # Model configuration
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "/app/cache/models")
    device: str = os.getenv("DEVICE", "cuda")

    # Metrics
    metrics_enabled: bool = True
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))


@dataclass
class Job:
    """GPU job to process."""
    id: UUID
    job_type: str
    input_data: dict
    params: dict
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: float = 0.0


class BaseWorker(ABC):
    """
    Abstract base class for GPU workers.

    Handles job queue polling, heartbeats, and result reporting.
    Subclasses implement the actual inference logic.
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """Initialize worker."""
        self.config = config or WorkerConfig()
        self.config.worker_type = self.worker_type

        self._running = False
        self._current_job: Optional[Job] = None
        self._redis: Optional[redis.Redis] = None
        self._http_session: Optional[aiohttp.ClientSession] = None

        # Metrics
        self._jobs_processed = 0
        self._jobs_failed = 0
        self._total_processing_time = 0.0

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    @property
    @abstractmethod
    def worker_type(self) -> str:
        """Worker type identifier."""
        pass

    @abstractmethod
    async def load_models(self) -> None:
        """Load required ML models."""
        pass

    @abstractmethod
    async def process_job(self, job: Job) -> dict:
        """
        Process a single job.

        Args:
            job: Job to process

        Returns:
            Result dictionary
        """
        pass

    @abstractmethod
    def get_supported_job_types(self) -> list[str]:
        """Get list of supported job types."""
        pass

    async def start(self) -> None:
        """Start the worker."""
        logger.info(f"Starting {self.worker_type} worker: {self.config.worker_id}")

        # Initialize connections
        self._redis = redis.from_url(self.config.redis_url)
        self._http_session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.config.api_key}"}
        )

        # Load models
        logger.info("Loading models...")
        await self.load_models()
        logger.info("Models loaded")

        # Register worker
        await self._register_worker()

        # Start processing
        self._running = True

        await asyncio.gather(
            self._process_queue(),
            self._heartbeat_loop(),
            self._cleanup_loop(),
        )

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info(f"Stopping worker: {self.config.worker_id}")
        self._running = False

        # Wait for current job to complete
        if self._current_job:
            logger.info("Waiting for current job to complete...")
            while self._current_job:
                await asyncio.sleep(1)

        # Deregister worker
        await self._deregister_worker()

        # Close connections
        if self._redis:
            await self._redis.close()
        if self._http_session:
            await self._http_session.close()

        logger.info("Worker stopped")

    async def _process_queue(self) -> None:
        """Main job processing loop."""
        queue_key = f"{self.config.job_queue}:{self.worker_type}"

        while self._running:
            try:
                # Pop job from queue with timeout
                result = await self._redis.brpop(queue_key, timeout=5)

                if result is None:
                    continue

                _, job_data = result
                job = self._deserialize_job(job_data)

                # Check if job type is supported
                if job.job_type not in self.get_supported_job_types():
                    logger.warning(f"Unsupported job type: {job.job_type}")
                    await self._report_job_error(job, "Unsupported job type")
                    continue

                # Process job
                await self._execute_job(job)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    async def _execute_job(self, job: Job) -> None:
        """Execute a single job with error handling."""
        self._current_job = job
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        logger.info(f"Processing job: {job.id} (type: {job.job_type})")

        try:
            # Report job started
            await self._report_job_status(job)

            # Process with timeout
            start_time = time.perf_counter()

            result = await asyncio.wait_for(
                self.process_job(job),
                timeout=self.config.job_timeout,
            )

            processing_time = time.perf_counter() - start_time

            # Update job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.progress = 1.0

            # Update metrics
            self._jobs_processed += 1
            self._total_processing_time += processing_time

            logger.info(
                f"Job {job.id} completed in {processing_time:.2f}s"
            )

        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error = f"Job timed out after {self.config.job_timeout}s"
            job.completed_at = datetime.utcnow()
            self._jobs_failed += 1
            logger.error(f"Job {job.id} timed out")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            self._jobs_failed += 1
            logger.error(f"Job {job.id} failed: {e}")

        finally:
            # Report final status
            await self._report_job_status(job)
            self._current_job = None

    async def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """Update job progress."""
        if self._current_job:
            self._current_job.progress = min(max(progress, 0.0), 1.0)
            await self._report_job_progress(self._current_job, message)

    async def _report_job_status(self, job: Job) -> None:
        """Report job status to backend."""
        try:
            url = f"{self.config.backend_url}/api/v1/gpu/jobs/{job.id}/status"

            payload = {
                "status": job.status.value,
                "progress": job.progress,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "result": job.result,
                "error": job.error,
            }

            async with self._http_session.patch(url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Failed to report job status: {response.status}")

        except Exception as e:
            logger.error(f"Error reporting job status: {e}")

    async def _report_job_progress(self, job: Job, message: Optional[str] = None) -> None:
        """Report job progress update."""
        try:
            # Publish to Redis for WebSocket relay
            channel = f"job_progress:{job.id}"
            await self._redis.publish(channel, json.dumps({
                "job_id": str(job.id),
                "progress": job.progress,
                "message": message,
            }))
        except Exception as e:
            logger.debug(f"Error publishing progress: {e}")

    async def _report_job_error(self, job: Job, error: str) -> None:
        """Report job error."""
        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.utcnow()
        await self._report_job_status(job)

    async def _register_worker(self) -> None:
        """Register worker with backend."""
        try:
            url = f"{self.config.backend_url}/api/v1/gpu/workers/register"

            payload = {
                "worker_id": self.config.worker_id,
                "worker_type": self.worker_type,
                "supported_job_types": self.get_supported_job_types(),
                "capabilities": await self._get_capabilities(),
            }

            async with self._http_session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Worker registered successfully")
                else:
                    logger.warning(f"Failed to register worker: {response.status}")

        except Exception as e:
            logger.error(f"Error registering worker: {e}")

    async def _deregister_worker(self) -> None:
        """Deregister worker from backend."""
        try:
            url = f"{self.config.backend_url}/api/v1/gpu/workers/{self.config.worker_id}"

            async with self._http_session.delete(url) as response:
                if response.status == 200:
                    logger.info("Worker deregistered successfully")

        except Exception as e:
            logger.error(f"Error deregistering worker: {e}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to backend."""
        try:
            url = f"{self.config.backend_url}/api/v1/gpu/workers/{self.config.worker_id}/heartbeat"

            payload = {
                "status": "busy" if self._current_job else "idle",
                "current_job_id": str(self._current_job.id) if self._current_job else None,
                "metrics": self._get_metrics(),
            }

            async with self._http_session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.debug(f"Heartbeat failed: {response.status}")

        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup tasks."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self._cleanup_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Cleanup error: {e}")

    async def _cleanup_cache(self) -> None:
        """Clean up old cache files."""
        # Subclasses can override for specific cleanup
        pass

    async def _get_capabilities(self) -> dict:
        """Get worker capabilities."""
        import torch

        capabilities = {
            "device": self.config.device,
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available():
            capabilities.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory,
                "gpu_memory_available": torch.cuda.memory_reserved(0),
                "cuda_version": torch.version.cuda,
            })

        return capabilities

    def _get_metrics(self) -> dict:
        """Get worker metrics."""
        return {
            "jobs_processed": self._jobs_processed,
            "jobs_failed": self._jobs_failed,
            "total_processing_time": self._total_processing_time,
            "avg_processing_time": (
                self._total_processing_time / self._jobs_processed
                if self._jobs_processed > 0 else 0
            ),
        }

    def _deserialize_job(self, data: bytes) -> Job:
        """Deserialize job from Redis."""
        job_dict = json.loads(data)
        return Job(
            id=UUID(job_dict["id"]),
            job_type=job_dict["job_type"],
            input_data=job_dict["input_data"],
            params=job_dict.get("params", {}),
            priority=job_dict.get("priority", 0),
            created_at=datetime.fromisoformat(job_dict["created_at"]),
        )

    def _handle_shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())
