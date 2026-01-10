"""
Vast.ai Provider Adapter

Implementation of GPU provider interface for Vast.ai marketplace.
https://vast.ai/docs
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from app.gpu.interfaces import (
    GPUInstance,
    GPUInstanceConfig,
    GPUInstanceStatus,
    GPUJob,
    GPUJobConfig,
    GPUJobStatus,
    GPUProvider,
    GPUSpec,
)

logger = logging.getLogger(__name__)


class VastAIProvider(GPUProvider):
    """
    Vast.ai GPU provider implementation.

    Vast.ai is a GPU marketplace connecting users with GPU renters.
    Offers both spot and on-demand instances with competitive pricing.
    """

    BASE_URL = "https://console.vast.ai/api/v0"

    def __init__(self, api_key: str):
        """
        Initialize Vast.ai provider.

        Args:
            api_key: Vast.ai API key
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._jobs: dict[str, GPUJob] = {}  # Local job tracking

    @property
    def provider_name(self) -> str:
        return "vastai"

    @property
    def supports_spot_instances(self) -> bool:
        return True

    @property
    def supports_persistent_disk(self) -> bool:
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Make API request to Vast.ai."""
        client = await self._get_client()
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Vast.ai API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Vast.ai request failed: {e}")
            raise

    def _build_search_query(self, config: GPUInstanceConfig) -> dict:
        """Build Vast.ai search query from config."""
        query = {
            "verified": {"eq": True},
            "external": {"eq": False},
            "rentable": {"eq": True},
            "gpu_ram": {"gte": config.min_vram_gb * 1024},  # Convert to MB
            "num_gpus": {"gte": config.gpu_count},
            "cpu_ram": {"gte": config.min_ram_gb * 1024},  # Convert to MB
            "disk_space": {"gte": config.min_disk_gb},
            "cpu_cores_effective": {"gte": config.min_cpu_cores},
        }

        # Add GPU model filter if specified
        if config.preferred_gpus:
            # Vast.ai uses regex for GPU name matching
            gpu_pattern = "|".join(config.preferred_gpus)
            query["gpu_name"] = {"regex": gpu_pattern}

        # Price constraint
        if config.max_price_per_hour:
            query["dph_total"] = {"lte": config.max_price_per_hour}

        return query

    async def list_available_gpus(
        self,
        config: Optional[GPUInstanceConfig] = None,
    ) -> list[dict]:
        """List available GPU offers from Vast.ai marketplace."""
        config = config or GPUInstanceConfig()
        query = self._build_search_query(config)

        data = await self._request(
            "GET",
            "/bundles",
            params={
                "q": json.dumps(query),
                "order": "dph_total",  # Sort by price
                "limit": 100,
            },
        )

        offers = []
        for offer in data.get("offers", []):
            offers.append({
                "offer_id": offer.get("id"),
                "provider": self.provider_name,
                "gpu_name": offer.get("gpu_name"),
                "gpu_count": offer.get("num_gpus", 1),
                "vram_gb": offer.get("gpu_ram", 0) / 1024,
                "ram_gb": offer.get("cpu_ram", 0) / 1024,
                "disk_gb": offer.get("disk_space", 0),
                "cpu_cores": offer.get("cpu_cores_effective", 0),
                "price_per_hour": offer.get("dph_total", 0),
                "reliability": offer.get("reliability", 0),
                "dlperf": offer.get("dlperf", 0),  # Deep learning performance score
                "inet_up": offer.get("inet_up", 0),
                "inet_down": offer.get("inet_down", 0),
                "cuda_version": offer.get("cuda_max_good", ""),
                "region": offer.get("geolocation", ""),
                "is_spot": not offer.get("static_ip", False),
                "raw_data": offer,
            })

        return offers

    async def create_instance(
        self,
        config: GPUInstanceConfig,
    ) -> GPUInstance:
        """Create a new GPU instance on Vast.ai."""
        # Find best available offer
        offers = await self.list_available_gpus(config)
        if not offers:
            raise ValueError("No GPU offers matching requirements")

        # Select best offer (first one, sorted by price)
        offer = offers[0]
        offer_id = offer["offer_id"]

        # Build instance creation request
        create_data = {
            "client_id": "me",
            "image": config.docker_image,
            "disk": config.persistent_disk_gb or config.min_disk_gb,
            "label": config.labels.get("name", "idkit-instance"),
            "onstart": config.docker_command or "",
            "runtype": "args" if config.docker_command else "ssh",
        }

        # Add environment variables
        if config.environment:
            env_str = " ".join(f"-e {k}={v}" for k, v in config.environment.items())
            create_data["env"] = env_str

        # Add port mappings
        if config.ports:
            create_data["ports"] = {str(p): str(p) for p in config.ports}

        data = await self._request(
            "PUT",
            f"/asks/{offer_id}/",
            json=create_data,
        )

        instance_id = str(data.get("new_contract"))

        return GPUInstance(
            instance_id=instance_id,
            provider=self.provider_name,
            status=GPUInstanceStatus.PENDING,
            gpu_spec=GPUSpec(
                name=offer["gpu_name"],
                vram_gb=offer["vram_gb"],
            ),
            gpu_count=offer["gpu_count"],
            ram_gb=offer["ram_gb"],
            disk_gb=offer["disk_gb"],
            cpu_cores=offer["cpu_cores"],
            price_per_hour=offer["price_per_hour"],
            region=offer.get("region"),
            created_at=datetime.utcnow(),
            metadata={"offer_id": offer_id, "raw_data": data},
        )

    async def get_instance(
        self,
        instance_id: str,
    ) -> GPUInstance:
        """Get instance status from Vast.ai."""
        data = await self._request("GET", f"/instances/{instance_id}/")

        instance = data.get("instances", [{}])[0] if data.get("instances") else data

        # Map Vast.ai status to our status
        vast_status = instance.get("actual_status", "")
        status_map = {
            "running": GPUInstanceStatus.RUNNING,
            "loading": GPUInstanceStatus.STARTING,
            "created": GPUInstanceStatus.PENDING,
            "exited": GPUInstanceStatus.STOPPED,
            "offline": GPUInstanceStatus.STOPPED,
        }
        status = status_map.get(vast_status, GPUInstanceStatus.PENDING)

        return GPUInstance(
            instance_id=instance_id,
            provider=self.provider_name,
            status=status,
            host=instance.get("public_ipaddr"),
            port=instance.get("ports", {}).get("22/tcp", [{}])[0].get("HostPort"),
            ssh_host=instance.get("ssh_host"),
            ssh_port=instance.get("ssh_port"),
            gpu_spec=GPUSpec(
                name=instance.get("gpu_name", ""),
                vram_gb=instance.get("gpu_ram", 0) / 1024,
            ),
            gpu_count=instance.get("num_gpus", 1),
            ram_gb=instance.get("cpu_ram", 0) / 1024,
            disk_gb=instance.get("disk_space", 0),
            cpu_cores=instance.get("cpu_cores", 0),
            price_per_hour=instance.get("dph_total", 0),
            total_cost=instance.get("total_dph", 0),
            public_ip=instance.get("public_ipaddr"),
            region=instance.get("geolocation"),
            started_at=datetime.fromisoformat(instance["start_date"]) if instance.get("start_date") else None,
            metadata={"raw_data": instance},
        )

    async def stop_instance(
        self,
        instance_id: str,
    ) -> bool:
        """Stop a Vast.ai instance."""
        try:
            await self._request(
                "PUT",
                f"/instances/{instance_id}/",
                json={"state": "stopped"},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to stop instance {instance_id}: {e}")
            return False

    async def destroy_instance(
        self,
        instance_id: str,
    ) -> bool:
        """Destroy a Vast.ai instance."""
        try:
            await self._request("DELETE", f"/instances/{instance_id}/")
            return True
        except Exception as e:
            logger.error(f"Failed to destroy instance {instance_id}: {e}")
            return False

    async def run_job(
        self,
        job_config: GPUJobConfig,
        instance_id: Optional[str] = None,
    ) -> GPUJob:
        """Run a job on Vast.ai instance."""
        # Create instance if not provided
        if not instance_id:
            instance = await self.create_instance(job_config.instance_config)
            instance_id = instance.instance_id

            # Wait for instance to be ready
            for _ in range(60):  # 5 minute timeout
                instance = await self.get_instance(instance_id)
                if instance.status == GPUInstanceStatus.RUNNING:
                    break
                await asyncio.sleep(5)
            else:
                raise TimeoutError("Instance failed to start within timeout")
        else:
            instance = await self.get_instance(instance_id)

        # Create job record
        job = GPUJob(
            job_id=job_config.job_id,
            config=job_config,
            status=GPUJobStatus.RUNNING,
            provider=self.provider_name,
            instance_id=instance_id,
            instance=instance,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
        )

        # Execute command on instance via SSH or API
        if job_config.command:
            try:
                # Use Vast.ai execute endpoint
                await self._request(
                    "PUT",
                    f"/instances/{instance_id}/",
                    json={
                        "state": "running",
                        "onstart": job_config.command,
                    },
                )
                job.status = GPUJobStatus.RUNNING
                job.progress_message = "Job started"
            except Exception as e:
                job.status = GPUJobStatus.FAILED
                job.error_message = str(e)

        # Store job for tracking
        self._jobs[job.job_id] = job

        return job

    async def get_job_status(
        self,
        job_id: str,
    ) -> GPUJob:
        """Get job status."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]

        # Update instance status
        if job.instance_id:
            try:
                instance = await self.get_instance(job.instance_id)
                job.instance = instance

                # Infer job status from instance status
                if instance.status == GPUInstanceStatus.STOPPED:
                    if job.status == GPUJobStatus.RUNNING:
                        job.status = GPUJobStatus.COMPLETED
                        job.completed_at = datetime.utcnow()
                        job.progress = 100
                elif instance.status == GPUInstanceStatus.FAILED:
                    job.status = GPUJobStatus.FAILED
                    job.error_message = "Instance failed"
            except Exception as e:
                logger.warning(f"Failed to get instance status: {e}")

        return job

    async def cancel_job(
        self,
        job_id: str,
    ) -> bool:
        """Cancel a running job."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]

        if job.instance_id:
            await self.destroy_instance(job.instance_id)

        job.status = GPUJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        return True

    async def get_logs(
        self,
        job_id: str,
        tail: int = 100,
    ) -> str:
        """Get job logs from Vast.ai instance."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]

        if not job.instance_id:
            return "No instance associated with job"

        try:
            data = await self._request(
                "GET",
                f"/instances/{job.instance_id}/logs/",
                params={"tail": tail},
            )
            return data.get("logs", "No logs available")
        except Exception as e:
            return f"Failed to get logs: {e}"

    async def get_account_balance(self) -> dict:
        """Get Vast.ai account balance."""
        data = await self._request("GET", "/users/current/")

        return {
            "balance": data.get("credit", 0),
            "currency": "USD",
            "provider": self.provider_name,
        }

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
