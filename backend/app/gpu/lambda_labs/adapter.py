"""
Lambda Labs Provider Adapter

Implementation of GPU provider interface for Lambda Labs Cloud.
https://cloud.lambdalabs.com/api/v1
"""

import asyncio
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


class LambdaLabsProvider(GPUProvider):
    """
    Lambda Labs GPU provider implementation.

    Lambda Labs offers high-performance GPUs (A100, H100, A10)
    with simple API and competitive pricing.
    """

    BASE_URL = "https://cloud.lambdalabs.com/api/v1"

    # GPU specifications
    GPU_SPECS = {
        "gpu_1x_a100": GPUSpec(
            name="A100",
            vram_gb=40,
            compute_capability="8.0",
            tensor_cores=True,
            cuda_cores=6912,
        ),
        "gpu_1x_a100_sxm4": GPUSpec(
            name="A100 SXM4",
            vram_gb=80,
            compute_capability="8.0",
            tensor_cores=True,
            cuda_cores=6912,
        ),
        "gpu_8x_a100_80gb_sxm4": GPUSpec(
            name="A100 SXM4 80GB",
            vram_gb=80,
            compute_capability="8.0",
            tensor_cores=True,
            cuda_cores=6912,
        ),
        "gpu_1x_h100_pcie": GPUSpec(
            name="H100 PCIe",
            vram_gb=80,
            compute_capability="9.0",
            tensor_cores=True,
            cuda_cores=14592,
        ),
        "gpu_8x_h100_sxm5": GPUSpec(
            name="H100 SXM5",
            vram_gb=80,
            compute_capability="9.0",
            tensor_cores=True,
            cuda_cores=14592,
        ),
        "gpu_1x_a10": GPUSpec(
            name="A10",
            vram_gb=24,
            compute_capability="8.6",
            tensor_cores=True,
            cuda_cores=9216,
        ),
        "gpu_1x_rtx6000": GPUSpec(
            name="RTX 6000",
            vram_gb=24,
            compute_capability="8.6",
            tensor_cores=True,
            cuda_cores=10752,
        ),
    }

    def __init__(self, api_key: str):
        """
        Initialize Lambda Labs provider.

        Args:
            api_key: Lambda Labs API key
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._jobs: dict[str, GPUJob] = {}
        self._instances: dict[str, GPUInstance] = {}

    @property
    def provider_name(self) -> str:
        return "lambda_labs"

    @property
    def supports_spot_instances(self) -> bool:
        return False  # Lambda Labs uses on-demand only

    @property
    def supports_persistent_disk(self) -> bool:
        return True  # Persistent storage available

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Make API request to Lambda Labs."""
        client = await self._get_client()

        try:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Lambda Labs API error: {e.response.status_code} - "
                f"{e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Lambda Labs request failed: {e}")
            raise

    async def list_available_gpus(
        self,
        config: Optional[GPUInstanceConfig] = None,
    ) -> list[dict]:
        """List available GPU instance types from Lambda Labs."""
        config = config or GPUInstanceConfig()

        data = await self._request("GET", "/instance-types")
        instance_types = data.get("data", {})

        offers = []
        for type_name, type_info in instance_types.items():
            specs = type_info.get("instance_type", {}).get("specs", {})
            gpu_count = specs.get("gpus", 1)
            vram_total = specs.get("memory_gib", 0)  # Total GPU memory

            # Get GPU spec from our mapping
            gpu_spec = self.GPU_SPECS.get(type_name)
            vram_per_gpu = gpu_spec.vram_gb if gpu_spec else vram_total / gpu_count

            # Filter by requirements
            if vram_per_gpu < config.min_vram_gb:
                continue

            if gpu_count < config.gpu_count:
                continue

            # Get pricing
            price = type_info.get("instance_type", {}).get(
                "price_cents_per_hour", 0
            ) / 100

            if config.max_price_per_hour and price > config.max_price_per_hour:
                continue

            # Get availability
            regions_available = type_info.get("regions_with_capacity_available", [])

            offers.append({
                "instance_type": type_name,
                "provider": self.provider_name,
                "gpu_name": gpu_spec.name if gpu_spec else type_name,
                "gpu_count": gpu_count,
                "vram_gb": vram_per_gpu,
                "total_vram_gb": vram_total,
                "price_per_hour": price,
                "vcpus": specs.get("vcpus", 0),
                "memory_gib": specs.get("memory_gib", 0),
                "storage_gib": specs.get("storage_gib", 0),
                "regions_available": [r.get("name") for r in regions_available],
                "is_available": len(regions_available) > 0,
            })

        # Sort by price
        offers.sort(key=lambda x: x["price_per_hour"])

        return offers

    async def create_instance(
        self,
        config: GPUInstanceConfig,
    ) -> GPUInstance:
        """Launch a new GPU instance on Lambda Labs."""
        # Find suitable instance type
        offers = await self.list_available_gpus(config)
        available_offers = [o for o in offers if o.get("is_available")]

        if not available_offers:
            raise ValueError("No GPU instances matching requirements are available")

        selected = available_offers[0]
        instance_type = selected["instance_type"]

        # Select first available region
        regions = selected.get("regions_available", [])
        if not regions:
            raise ValueError(f"No regions available for {instance_type}")

        region = regions[0]

        # Prepare SSH key
        # Lambda Labs requires SSH key to be pre-added via UI or API
        ssh_key_names = config.labels.get("ssh_key_names", [])
        if isinstance(ssh_key_names, str):
            ssh_key_names = [ssh_key_names]

        # If no SSH key specified, list available and use first
        if not ssh_key_names:
            keys_data = await self._request("GET", "/ssh-keys")
            ssh_keys = keys_data.get("data", [])
            if ssh_keys:
                ssh_key_names = [ssh_keys[0].get("name")]
            else:
                raise ValueError("No SSH keys configured in Lambda Labs account")

        # Launch instance
        payload = {
            "region_name": region,
            "instance_type_name": instance_type,
            "ssh_key_names": ssh_key_names,
            "quantity": 1,
        }

        # Optional: name for the instance
        if config.labels.get("name"):
            payload["name"] = config.labels["name"]

        # Optional: file system attachment
        if config.labels.get("filesystem_name"):
            payload["file_system_names"] = [config.labels["filesystem_name"]]

        data = await self._request("POST", "/instance-operations/launch", json=payload)
        instances = data.get("data", {}).get("instance_ids", [])

        if not instances:
            raise ValueError("Failed to launch instance")

        instance_id = instances[0]

        gpu_spec = self.GPU_SPECS.get(instance_type)

        instance = GPUInstance(
            instance_id=instance_id,
            provider=self.provider_name,
            status=GPUInstanceStatus.PENDING,
            gpu_spec=gpu_spec,
            gpu_count=selected["gpu_count"],
            ram_gb=selected.get("memory_gib", 0),
            disk_gb=selected.get("storage_gib", 0),
            price_per_hour=selected["price_per_hour"],
            region=region,
            created_at=datetime.utcnow(),
            metadata={
                "instance_type": instance_type,
                "ssh_key_names": ssh_key_names,
            },
        )

        self._instances[instance_id] = instance
        return instance

    async def get_instance(
        self,
        instance_id: str,
    ) -> GPUInstance:
        """Get instance status from Lambda Labs."""
        data = await self._request("GET", f"/instances/{instance_id}")
        instance_data = data.get("data", {})

        if not instance_data:
            raise ValueError(f"Instance {instance_id} not found")

        # Map Lambda Labs status to our status
        status_map = {
            "booting": GPUInstanceStatus.STARTING,
            "active": GPUInstanceStatus.RUNNING,
            "unhealthy": GPUInstanceStatus.ERROR,
            "terminated": GPUInstanceStatus.TERMINATED,
        }

        ll_status = instance_data.get("status", "")
        status = status_map.get(ll_status, GPUInstanceStatus.PENDING)

        instance_type = instance_data.get("instance_type", {}).get("name", "")
        gpu_spec = self.GPU_SPECS.get(instance_type)

        return GPUInstance(
            instance_id=instance_id,
            provider=self.provider_name,
            status=status,
            host=instance_data.get("ip"),
            public_ip=instance_data.get("ip"),
            ssh_port=22,
            ssh_user="ubuntu",
            gpu_spec=gpu_spec,
            gpu_count=instance_data.get("instance_type", {}).get("specs", {}).get("gpus", 1),
            region=instance_data.get("region", {}).get("name"),
            price_per_hour=instance_data.get("instance_type", {}).get("price_cents_per_hour", 0) / 100,
            metadata={
                "instance_type": instance_type,
                "hostname": instance_data.get("hostname"),
                "jupyter_url": instance_data.get("jupyter_url"),
                "file_system_names": instance_data.get("file_system_names", []),
            },
        )

    async def stop_instance(
        self,
        instance_id: str,
    ) -> bool:
        """
        Lambda Labs doesn't support stop/resume.
        This will terminate the instance.
        """
        logger.warning(
            f"Lambda Labs doesn't support stop. "
            f"Instance {instance_id} will be terminated."
        )
        return await self.destroy_instance(instance_id)

    async def destroy_instance(
        self,
        instance_id: str,
    ) -> bool:
        """Terminate a Lambda Labs instance."""
        try:
            payload = {"instance_ids": [instance_id]}
            await self._request(
                "POST",
                "/instance-operations/terminate",
                json=payload,
            )

            # Update cached instance
            if instance_id in self._instances:
                self._instances[instance_id].status = GPUInstanceStatus.TERMINATED

            return True
        except Exception as e:
            logger.error(f"Failed to terminate instance {instance_id}: {e}")
            return False

    async def run_job(
        self,
        job_config: GPUJobConfig,
        instance_id: Optional[str] = None,
    ) -> GPUJob:
        """Run a job on Lambda Labs instance."""
        # Create instance if not provided
        if not instance_id:
            instance = await self.create_instance(job_config.instance_config)
            instance_id = instance.instance_id

            # Wait for instance to be ready
            for _ in range(120):  # 10 minute timeout
                instance = await self.get_instance(instance_id)
                if instance.status == GPUInstanceStatus.RUNNING:
                    break
                if instance.status == GPUInstanceStatus.ERROR:
                    raise RuntimeError(f"Instance {instance_id} failed to start")
                await asyncio.sleep(5)
            else:
                raise TimeoutError("Instance failed to become ready within timeout")
        else:
            instance = await self.get_instance(instance_id)

        job = GPUJob(
            job_id=job_config.job_id,
            config=job_config,
            status=GPUJobStatus.RUNNING,
            provider=self.provider_name,
            instance_id=instance_id,
            instance=instance,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            metadata={
                "ssh_host": instance.public_ip,
                "ssh_port": instance.ssh_port,
                "ssh_user": instance.ssh_user,
            },
        )

        # Execute command via SSH if provided
        if job_config.command:
            job.progress_message = f"Job started on {instance.public_ip}"
            # Actual SSH execution would be handled by a job runner

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

        # Update instance status if running
        if job.instance_id and job.status == GPUJobStatus.RUNNING:
            try:
                instance = await self.get_instance(job.instance_id)
                job.instance = instance

                if instance.status == GPUInstanceStatus.TERMINATED:
                    job.status = GPUJobStatus.FAILED
                    job.error_message = "Instance was terminated"
                    job.completed_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Failed to check instance status: {e}")

        return job

    async def cancel_job(
        self,
        job_id: str,
    ) -> bool:
        """Cancel a running job."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]

        # Terminate the instance if job was running
        if job.instance_id and job.status == GPUJobStatus.RUNNING:
            await self.destroy_instance(job.instance_id)

        job.status = GPUJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        return True

    async def get_logs(
        self,
        job_id: str,
        tail: int = 100,
    ) -> str:
        """
        Get job logs.

        Note: Lambda Labs doesn't have a logs API.
        Logs would need to be retrieved via SSH.
        """
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]
        return f"Logs for job {job_id} on instance {job.instance_id} (SSH access required)"

    async def get_account_balance(self) -> dict:
        """
        Get Lambda Labs account information.

        Note: Lambda Labs uses credit card billing, not balance-based.
        """
        # Lambda Labs doesn't have a balance API like Vast.ai
        # Return account info instead
        try:
            # List running instances to show current usage
            data = await self._request("GET", "/instances")
            instances = data.get("data", [])

            running_instances = len(instances)
            total_cost_per_hour = sum(
                inst.get("instance_type", {}).get("price_cents_per_hour", 0) / 100
                for inst in instances
            )

            return {
                "provider": self.provider_name,
                "billing_type": "credit_card",
                "running_instances": running_instances,
                "current_hourly_cost": total_cost_per_hour,
                "currency": "USD",
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {
                "provider": self.provider_name,
                "error": str(e),
            }

    async def list_ssh_keys(self) -> list[dict]:
        """List SSH keys in Lambda Labs account."""
        data = await self._request("GET", "/ssh-keys")
        keys = data.get("data", [])

        return [
            {
                "id": key.get("id"),
                "name": key.get("name"),
                "public_key": key.get("public_key"),
            }
            for key in keys
        ]

    async def add_ssh_key(
        self,
        name: str,
        public_key: str,
    ) -> dict:
        """Add an SSH key to Lambda Labs account."""
        payload = {
            "name": name,
            "public_key": public_key,
        }

        data = await self._request("POST", "/ssh-keys", json=payload)
        return data.get("data", {})

    async def delete_ssh_key(
        self,
        key_id: str,
    ) -> bool:
        """Delete an SSH key from Lambda Labs account."""
        try:
            await self._request("DELETE", f"/ssh-keys/{key_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete SSH key: {e}")
            return False

    async def list_filesystems(self) -> list[dict]:
        """List persistent file systems."""
        data = await self._request("GET", "/file-systems")
        filesystems = data.get("data", [])

        return [
            {
                "id": fs.get("id"),
                "name": fs.get("name"),
                "region": fs.get("region", {}).get("name"),
                "mount_point": fs.get("mount_point"),
                "created_at": fs.get("created"),
            }
            for fs in filesystems
        ]

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
