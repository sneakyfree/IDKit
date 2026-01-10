"""
Rate Limiting Middleware

Redis-backed rate limiting with configurable rules per endpoint and user tier.
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class UserTier(str, Enum):
    """User subscription tiers with different rate limits."""

    ANONYMOUS = "anonymous"
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""

    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst_limit: Optional[int] = None  # Optional burst allowance
    tier_multipliers: dict[UserTier, float] = field(default_factory=dict)

    def get_limit_for_tier(self, tier: UserTier) -> int:
        """Get the rate limit adjusted for user tier."""
        multiplier = self.tier_multipliers.get(tier, 1.0)
        return int(self.requests * multiplier)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: Optional[int] = None
    limit: int = 0
    window: int = 0


# Default rate limit rules by endpoint pattern
DEFAULT_RULES: dict[str, RateLimitRule] = {
    # Authentication endpoints - stricter limits
    "/api/v1/auth/login": RateLimitRule(
        requests=5,
        window_seconds=60,
        tier_multipliers={
            UserTier.ANONYMOUS: 1.0,
            UserTier.FREE: 1.0,
        },
    ),
    "/api/v1/auth/register": RateLimitRule(
        requests=3,
        window_seconds=300,
        tier_multipliers={
            UserTier.ANONYMOUS: 1.0,
        },
    ),
    "/api/v1/auth/password-reset": RateLimitRule(
        requests=3,
        window_seconds=3600,
    ),
    # AI Generation endpoints - resource intensive
    "/api/v1/twins/*/generate": RateLimitRule(
        requests=10,
        window_seconds=3600,
        tier_multipliers={
            UserTier.FREE: 0.5,  # 5 per hour
            UserTier.STARTER: 1.0,  # 10 per hour
            UserTier.PRO: 3.0,  # 30 per hour
            UserTier.ENTERPRISE: 10.0,  # 100 per hour
        },
    ),
    "/api/v1/content/generate": RateLimitRule(
        requests=20,
        window_seconds=3600,
        tier_multipliers={
            UserTier.FREE: 0.5,
            UserTier.STARTER: 1.0,
            UserTier.PRO: 2.5,
            UserTier.ENTERPRISE: 10.0,
        },
    ),
    "/api/v1/podcasts/*/episodes/generate": RateLimitRule(
        requests=5,
        window_seconds=3600,
        tier_multipliers={
            UserTier.FREE: 0.2,  # 1 per hour
            UserTier.STARTER: 1.0,  # 5 per hour
            UserTier.PRO: 2.0,  # 10 per hour
            UserTier.ENTERPRISE: 10.0,  # 50 per hour
        },
    ),
    # Social posting - prevent spam
    "/api/v1/posts": RateLimitRule(
        requests=30,
        window_seconds=3600,
        tier_multipliers={
            UserTier.FREE: 0.5,
            UserTier.STARTER: 1.0,
            UserTier.PRO: 2.0,
            UserTier.ENTERPRISE: 5.0,
        },
    ),
    "/api/v1/social/publish": RateLimitRule(
        requests=50,
        window_seconds=3600,
        tier_multipliers={
            UserTier.FREE: 0.2,
            UserTier.STARTER: 1.0,
            UserTier.PRO: 2.0,
            UserTier.ENTERPRISE: 5.0,
        },
    ),
    # Search endpoints - moderate limits
    "/api/v1/search": RateLimitRule(
        requests=60,
        window_seconds=60,
        tier_multipliers={
            UserTier.ANONYMOUS: 0.5,
            UserTier.FREE: 1.0,
            UserTier.STARTER: 2.0,
            UserTier.PRO: 3.0,
            UserTier.ENTERPRISE: 10.0,
        },
    ),
    # Default global rate limit
    "default": RateLimitRule(
        requests=100,
        window_seconds=60,
        burst_limit=120,
        tier_multipliers={
            UserTier.ANONYMOUS: 0.5,
            UserTier.FREE: 1.0,
            UserTier.STARTER: 2.0,
            UserTier.PRO: 3.0,
            UserTier.ENTERPRISE: 10.0,
            UserTier.ADMIN: 100.0,
        },
    ),
}


class RateLimiter:
    """
    Redis-backed sliding window rate limiter.

    Uses a sliding window log algorithm for accurate rate limiting.
    """

    def __init__(
        self,
        redis_client=None,
        rules: Optional[dict[str, RateLimitRule]] = None,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis_client
        self.rules = rules or DEFAULT_RULES
        self.key_prefix = key_prefix
        self._local_cache: dict[str, list[float]] = {}  # Fallback if Redis unavailable
        self._lock = asyncio.Lock()

    async def set_redis(self, redis_client):
        """Set Redis client after initialization."""
        self.redis = redis_client

    def _get_rule(self, path: str) -> RateLimitRule:
        """Get the rate limit rule for a given path."""
        # Check exact match first
        if path in self.rules:
            return self.rules[path]

        # Check wildcard patterns
        for pattern, rule in self.rules.items():
            if pattern == "default":
                continue
            if self._match_pattern(path, pattern):
                return rule

        return self.rules.get("default", DEFAULT_RULES["default"])

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match path against pattern with wildcard support."""
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part == "*":
                continue
            if pattern_part != path_part:
                return False

        return True

    def _get_key(self, identifier: str, path: str) -> str:
        """Generate Redis key for rate limiting."""
        # Normalize path for pattern matching
        path_hash = hashlib.md5(path.encode()).hexdigest()[:8]
        return f"{self.key_prefix}:{identifier}:{path_hash}"

    async def check_rate_limit(
        self,
        identifier: str,
        path: str,
        tier: UserTier = UserTier.ANONYMOUS,
    ) -> RateLimitResult:
        """
        Check if request is within rate limit.

        Uses sliding window log algorithm.
        """
        rule = self._get_rule(path)
        limit = rule.get_limit_for_tier(tier)
        window = rule.window_seconds
        now = time.time()
        window_start = now - window

        key = self._get_key(identifier, path)

        if self.redis:
            return await self._check_redis(key, limit, window, now, window_start)
        else:
            return await self._check_local(key, limit, window, now, window_start)

    async def _check_redis(
        self,
        key: str,
        limit: int,
        window: int,
        now: float,
        window_start: float,
    ) -> RateLimitResult:
        """Check rate limit using Redis."""
        try:
            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Set expiry on key
            pipe.expire(key, window + 1)

            results = await pipe.execute()
            count = results[1]

            reset_at = int(now + window)
            remaining = max(0, limit - count - 1)

            if count >= limit:
                # Get oldest entry to calculate retry time
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window - now) + 1
                else:
                    retry_after = window

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                    limit=limit,
                    window=window,
                )

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_at=reset_at,
                limit=limit,
                window=window,
            )

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                remaining=limit,
                reset_at=int(now + window),
                limit=limit,
                window=window,
            )

    async def _check_local(
        self,
        key: str,
        limit: int,
        window: int,
        now: float,
        window_start: float,
    ) -> RateLimitResult:
        """Fallback to local in-memory rate limiting."""
        async with self._lock:
            if key not in self._local_cache:
                self._local_cache[key] = []

            # Remove old entries
            self._local_cache[key] = [
                ts for ts in self._local_cache[key] if ts > window_start
            ]

            count = len(self._local_cache[key])
            reset_at = int(now + window)

            if count >= limit:
                retry_after = int(self._local_cache[key][0] + window - now) + 1
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                    limit=limit,
                    window=window,
                )

            # Add current request
            self._local_cache[key].append(now)

            return RateLimitResult(
                allowed=True,
                remaining=limit - count - 1,
                reset_at=reset_at,
                limit=limit,
                window=window,
            )

    async def reset(self, identifier: str, path: str):
        """Reset rate limit for an identifier (admin function)."""
        key = self._get_key(identifier, path)
        if self.redis:
            await self.redis.delete(key)
        else:
            async with self._lock:
                self._local_cache.pop(key, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Extracts user information from request and applies rate limits.
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: Optional[RateLimiter] = None,
        get_tier_callback: Optional[Callable[[Request], UserTier]] = None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.get_tier_callback = get_tier_callback

    def _get_identifier(self, request: Request) -> str:
        """Extract identifier from request for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    async def _get_tier(self, request: Request) -> UserTier:
        """Get user tier from request."""
        if self.get_tier_callback:
            return self.get_tier_callback(request)

        # Try to get from request state
        tier = getattr(request.state, "user_tier", None)
        if tier:
            return UserTier(tier)

        # Check if user is authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return UserTier.FREE  # Default authenticated user tier

        return UserTier.ANONYMOUS

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiter."""
        path = request.url.path

        # Skip exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip WebSocket connections (handled separately)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        identifier = self._get_identifier(request)
        tier = await self._get_tier(request)

        result = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            path=path,
            tier=tier,
        )

        if not result.allowed:
            logger.warning(
                f"Rate limit exceeded: {identifier} on {path} "
                f"(tier: {tier.value}, retry_after: {result.retry_after}s)"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": result.retry_after,
                    "limit": result.limit,
                    "window": result.window,
                },
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.reset_at),
                    "Retry-After": str(result.retry_after),
                },
            )

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)

        return response


# Dependency for per-endpoint rate limiting
class EndpointRateLimiter:
    """
    Dependency for custom per-endpoint rate limiting.

    Usage:
        @router.post("/expensive-operation")
        async def expensive_op(
            rate_limit: None = Depends(EndpointRateLimiter(requests=5, window=3600))
        ):
            pass
    """

    def __init__(
        self,
        requests: int,
        window: int,
        identifier_func: Optional[Callable[[Request], str]] = None,
    ):
        self.requests = requests
        self.window = window
        self.identifier_func = identifier_func
        self._limiter: Optional[RateLimiter] = None

    async def __call__(self, request: Request):
        """Check rate limit for this endpoint."""
        from app.utils.redis import get_redis

        if not self._limiter:
            try:
                redis = await get_redis()
                self._limiter = RateLimiter(redis_client=redis)
            except Exception:
                self._limiter = RateLimiter()

        if self.identifier_func:
            identifier = self.identifier_func(request)
        else:
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                identifier = f"user:{user_id}"
            else:
                ip = request.client.host if request.client else "unknown"
                identifier = f"ip:{ip}"

        # Create custom rule for this endpoint
        rule = RateLimitRule(requests=self.requests, window_seconds=self.window)
        self._limiter.rules[request.url.path] = rule

        result = await self._limiter.check_rate_limit(
            identifier=identifier,
            path=request.url.path,
        )

        if not result.allowed:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": result.retry_after,
                },
                headers={
                    "Retry-After": str(result.retry_after),
                },
            )

        return None


# Global rate limiter instance
rate_limiter = RateLimiter()
