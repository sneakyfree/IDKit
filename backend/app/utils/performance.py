"""
Performance Optimization Utilities

Tools for monitoring, profiling, and optimizing application performance.
Includes caching, rate limiting, batch processing, and memory management.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Generic, Optional, TypeVar, Union

import redis.asyncio as redis

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


# =============================================================================
# Caching
# =============================================================================


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    ttl_seconds: int = 300  # 5 minutes default
    max_size: int = 1000
    namespace: str = "idkit"
    serialize: bool = True


class InMemoryCache(Generic[T]):
    """
    Simple in-memory cache with TTL and LRU eviction.

    Usage:
        cache = InMemoryCache[str](max_size=100, ttl_seconds=60)
        cache.set("key", "value")
        value = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 300,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[T, float]] = {}
        self._access_order: list[str] = []

    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]

        if time.time() > expires_at:
            self._remove(key)
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return value

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.ttl_seconds
        expires_at = time.time() + ttl

        # Evict oldest entries if at capacity
        while len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = (value, expires_at)

        if key not in self._access_order:
            self._access_order.append(key)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            self._remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()
        self._access_order.clear()

    def _remove(self, key: str) -> None:
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_oldest(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            oldest = self._access_order.pop(0)
            if oldest in self._cache:
                del self._cache[oldest]


class RedisCache:
    """
    Redis-backed cache with automatic serialization.

    Usage:
        cache = RedisCache(redis_client, namespace="users")
        await cache.set("user:123", user_data)
        user = await cache.get("user:123")
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        namespace: str = "idkit",
        default_ttl: int = 300,
    ):
        self.redis = redis_client
        self.namespace = namespace
        self.default_ttl = default_ttl

    def _key(self, key: str) -> str:
        """Generate namespaced key."""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        data = await self.redis.get(self._key(key))
        if data:
            return json.loads(data)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in Redis."""
        ttl = ttl or self.default_ttl
        await self.redis.setex(
            self._key(key),
            ttl,
            json.dumps(value, default=str),
        )

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        result = await self.redis.delete(self._key(key))
        return result > 0

    async def clear_namespace(self) -> int:
        """Clear all keys in namespace."""
        pattern = f"{self.namespace}:*"
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute and cache."""
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set(key, value, ttl)
        return value


def cached(
    ttl_seconds: int = 300,
    key_builder: Optional[Callable[..., str]] = None,
    cache: Optional[InMemoryCache] = None,
):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl_seconds=60)
        async def get_user(user_id: str):
            return await db.fetch_user(user_id)
    """
    _cache = cache or InMemoryCache(ttl_seconds=ttl_seconds)

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> R:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try cache
            result = _cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Cache result
            _cache.set(cache_key, result)
            return result

        wrapper.cache = _cache
        wrapper.cache_clear = _cache.clear
        return wrapper

    return decorator


# =============================================================================
# Rate Limiting
# =============================================================================


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int = 100
    window_seconds: int = 60
    burst_size: int = 10


class RateLimiter:
    """
    Token bucket rate limiter.

    Usage:
        limiter = RateLimiter(requests=100, window_seconds=60)
        if await limiter.acquire("user:123"):
            # Process request
        else:
            # Rate limited
    """

    def __init__(
        self,
        requests: int = 100,
        window_seconds: int = 60,
        burst_size: Optional[int] = None,
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or min(requests // 10, 10)

        # Tokens added per second
        self.refill_rate = requests / window_seconds

        # State per key
        self._buckets: dict[str, dict] = {}

    async def acquire(
        self,
        key: str,
        tokens: int = 1,
    ) -> bool:
        """Acquire tokens from rate limiter."""
        now = time.time()

        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": float(self.requests),
                "last_update": now,
            }

        bucket = self._buckets[key]

        # Refill tokens based on elapsed time
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            float(self.requests),
            bucket["tokens"] + elapsed * self.refill_rate,
        )
        bucket["last_update"] = now

        # Check if we have enough tokens
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True

        return False

    def get_wait_time(self, key: str, tokens: int = 1) -> float:
        """Get seconds to wait before tokens available."""
        if key not in self._buckets:
            return 0.0

        bucket = self._buckets[key]
        if bucket["tokens"] >= tokens:
            return 0.0

        needed = tokens - bucket["tokens"]
        return needed / self.refill_rate


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis.

    Uses sliding window algorithm for accurate rate limiting.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        requests: int = 100,
        window_seconds: int = 60,
        namespace: str = "ratelimit",
    ):
        self.redis = redis_client
        self.requests = requests
        self.window_seconds = window_seconds
        self.namespace = namespace

    def _key(self, identifier: str) -> str:
        """Generate rate limit key."""
        return f"{self.namespace}:{identifier}"

    async def acquire(
        self,
        identifier: str,
        tokens: int = 1,
    ) -> tuple[bool, dict]:
        """
        Acquire tokens, returns (allowed, info).

        Info contains:
        - remaining: tokens remaining in window
        - reset_at: when window resets
        - retry_after: seconds to wait if rate limited
        """
        now = time.time()
        window_start = now - self.window_seconds
        key = self._key(identifier)

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add new request with score as timestamp
        pipe.zadd(key, {f"{now}:{tokens}": now})

        # Set expiry
        pipe.expire(key, self.window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, self.requests - current_count - tokens)
        reset_at = now + self.window_seconds

        info = {
            "remaining": remaining,
            "limit": self.requests,
            "reset_at": reset_at,
            "retry_after": 0,
        }

        if current_count + tokens > self.requests:
            # Rate limited
            info["retry_after"] = self.window_seconds - (now - window_start)
            return False, info

        return True, info


def rate_limited(
    requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Decorator for rate limiting functions.

    Usage:
        @rate_limited(requests=10, window_seconds=60)
        async def api_call(user_id: str):
            pass
    """
    limiter = RateLimiter(requests=requests, window_seconds=window_seconds)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "global"

            if not await limiter.acquire(key):
                wait_time = limiter.get_wait_time(key)
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {wait_time:.1f}s"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""
    pass


# =============================================================================
# Batch Processing
# =============================================================================


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 100
    max_wait_ms: int = 100
    max_concurrent: int = 10


class BatchProcessor(Generic[T, R]):
    """
    Batch multiple requests together for efficiency.

    Usage:
        processor = BatchProcessor(
            process_func=bulk_db_insert,
            batch_size=100,
            max_wait_ms=50,
        )

        result = await processor.submit(item)
    """

    def __init__(
        self,
        process_func: Callable[[list[T]], list[R]],
        batch_size: int = 100,
        max_wait_ms: int = 100,
    ):
        self.process_func = process_func
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_ms / 1000

        self._queue: list[tuple[T, asyncio.Future]] = []
        self._lock = asyncio.Lock()
        self._processing = False

    async def submit(self, item: T) -> R:
        """Submit item for batch processing."""
        future: asyncio.Future = asyncio.Future()

        async with self._lock:
            self._queue.append((item, future))

            if len(self._queue) >= self.batch_size:
                asyncio.create_task(self._process_batch())
            elif not self._processing:
                asyncio.create_task(self._delayed_process())

        return await future

    async def _delayed_process(self) -> None:
        """Process after max wait time."""
        await asyncio.sleep(self.max_wait_seconds)
        await self._process_batch()

    async def _process_batch(self) -> None:
        """Process queued items."""
        async with self._lock:
            if not self._queue:
                return

            self._processing = True
            batch = self._queue[: self.batch_size]
            self._queue = self._queue[self.batch_size :]

        items = [item for item, _ in batch]
        futures = [future for _, future in batch]

        try:
            if asyncio.iscoroutinefunction(self.process_func):
                results = await self.process_func(items)
            else:
                results = self.process_func(items)

            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)

        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)

        finally:
            async with self._lock:
                self._processing = False


# =============================================================================
# Connection Pooling
# =============================================================================


class ConnectionPool(Generic[T]):
    """
    Generic connection pool.

    Usage:
        pool = ConnectionPool(
            create_conn=create_db_connection,
            max_size=10,
        )

        async with pool.acquire() as conn:
            await conn.execute(query)
    """

    def __init__(
        self,
        create_conn: Callable[[], T],
        max_size: int = 10,
        min_size: int = 1,
        max_idle_time: int = 300,
    ):
        self.create_conn = create_conn
        self.max_size = max_size
        self.min_size = min_size
        self.max_idle_time = max_idle_time

        self._pool: list[tuple[T, float]] = []
        self._in_use: set[T] = set()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_size)

    async def acquire(self) -> T:
        """Acquire connection from pool."""
        await self._semaphore.acquire()

        async with self._lock:
            # Get from pool
            now = time.time()
            while self._pool:
                conn, created_at = self._pool.pop(0)
                if now - created_at < self.max_idle_time:
                    self._in_use.add(conn)
                    return conn

            # Create new connection
            if asyncio.iscoroutinefunction(self.create_conn):
                conn = await self.create_conn()
            else:
                conn = self.create_conn()

            self._in_use.add(conn)
            return conn

    async def release(self, conn: T) -> None:
        """Release connection back to pool."""
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append((conn, time.time()))

        self._semaphore.release()

    @asynccontextmanager
    async def connection(self):
        """Context manager for acquiring connection."""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)


# =============================================================================
# Performance Monitoring
# =============================================================================


@dataclass
class TimingStats:
    """Statistics for timed operations."""
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0
    recent: list[float] = field(default_factory=list)

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count > 0 else 0.0

    @property
    def p50_ms(self) -> float:
        if not self.recent:
            return 0.0
        sorted_recent = sorted(self.recent)
        return sorted_recent[len(sorted_recent) // 2]

    @property
    def p95_ms(self) -> float:
        if not self.recent:
            return 0.0
        sorted_recent = sorted(self.recent)
        idx = int(len(sorted_recent) * 0.95)
        return sorted_recent[min(idx, len(sorted_recent) - 1)]

    @property
    def p99_ms(self) -> float:
        if not self.recent:
            return 0.0
        sorted_recent = sorted(self.recent)
        idx = int(len(sorted_recent) * 0.99)
        return sorted_recent[min(idx, len(sorted_recent) - 1)]


class PerformanceMonitor:
    """
    Performance monitoring and profiling.

    Usage:
        monitor = PerformanceMonitor()

        with monitor.timer("db_query"):
            await db.execute(query)

        stats = monitor.get_stats("db_query")
    """

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._timings: dict[str, TimingStats] = defaultdict(TimingStats)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def timer(self, name: str):
        """Time an async operation."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            await self._record(name, elapsed_ms)

    def timer_sync(self, name: str):
        """Time a sync operation (context manager)."""
        return SyncTimer(self, name)

    async def _record(self, name: str, elapsed_ms: float) -> None:
        """Record timing measurement."""
        async with self._lock:
            stats = self._timings[name]
            stats.count += 1
            stats.total_ms += elapsed_ms
            stats.min_ms = min(stats.min_ms, elapsed_ms)
            stats.max_ms = max(stats.max_ms, elapsed_ms)

            stats.recent.append(elapsed_ms)
            if len(stats.recent) > self.max_samples:
                stats.recent.pop(0)

    def get_stats(self, name: str) -> Optional[TimingStats]:
        """Get timing statistics for operation."""
        return self._timings.get(name)

    def get_all_stats(self) -> dict[str, dict]:
        """Get all timing statistics."""
        return {
            name: {
                "count": stats.count,
                "avg_ms": round(stats.avg_ms, 2),
                "min_ms": round(stats.min_ms, 2),
                "max_ms": round(stats.max_ms, 2),
                "p50_ms": round(stats.p50_ms, 2),
                "p95_ms": round(stats.p95_ms, 2),
                "p99_ms": round(stats.p99_ms, 2),
            }
            for name, stats in self._timings.items()
        }

    def reset(self, name: Optional[str] = None) -> None:
        """Reset statistics."""
        if name:
            if name in self._timings:
                del self._timings[name]
        else:
            self._timings.clear()


class SyncTimer:
    """Synchronous timer context manager."""

    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start: float = 0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.perf_counter() - self.start) * 1000
        # Schedule async recording
        asyncio.create_task(self.monitor._record(self.name, elapsed_ms))


def timed(name: Optional[str] = None, monitor: Optional[PerformanceMonitor] = None):
    """
    Decorator to time function execution.

    Usage:
        @timed("user_lookup")
        async def get_user(user_id: str):
            pass
    """
    _monitor = monitor or PerformanceMonitor()

    def decorator(func: Callable) -> Callable:
        op_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with _monitor.timer(op_name):
                return await func(*args, **kwargs)

        wrapper.monitor = _monitor
        return wrapper

    return decorator


# =============================================================================
# Memory Management
# =============================================================================


class MemoryTracker:
    """
    Track memory usage of objects.

    Usage:
        tracker = MemoryTracker()
        tracker.track("cache", my_cache)

        report = tracker.get_report()
    """

    def __init__(self):
        self._tracked: dict[str, Any] = {}

    def track(self, name: str, obj: Any) -> None:
        """Track an object's memory usage."""
        import sys
        self._tracked[name] = {
            "obj": obj,
            "size_bytes": sys.getsizeof(obj),
            "tracked_at": datetime.utcnow(),
        }

    def untrack(self, name: str) -> None:
        """Stop tracking an object."""
        if name in self._tracked:
            del self._tracked[name]

    def get_report(self) -> dict:
        """Get memory usage report."""
        import sys

        report = {
            "total_tracked_bytes": 0,
            "objects": {},
        }

        for name, info in self._tracked.items():
            current_size = sys.getsizeof(info["obj"])
            report["objects"][name] = {
                "size_bytes": current_size,
                "size_mb": round(current_size / (1024 * 1024), 2),
                "tracked_since": info["tracked_at"].isoformat(),
            }
            report["total_tracked_bytes"] += current_size

        report["total_tracked_mb"] = round(
            report["total_tracked_bytes"] / (1024 * 1024), 2
        )

        return report


# =============================================================================
# Retry Utilities
# =============================================================================


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry async function with exponential backoff.

    Usage:
        result = await retry_async(
            lambda: api.fetch_data(),
            max_retries=3,
            base_delay=1.0,
        )
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            return func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                break

            delay = base_delay
            if exponential:
                delay = min(base_delay * (2 ** attempt), max_delay)

            logger.warning(
                f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}"
            )
            await asyncio.sleep(delay)

    raise last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retry with exponential backoff.

    Usage:
        @with_retry(max_retries=3)
        async def unreliable_api_call():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                exceptions=exceptions,
            )

        return wrapper

    return decorator


# =============================================================================
# Async Utilities
# =============================================================================


async def gather_with_concurrency(
    tasks: list[Callable],
    max_concurrent: int = 10,
) -> list[Any]:
    """
    Run tasks with limited concurrency.

    Usage:
        results = await gather_with_concurrency(
            [lambda: fetch(url) for url in urls],
            max_concurrent=5,
        )
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_task(task: Callable) -> Any:
        async with semaphore:
            if asyncio.iscoroutinefunction(task):
                return await task()
            return task()

    return await asyncio.gather(
        *[limited_task(task) for task in tasks],
        return_exceptions=True,
    )


async def timeout_after(
    coro,
    timeout_seconds: float,
    default: Any = None,
) -> Any:
    """
    Execute coroutine with timeout.

    Usage:
        result = await timeout_after(
            slow_operation(),
            timeout_seconds=5.0,
            default="timeout",
        )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout_seconds}s")
        return default


class Debouncer:
    """
    Debounce rapid function calls.

    Usage:
        debouncer = Debouncer(delay_seconds=1.0)

        @debouncer.debounce
        async def save_to_db(data):
            pass
    """

    def __init__(self, delay_seconds: float = 1.0):
        self.delay_seconds = delay_seconds
        self._tasks: dict[str, asyncio.Task] = {}

    def debounce(self, func: Callable) -> Callable:
        """Debounce decorator."""

        @functools.wraps(func)
        async def wrapper(*args, key: str = "default", **kwargs):
            # Cancel existing task
            if key in self._tasks:
                self._tasks[key].cancel()

            # Schedule new task
            async def delayed():
                await asyncio.sleep(self.delay_seconds)
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            self._tasks[key] = asyncio.create_task(delayed())
            return await self._tasks[key]

        return wrapper
