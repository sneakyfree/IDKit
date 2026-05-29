"""
IDKit FastAPI Application Entry Point

A TikTok-simple, AI-powered platform for influencers.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware, rate_limiter
from app.middleware.metrics import PrometheusMiddleware, set_app_info
from app.middleware.security import SecurityHeadersMiddleware, get_security_middleware_config
from app.middleware.performance import CacheMiddleware, TimingMiddleware
from app.logging_config import configure_logging, get_logger, LoggingMiddleware
from app.api.versioning import VersionMiddleware

# Initialize structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.project_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug: {settings.debug}")

    # Configure email service
    from app.services.email.service import configure_email_service

    try:
        configure_email_service()
        logger.info("Email service configured")
    except Exception as e:
        logger.warning(f"Email service configuration failed: {e}")

    # Initialize Redis connection
    from app.utils.redis import get_redis, close_redis

    try:
        redis_client = await get_redis()
        logger.info("Redis connection established")

        # Initialize rate limiter with Redis
        await rate_limiter.set_redis(redis_client)
        logger.info("Rate limiter initialized with Redis")

        # Initialize WebSocket Redis bridge for horizontal scaling
        from app.websocket.manager import RedisWebSocketBridge, connection_manager
        import app.websocket.manager as ws_manager

        ws_manager.redis_bridge = RedisWebSocketBridge(connection_manager)
        await ws_manager.redis_bridge.connect(redis_client)
        logger.info("WebSocket Redis bridge initialized")

    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without Redis.")


    # Initialize database tables in dev (sqlite preview). Use Alembic in production.
    if settings.environment != "production":
        try:
            from app.models.database import init_db
            await init_db()
            logger.info("DB tables initialized (dev)")
        except Exception as e:
            logger.warning(f"init_db failed: {e}")
    # Start WebSocket cleanup task
    cleanup_task = asyncio.create_task(_websocket_cleanup_loop())

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.project_name}")

    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # Close WebSocket Redis bridge
    try:
        import app.websocket.manager as ws_manager
        if ws_manager.redis_bridge:
            await ws_manager.redis_bridge.disconnect()
    except Exception as e:
        logger.error(f"Error closing WebSocket bridge: {e}")

    # Close Redis connections
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


async def _websocket_cleanup_loop():
    """Periodically cleanup stale WebSocket connections."""
    from app.websocket.manager import connection_manager

    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            removed = await connection_manager.cleanup_stale_connections(
                max_idle_seconds=300  # 5 minutes
            )
            if removed > 0:
                logger.info(f"Cleaned up {removed} stale WebSocket connections")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description="IDKit - AI-powered Influencer Development Kit",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

    # Prometheus metrics middleware
    app.add_middleware(PrometheusMiddleware, app_name="idkit")

    # Security headers middleware
    security_config = get_security_middleware_config()
    app.add_middleware(SecurityHeadersMiddleware, **security_config)

    # Structured logging middleware (request context and timing)
    app.add_middleware(LoggingMiddleware)

    # API versioning middleware (negotiation, headers, deprecation warnings)
    app.add_middleware(VersionMiddleware)

    # Performance middleware - response caching and timing headers
    app.add_middleware(TimingMiddleware)
    if not settings.debug:  # Only cache in production
        app.add_middleware(CacheMiddleware, default_ttl=60, max_size=1000)

    # Set app info for Prometheus
    set_app_info(version=settings.version, environment=settings.environment)

    # Include API routers
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Include WebSocket router
    from app.api.v1.websocket import router as websocket_router

    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

    # Include Stripe Connect webhook router
    from app.api.v1.webhooks_connect import router as webhooks_connect_router

    app.include_router(webhooks_connect_router, prefix="/webhooks", tags=["Webhooks"])

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.version,
            "environment": settings.environment,
        }

    @app.get("/metrics")
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint.

        Exposes application metrics in Prometheus format for scraping.
        Metrics include:
        - HTTP request counts and latencies
        - Database connection pool stats
        - Redis connection stats
        - GPU job queue metrics
        - WebSocket connection counts
        - Business metrics (content generated, posts published, etc.)
        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "name": settings.project_name,
            "version": settings.version,
            "message": "Welcome to IDKit API",
            "docs": "/docs" if settings.debug else None,
        }

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

# Offline sync status endpoint (PWA support)
@app.get("/api/v1/offline/status")
async def offline_status():
    return {"pending_actions": 0, "last_sync": None, "sync_in_progress": False, "cached_items": []}

@app.get("/api/v1/payouts/summary")
async def payouts_summary():
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Not authenticated")
