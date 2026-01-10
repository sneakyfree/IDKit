"""
RunPod Provider Adapter

Implementation of GPU provider interface for RunPod serverless platform.
https://docs.runpod.io/
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


class RunPodProvider(GPUProvider):
    """
    RunPod GPU provider implementation.

    RunPod offers both pod-based and serverless GPU computing.
    Supports secure cloud and community cloud options.
    """

    BASE_URL = "https://api.runpod.io"
    GRAPHQL_URL = "https://api.runpod.io/graphql"

    def __init__(self, api_key: str):
        """
        Initialize RunPod provider.

        Args:
            api_key: RunPod API key
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._jobs: dict[str, GPUJob] = {}

    @property
    def provider_name(self) -> str:
        return "runpod"

    @property
    def supports_spot_instances(self) -> bool:
        return True  # Community cloud is essentially spot

    @property
    def supports_persistent_disk(self) -> bool:
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._client

    async def _graphql(
        self,
        query: str,
        variables: Optional[dict] = None,
    ) -> dict:
        """Execute GraphQL query."""
        client = await self._get_client()

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = await client.post(self.GRAPHQL_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"RunPod GraphQL errors: {data['errors']}")
                raise Exception(data["errors"][0].get("message", "GraphQL error"))

            return data.get("data", {})
        except httpx.HTTPStatusError as e:
            logger.error(f"RunPod API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"RunPod request failed: {e}")
            raise

    async def _rest_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Make REST API request."""
        client = await self._get_client()
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"RunPod API error: {e.response.status_code}")
            raise

    def _get_gpu_type_id(self, gpu_name: str) -> str:
        """Map GPU name to RunPod GPU type ID."""
        # RunPod GPU type IDs
        gpu_map = {
            "A100": "NVIDIA A100 80GB PCIe",
            "A100-80GB": "NVIDIA A100 80GB PCIe",
            "A100-40GB": "NVIDIA A100-PCIE-40GB",
            "H100": "NVIDIA H100 80GB HBM3",
            "RTX 4090": "NVIDIA GeForce RTX 4090",
            "RTX 3090": "NVIDIA GeForce RTX 3090",
            "RTX 3080": "NVIDIA GeForce RTX 3080",
            "A6000": "NVIDIA RTX A6000",
            "A5000": "NVIDIA RTX A5000",
            "A4000": "NVIDIA RTX A4000",
        }
        return gpu_map.get(gpu_name, gpu_name)

    async def list_available_gpus(
        self,
        config: Optional[GPUInstanceConfig] = None,
    ) -> list[dict]:
        """List available GPU types from RunPod."""
        config = config or GPUInstanceConfig()

        query = """
        query GpuTypes {
            gpuTypes {
                id
                displayName
                memoryInGb
                secureCloud
                communityCloud
                lowestPrice(input: { gpuCount: 1 }) {
                    minimumBidPrice
                    uninterruptablePrice
                }
            }
        }
        """

        data = await self._graphql(query)
        gpu_types = data.get("gpuTypes", [])

        offers = []
        for gpu in gpu_types:
            vram_gb = gpu.get("memoryInGb", 0)

            # Filter by VRAM requirement
            if vram_gb < config.min_vram_gb:
                continue

            # Get pricing
            pricing = gpu.get("lowestPrice", {})
            spot_price = pricing.get("minimumBidPrice", 0)
            on_demand_price = pricing.get("uninterruptablePrice", 0)

            # Filter by max price
            if config.max_price_per_hour:
                effective_price = spot_price if config.use_spot else on_demand_price
                if effective_price > config.max_price_per_hour:
                    continue

            offers.append({
                "gpu_type_id": gpu.get("id"),
                "provider": self.provider_name,
                "gpu_name": gpu.get("displayName"),
                "gpu_count": 1,
                "vram_gb": vram_gb,
                "price_per_hour": spot_price if config.use_spot else on_demand_price,
                "spot_price": spot_price,
                "on_demand_price": on_demand_price,
                "secure_cloud": gpu.get("secureCloud", False),
                "community_cloud": gpu.get("communityCloud", False),
                "is_spot": config.use_spot,
            })

        # Sort by price
        offers.sort(key=lambda x: x["price_per_hour"])

        return offers

    async def create_instance(
        self,
        config: GPUInstanceConfig,
    ) -> GPUInstance:
        """Create a new GPU pod on RunPod."""
        # Find best GPU type
        offers = await self.list_available_gpus(config)
        if not offers:
            raise ValueError("No GPU types matching requirements")

        gpu_type = offers[0]
        gpu_type_id = gpu_type["gpu_type_id"]

        # Build pod creation mutation
        cloud_type = "COMMUNITY" if config.use_spot else "SECURE"

        mutation = """
        mutation CreatePod($input: PodFindAndDeployOnDemandInput!) {
            podFindAndDeployOnDemand(input: $input) {
                id
                name
                imageName
                gpuCount
                machineId
                machine {
                    gpuDisplayName
                }
                runtime {
                    uptimeInSeconds
                    gpus {
                        id
                        gpuUtilPercent
                        memoryUtilPercent
                    }
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """

        variables = {
            "input": {
                "cloudType": cloud_type,
                "gpuCount": config.gpu_count,
                "gpuTypeId": gpu_type_id,
                "name": config.labels.get("name", "idkit-pod"),
                "imageName": config.docker_image,
                "containerDiskInGb": int(config.min_disk_gb),
                "volumeInGb": int(config.persistent_disk_gb or 0),
                "minVcpuCount": config.min_cpu_cores,
                "minMemoryInGb": int(config.min_ram_gb),
                "startSsh": True,
                "env": [
                    {"key": k, "value": v}
                    for k, v in config.environment.items()
                ],
                "ports": ",".join(str(p) for p in config.ports) if config.ports else None,
                "dockerArgs": config.docker_command or "",
            }
        }

        data = await self._graphql(mutation, variables)
        pod = data.get("podFindAndDeployOnDemand", {})

        return GPUInstance(
            instance_id=pod.get("id"),
            provider=self.provider_name,
            status=GPUInstanceStatus.PENDING,
            gpu_spec=GPUSpec(
                name=gpu_type["gpu_name"],
                vram_gb=gpu_type["vram_gb"],
            ),
            gpu_count=pod.get("gpuCount", config.gpu_count),
            price_per_hour=gpu_type["price_per_hour"],
            created_at=datetime.utcnow(),
            metadata={
                "gpu_type_id": gpu_type_id,
                "cloud_type": cloud_type,
                "machine_id": pod.get("machineId"),
            },
        )

    async def get_instance(
        self,
        instance_id: str,
    ) -> GPUInstance:
        """Get pod status from RunPod."""
        query = """
        query Pod($podId: String!) {
            pod(input: { podId: $podId }) {
                id
                name
                imageName
                gpuCount
                desiredStatus
                machineId
                machine {
                    gpuDisplayName
                    gpuMemoryMb
                    cpuCount
                    memoryMb
                }
                runtime {
                    uptimeInSeconds
                    gpus {
                        id
                        gpuUtilPercent
                        memoryUtilPercent
                    }
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                    }
                }
                costPerHr
            }
        }
        """

        data = await self._graphql(query, {"podId": instance_id})
        pod = data.get("pod", {})

        if not pod:
            raise ValueError(f"Pod {instance_id} not found")

        # Map status
        desired_status = pod.get("desiredStatus", "")
        runtime = pod.get("runtime")

        if runtime and runtime.get("uptimeInSeconds", 0) > 0:
            status = GPUInstanceStatus.RUNNING
        elif desired_status == "RUNNING":
            status = GPUInstanceStatus.STARTING
        elif desired_status == "STOPPED":
            status = GPUInstanceStatus.STOPPED
        else:
            status = GPUInstanceStatus.PENDING

        # Extract connection info
        ports = runtime.get("ports", []) if runtime else []
        ssh_port_info = next(
            (p for p in ports if p.get("privatePort") == 22),
            {}
        )

        machine = pod.get("machine", {})

        return GPUInstance(
            instance_id=instance_id,
            provider=self.provider_name,
            status=status,
            host=ssh_port_info.get("ip"),
            ssh_port=ssh_port_info.get("publicPort"),
            public_ip=ssh_port_info.get("ip") if ssh_port_info.get("isIpPublic") else None,
            gpu_spec=GPUSpec(
                name=machine.get("gpuDisplayName", ""),
                vram_gb=machine.get("gpuMemoryMb", 0) / 1024,
            ),
            gpu_count=pod.get("gpuCount", 1),
            ram_gb=machine.get("memoryMb", 0) / 1024,
            cpu_cores=machine.get("cpuCount", 0),
            price_per_hour=pod.get("costPerHr", 0),
            metadata={"raw_data": pod},
        )

    async def stop_instance(
        self,
        instance_id: str,
    ) -> bool:
        """Stop a RunPod pod."""
        mutation = """
        mutation StopPod($podId: String!) {
            podStop(input: { podId: $podId }) {
                id
                desiredStatus
            }
        }
        """

        try:
            await self._graphql(mutation, {"podId": instance_id})
            return True
        except Exception as e:
            logger.error(f"Failed to stop pod {instance_id}: {e}")
            return False

    async def destroy_instance(
        self,
        instance_id: str,
    ) -> bool:
        """Terminate a RunPod pod."""
        mutation = """
        mutation TerminatePod($podId: String!) {
            podTerminate(input: { podId: $podId })
        }
        """

        try:
            await self._graphql(mutation, {"podId": instance_id})
            return True
        except Exception as e:
            logger.error(f"Failed to terminate pod {instance_id}: {e}")
            return False

    async def run_job(
        self,
        job_config: GPUJobConfig,
        instance_id: Optional[str] = None,
    ) -> GPUJob:
        """Run a job on RunPod."""
        # For serverless endpoints, use the serverless API
        # For pods, create/use instance and execute command

        if not instance_id:
            instance = await self.create_instance(job_config.instance_config)
            instance_id = instance.instance_id

            # Wait for pod to be ready
            for _ in range(60):  # 5 minute timeout
                instance = await self.get_instance(instance_id)
                if instance.status == GPUInstanceStatus.RUNNING:
                    break
                await asyncio.sleep(5)
            else:
                raise TimeoutError("Pod failed to start within timeout")
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
        )

        # Execute command via runsync API for serverless,
        # or SSH for pod-based
        if job_config.command:
            # For pod-based execution, we'd use SSH
            # This is a simplified version
            job.progress_message = "Job started on pod"

        self._jobs[job.job_id] = job
        return job

    async def run_serverless_job(
        self,
        endpoint_id: str,
        input_data: dict,
        webhook_url: Optional[str] = None,
    ) -> GPUJob:
        """
        Run a job on RunPod serverless endpoint.

        This is RunPod's primary serverless API for inference.
        """
        endpoint = f"/v2/{endpoint_id}/run"

        payload = {"input": input_data}
        if webhook_url:
            payload["webhook"] = webhook_url

        data = await self._rest_request("POST", endpoint, json=payload)

        job_id = data.get("id")

        job = GPUJob(
            job_id=job_id,
            config=GPUJobConfig(job_id=job_id),
            status=GPUJobStatus.QUEUED,
            provider=self.provider_name,
            created_at=datetime.utcnow(),
            metadata={"endpoint_id": endpoint_id, "raw_data": data},
        )

        self._jobs[job_id] = job
        return job

    async def get_serverless_job_status(
        self,
        endpoint_id: str,
        job_id: str,
    ) -> GPUJob:
        """Get serverless job status."""
        endpoint = f"/v2/{endpoint_id}/status/{job_id}"

        data = await self._rest_request("GET", endpoint)

        status_map = {
            "IN_QUEUE": GPUJobStatus.QUEUED,
            "IN_PROGRESS": GPUJobStatus.RUNNING,
            "COMPLETED": GPUJobStatus.COMPLETED,
            "FAILED": GPUJobStatus.FAILED,
            "CANCELLED": GPUJobStatus.CANCELLED,
            "TIMED_OUT": GPUJobStatus.TIMEOUT,
        }

        runpod_status = data.get("status", "")
        status = status_map.get(runpod_status, GPUJobStatus.PENDING)

        job = self._jobs.get(job_id, GPUJob(
            job_id=job_id,
            config=GPUJobConfig(job_id=job_id),
            status=status,
            provider=self.provider_name,
        ))

        job.status = status
        job.result_data = data.get("output", {})

        if status == GPUJobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()
            job.progress = 100

        if status == GPUJobStatus.FAILED:
            job.error_message = data.get("error", "Unknown error")

        execution_time = data.get("executionTime", 0)
        if execution_time:
            job.metadata["execution_time_ms"] = execution_time

        return job

    async def get_job_status(
        self,
        job_id: str,
    ) -> GPUJob:
        """Get job status."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]

        # Check if this is a serverless job
        endpoint_id = job.metadata.get("endpoint_id")
        if endpoint_id:
            return await self.get_serverless_job_status(endpoint_id, job_id)

        # For pod-based jobs, check instance status
        if job.instance_id:
            instance = await self.get_instance(job.instance_id)
            job.instance = instance

        return job

    async def cancel_job(
        self,
        job_id: str,
    ) -> bool:
        """Cancel a running job."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]

        # For serverless jobs, use cancel endpoint
        endpoint_id = job.metadata.get("endpoint_id")
        if endpoint_id:
            endpoint = f"/v2/{endpoint_id}/cancel/{job_id}"
            try:
                await self._rest_request("POST", endpoint)
                job.status = GPUJobStatus.CANCELLED
                return True
            except Exception as e:
                logger.error(f"Failed to cancel serverless job: {e}")
                return False

        # For pod-based jobs, terminate the pod
        if job.instance_id:
            await self.destroy_instance(job.instance_id)

        job.status = GPUJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        return True

    async def get_account_balance(self) -> dict:
        """Get RunPod account balance."""
        query = """
        query Myself {
            myself {
                id
                currentSpendPerHr
                machineQuota
                creditBalance
                creditAlertThreshold
            }
        }
        """

        data = await self._graphql(query)
        myself = data.get("myself", {})

        return {
            "balance": myself.get("creditBalance", 0),
            "currency": "USD",
            "current_spend_per_hour": myself.get("currentSpendPerHr", 0),
            "machine_quota": myself.get("machineQuota", 0),
            "alert_threshold": myself.get("creditAlertThreshold", 0),
            "provider": self.provider_name,
        }

    async def list_endpoints(self) -> list[dict]:
        """List available serverless endpoints."""
        query = """
        query Endpoints {
            myself {
                endpoints {
                    id
                    name
                    gpuIds
                    templateId
                    workersMin
                    workersMax
                    idleTimeout
                }
            }
        }
        """

        data = await self._graphql(query)
        endpoints = data.get("myself", {}).get("endpoints", [])

        return [
            {
                "endpoint_id": ep.get("id"),
                "name": ep.get("name"),
                "gpu_ids": ep.get("gpuIds"),
                "template_id": ep.get("templateId"),
                "workers_min": ep.get("workersMin"),
                "workers_max": ep.get("workersMax"),
                "idle_timeout": ep.get("idleTimeout"),
            }
            for ep in endpoints
        ]

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
