"""
Redis Client

Provides async Redis client for caching and pub/sub.
"""

from typing import Any, Optional
import json

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings

# Global Redis client
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get or create Redis client."""
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class CacheService:
    """High-level caching service."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        await self.redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.redis.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment counter."""
        return await self.redis.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiration on key."""
        await self.redis.expire(key, ttl)


class RateLimiter:
    """
    Redis-based rate limiter using sliding window.
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        import time

        now = time.time()
        window_start = now - window_seconds

        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry on the key
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        is_allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - 1)

        return is_allowed, remaining


class PubSub:
    """Redis Pub/Sub wrapper for real-time events."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.pubsub = redis_client.pubsub()

    async def publish(self, channel: str, message: dict) -> int:
        """Publish message to channel."""
        return await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, *channels: str) -> None:
        """Subscribe to channels."""
        await self.pubsub.subscribe(*channels)

    async def unsubscribe(self, *channels: str) -> None:
        """Unsubscribe from channels."""
        await self.pubsub.unsubscribe(*channels)

    async def listen(self):
        """Generator that yields messages."""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                except json.JSONDecodeError:
                    data = message["data"]

                yield {
                    "channel": message["channel"],
                    "data": data,
                }

    async def close(self) -> None:
        """Close pub/sub connection."""
        await self.pubsub.close()
