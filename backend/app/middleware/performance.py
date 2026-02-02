"""
TASK 4.1.3: API Performance Middleware

Response caching, compression, and latency improvements
"""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# In-memory cache (use Redis in production)
_cache: dict[str, tuple[Any, float]] = {}


# ============================================================================
# Response Caching Middleware
# ============================================================================

class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP response caching middleware with configurable TTL.
    
    Caches GET requests based on URL + query params + auth header.
    """
    
    def __init__(self, app, default_ttl: int = 60, max_size: int = 1000):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate unique cache key from request"""
        key_parts = [
            request.method,
            str(request.url),
            request.headers.get("authorization", "anon")[:50],
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _should_cache(self, request: Request, response: Response) -> bool:
        """Determine if request/response should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Don't cache errors
        if response.status_code >= 400:
            return False
        
        # Check for no-cache headers
        cache_control = request.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        # Don't cache private/sensitive endpoints
        path = request.url.path
        sensitive_paths = ["/auth", "/payments", "/stripe", "/webhook"]
        if any(p in path for p in sensitive_paths):
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip caching for non-GET requests
        if request.method != "GET":
            return await call_next(request)
        
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached = _cache.get(cache_key)
        if cached:
            data, expires = cached
            if time.time() < expires:
                self.cache_stats["hits"] += 1
                response = JSONResponse(content=data)
                response.headers["X-Cache"] = "HIT"
                return response
            else:
                # Expired - remove from cache
                del _cache[cache_key]
        
        self.cache_stats["misses"] += 1
        
        # Call original endpoint
        response = await call_next(request)
        
        # Cache response if appropriate
        if self._should_cache(request, response):
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                data = json.loads(body)
                ttl = self._get_ttl(request.url.path)
                expires = time.time() + ttl
                
                # Evict oldest entries if cache is full
                if len(_cache) >= self.max_size:
                    oldest_key = min(_cache.keys(), key=lambda k: _cache[k][1])
                    del _cache[oldest_key]
                
                _cache[cache_key] = (data, expires)
                self.cache_stats["size"] = len(_cache)
                
                # Return new response with body
                response = JSONResponse(content=data, status_code=response.status_code)
                response.headers["X-Cache"] = "MISS"
                response.headers["Cache-Control"] = f"max-age={ttl}"
            except json.JSONDecodeError:
                # Not JSON, return original response
                return Response(content=body, status_code=response.status_code)
        
        return response
    
    def _get_ttl(self, path: str) -> int:
        """Get TTL based on endpoint path"""
        # Static/rarely changing data - longer TTL
        if "/trends" in path or "/discover" in path:
            return 300  # 5 minutes
        
        # Analytics/metrics - medium TTL
        if "/analytics" in path or "/performance" in path:
            return 120  # 2 minutes
        
        # User-specific but not real-time
        if "/content" in path or "/profile" in path:
            return 60  # 1 minute
        
        # Default
        return self.default_ttl


# ============================================================================
# Request Timing Middleware
# ============================================================================

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Add server-timing headers for performance monitoring.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Add timing headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.2f}"
        
        # Log slow requests
        if duration_ms > 500:
            print(f"SLOW REQUEST: {request.method} {request.url.path} - {duration_ms:.2f}ms")
        
        return response


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}
    
    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > window_start]
        else:
            self.requests[key] = []
        
        current_count = len(self.requests[key])
        
        if current_count >= self.max_requests:
            reset_time = min(self.requests[key]) + self.window_seconds
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset": int(reset_time),
            }
        
        # Record this request
        self.requests[key].append(now)
        
        return True, {
            "limit": self.max_requests,
            "remaining": self.max_requests - current_count - 1,
            "reset": int(now + self.window_seconds),
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with headers.
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("authorization", "")
        key = f"{client_ip}:{hashlib.md5(auth_header.encode()).hexdigest()[:8]}"
        
        allowed, info = self.limiter.is_allowed(key)
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"error": "Too many requests", "retry_after": info["reset"] - int(time.time())},
            )
            response.headers["Retry-After"] = str(info["reset"] - int(time.time()))
        else:
            response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response


# ============================================================================
# Query Optimization Utilities
# ============================================================================

def batch_queries(batch_size: int = 100):
    """
    Decorator for batching database queries.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            items = kwargs.get("items", args[0] if args else [])
            results = []
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_results = await func(batch, **kwargs)
                results.extend(batch_results)
            
            return results
        return wrapper
    return decorator


def cached_query(ttl_seconds: int = 60):
    """
    Decorator for caching query results.
    """
    def decorator(func: Callable):
        cache: dict[str, tuple[Any, float]] = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = hashlib.md5("".join(key_parts).encode()).hexdigest()
            
            # Check cache
            if cache_key in cache:
                result, expires = cache[cache_key]
                if time.time() < expires:
                    return result
            
            # Execute query
            result = await func(*args, **kwargs)
            
            # Cache result
            cache[cache_key] = (result, time.time() + ttl_seconds)
            
            return result
        return wrapper
    return decorator


# ============================================================================
# Database Connection Pooling Config
# ============================================================================

def get_optimized_pool_config() -> dict:
    """
    Returns optimized connection pool settings.
    """
    return {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,  # Recycle connections after 30 minutes
        "pool_pre_ping": True,  # Verify connections before use
    }


# ============================================================================
# Response Compression Utilities
# ============================================================================

def should_compress(content_type: str, content_length: int) -> bool:
    """
    Determine if response should be compressed.
    """
    # Only compress text-based content
    compressible_types = [
        "application/json",
        "text/html",
        "text/plain",
        "text/css",
        "application/javascript",
    ]
    
    if not any(t in content_type for t in compressible_types):
        return False
    
    # Don't compress small responses
    if content_length < 1024:  # 1KB threshold
        return False
    
    return True
