"""
Prometheus Metrics Middleware and Instrumentation

Provides application metrics for monitoring:
- HTTP request counts and latencies
- Active connections
- GPU job queue metrics
- Database connection pool stats
- Redis connection stats
"""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, Info
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match


# =============================================================================
# Application Info
# =============================================================================

APP_INFO = Info("idkit_app", "IDKit application information")


# =============================================================================
# HTTP Metrics
# =============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "idkit_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "idkit_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "idkit_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)


# =============================================================================
# Database Metrics
# =============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "idkit_db_connections_active",
    "Number of active database connections",
)

DB_CONNECTIONS_POOL_SIZE = Gauge(
    "idkit_db_connections_pool_size",
    "Database connection pool size",
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "idkit_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


# =============================================================================
# Redis Metrics
# =============================================================================

REDIS_CONNECTIONS_ACTIVE = Gauge(
    "idkit_redis_connections_active",
    "Number of active Redis connections",
)

REDIS_OPERATIONS_TOTAL = Counter(
    "idkit_redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)


# =============================================================================
# GPU Job Metrics
# =============================================================================

GPU_JOBS_QUEUED = Gauge(
    "idkit_gpu_jobs_queued",
    "Number of GPU jobs currently in queue",
    ["job_type"],
)

GPU_JOBS_PROCESSING = Gauge(
    "idkit_gpu_jobs_processing",
    "Number of GPU jobs currently being processed",
    ["job_type", "worker"],
)

GPU_JOBS_TOTAL = Counter(
    "idkit_gpu_jobs_total",
    "Total GPU jobs processed",
    ["job_type", "status"],
)

GPU_JOB_DURATION_SECONDS = Histogram(
    "idkit_gpu_job_duration_seconds",
    "GPU job processing duration in seconds",
    ["job_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)


# =============================================================================
# WebSocket Metrics
# =============================================================================

WEBSOCKET_CONNECTIONS_ACTIVE = Gauge(
    "idkit_websocket_connections_active",
    "Number of active WebSocket connections",
    ["connection_type"],
)

WEBSOCKET_MESSAGES_TOTAL = Counter(
    "idkit_websocket_messages_total",
    "Total WebSocket messages",
    ["direction", "message_type"],
)


# =============================================================================
# Business Metrics
# =============================================================================

CONTENT_GENERATED_TOTAL = Counter(
    "idkit_content_generated_total",
    "Total content items generated",
    ["content_type", "ai_provider"],
)

SOCIAL_POSTS_PUBLISHED_TOTAL = Counter(
    "idkit_social_posts_published_total",
    "Total social media posts published",
    ["platform", "status"],
)

PODCAST_EPISODES_CREATED_TOTAL = Counter(
    "idkit_podcast_episodes_created_total",
    "Total podcast episodes created",
    ["generation_type"],
)

ACTIVE_USERS = Gauge(
    "idkit_active_users",
    "Number of active users",
    ["period"],  # "daily", "weekly", "monthly"
)


# =============================================================================
# Middleware
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics.

    Tracks:
    - Request counts by method, endpoint, status
    - Request duration histogram
    - In-progress request gauge
    """

    def __init__(self, app, app_name: str = "idkit"):
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method

        # Get the matched route path for consistent labeling
        endpoint = self._get_endpoint_label(request)

        # Skip metrics endpoint to avoid recursion
        if endpoint == "/metrics":
            return await call_next(request)

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Record duration
            duration = time.perf_counter() - start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Record request count
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            # Decrement in-progress
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

        return response

    def _get_endpoint_label(self, request: Request) -> str:
        """
        Get a consistent endpoint label from the request.
        Uses the route path template rather than the actual path
        to avoid high cardinality from path parameters.
        """
        # Try to match against routes to get the path template
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, "path", request.url.path)

        # Fallback to the actual path (truncated for safety)
        path = request.url.path
        # Limit path depth to prevent cardinality explosion
        parts = path.split("/")[:4]
        return "/".join(parts)


# =============================================================================
# Metric Update Functions
# =============================================================================

def set_app_info(version: str, environment: str):
    """Set application info metric."""
    APP_INFO.info({
        "version": version,
        "environment": environment,
    })


def update_db_pool_metrics(active: int, pool_size: int):
    """Update database connection pool metrics."""
    DB_CONNECTIONS_ACTIVE.set(active)
    DB_CONNECTIONS_POOL_SIZE.set(pool_size)


def record_db_query(operation: str, duration: float):
    """Record a database query duration."""
    DB_QUERY_DURATION_SECONDS.labels(operation=operation).observe(duration)


def update_redis_connections(active: int):
    """Update Redis connection count."""
    REDIS_CONNECTIONS_ACTIVE.set(active)


def record_redis_operation(operation: str, success: bool):
    """Record a Redis operation."""
    status = "success" if success else "error"
    REDIS_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()


def update_gpu_queue(job_type: str, count: int):
    """Update GPU job queue count."""
    GPU_JOBS_QUEUED.labels(job_type=job_type).set(count)


def record_gpu_job_complete(job_type: str, duration: float, success: bool):
    """Record a completed GPU job."""
    status = "success" if success else "error"
    GPU_JOBS_TOTAL.labels(job_type=job_type, status=status).inc()
    GPU_JOB_DURATION_SECONDS.labels(job_type=job_type).observe(duration)


def update_websocket_connections(connection_type: str, count: int):
    """Update WebSocket connection count."""
    WEBSOCKET_CONNECTIONS_ACTIVE.labels(connection_type=connection_type).set(count)


def record_websocket_message(direction: str, message_type: str):
    """Record a WebSocket message."""
    WEBSOCKET_MESSAGES_TOTAL.labels(
        direction=direction,
        message_type=message_type
    ).inc()


def record_content_generated(content_type: str, ai_provider: str):
    """Record content generation."""
    CONTENT_GENERATED_TOTAL.labels(
        content_type=content_type,
        ai_provider=ai_provider,
    ).inc()


def record_social_post(platform: str, success: bool):
    """Record a social media post."""
    status = "success" if success else "error"
    SOCIAL_POSTS_PUBLISHED_TOTAL.labels(platform=platform, status=status).inc()


def record_podcast_episode(generation_type: str):
    """Record podcast episode creation."""
    PODCAST_EPISODES_CREATED_TOTAL.labels(generation_type=generation_type).inc()


def update_active_users(period: str, count: int):
    """Update active user count."""
    ACTIVE_USERS.labels(period=period).set(count)
