"""
API Versioning Middleware

Implements backward-compatible API versioning with:
- URL path versioning (/v1, /v2)
- Header-based versioning (X-API-Version)
- Version negotiation
- Deprecation warnings
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class APIVersion(Enum):
    V1 = "1"
    V2 = "2"
    
    @classmethod
    def from_string(cls, version: str) -> "APIVersion":
        """Parse version string to enum."""
        version = version.lstrip("v").split(".")[0]
        for v in cls:
            if v.value == version:
                return v
        raise ValueError(f"Unknown API version: {version}")
    
    @classmethod
    def latest(cls) -> "APIVersion":
        return cls.V2


# Version configuration
VERSION_CONFIG = {
    APIVersion.V1: {
        "supported": True,
        "deprecated": True,
        "sunset_date": datetime(2026, 6, 1),
        "min_client_version": None,
    },
    APIVersion.V2: {
        "supported": True,
        "deprecated": False,
        "sunset_date": None,
        "min_client_version": "2.0.0",
    },
}

# Routes that have breaking changes between versions
VERSIONED_ROUTES = {
    "/api/{version}/content": {
        APIVersion.V1: "v1_content_handler",
        APIVersion.V2: "v2_content_handler",
    },
    "/api/{version}/analytics": {
        APIVersion.V1: "v1_analytics_handler",
        APIVersion.V2: "v2_analytics_handler",
    },
}


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API version handling.
    
    Supports:
    - Path-based versioning: /api/v1/resource
    - Header-based versioning: X-API-Version: 2
    - Query param versioning: ?api_version=2
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract version from request
        version = self._extract_version(request)
        
        # Validate version
        if not self._is_supported(version):
            raise HTTPException(
                status_code=400,
                detail=f"API version {version.value} is not supported"
            )
        
        # Store version in request state
        request.state.api_version = version
        
        # Call handler
        response = await call_next(request)
        
        # Add version headers
        response.headers["X-API-Version"] = version.value
        response.headers["X-API-Latest"] = APIVersion.latest().value
        
        # Add deprecation warning if applicable
        config = VERSION_CONFIG.get(version, {})
        if config.get("deprecated"):
            sunset_date = config.get("sunset_date")
            response.headers["Deprecation"] = "true"
            if sunset_date:
                response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                response.headers["X-Deprecation-Notice"] = (
                    f"This API version is deprecated and will be removed on {sunset_date.strftime('%Y-%m-%d')}. "
                    f"Please migrate to v{APIVersion.latest().value}."
                )
        
        return response
    
    def _extract_version(self, request: Request) -> APIVersion:
        """Extract API version from request."""
        # 1. Check URL path
        path = request.url.path
        if "/v1/" in path or path.endswith("/v1"):
            return APIVersion.V1
        if "/v2/" in path or path.endswith("/v2"):
            return APIVersion.V2
        
        # 2. Check header
        header_version = request.headers.get("X-API-Version")
        if header_version:
            try:
                return APIVersion.from_string(header_version)
            except ValueError:
                pass
        
        # 3. Check query param
        query_version = request.query_params.get("api_version")
        if query_version:
            try:
                return APIVersion.from_string(query_version)
            except ValueError:
                pass
        
        # Default to latest
        return APIVersion.latest()
    
    def _is_supported(self, version: APIVersion) -> bool:
        """Check if version is supported."""
        config = VERSION_CONFIG.get(version, {})
        return config.get("supported", False)


# Decorators for version-specific handlers

def api_version(*versions: APIVersion):
    """
    Decorator to mark an endpoint as available only for specific versions.
    
    Usage:
        @api_version(APIVersion.V2)
        async def v2_only_endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if hasattr(request.state, "api_version"):
                if request.state.api_version not in versions:
                    raise HTTPException(
                        status_code=400,
                        detail=f"This endpoint requires API version {[v.value for v in versions]}"
                    )
            return await func(request, *args, **kwargs)
        wrapper._api_versions = versions
        return wrapper
    return decorator


def deprecated(sunset_date: Optional[datetime] = None, replacement: Optional[str] = None):
    """
    Decorator to mark an endpoint as deprecated.
    
    Usage:
        @deprecated(sunset_date=datetime(2026, 6, 1), replacement="/api/v2/resource")
        async def old_endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            
            # If response is a dict, add deprecation notice
            if isinstance(response, dict):
                response["_deprecation"] = {
                    "deprecated": True,
                    "sunset_date": sunset_date.isoformat() if sunset_date else None,
                    "replacement": replacement,
                }
            
            return response
        wrapper._deprecated = True
        wrapper._sunset_date = sunset_date
        wrapper._replacement = replacement
        return wrapper
    return decorator


# Response transformers for version compatibility

class ResponseTransformer:
    """
    Transform responses between API versions.
    
    Allows V2 handlers to serve V1-compatible responses when needed.
    """
    
    @staticmethod
    def transform(data: dict, from_version: APIVersion, to_version: APIVersion) -> dict:
        """Transform data from one version format to another."""
        if from_version == to_version:
            return data
        
        if from_version == APIVersion.V2 and to_version == APIVersion.V1:
            return ResponseTransformer._v2_to_v1(data)
        
        if from_version == APIVersion.V1 and to_version == APIVersion.V2:
            return ResponseTransformer._v1_to_v2(data)
        
        return data
    
    @staticmethod
    def _v2_to_v1(data: dict) -> dict:
        """Transform V2 response to V1 format."""
        # Example: V2 uses camelCase, V1 uses snake_case
        # Example: V2 has additional fields not in V1
        
        transformed = {}
        for key, value in data.items():
            # Convert camelCase to snake_case
            snake_key = "".join(
                f"_{c.lower()}" if c.isupper() else c
                for c in key
            ).lstrip("_")
            
            # Skip V2-only fields
            if key in ["metadata", "links", "_embedded"]:
                continue
            
            transformed[snake_key] = value
        
        return transformed
    
    @staticmethod
    def _v1_to_v2(data: dict) -> dict:
        """Transform V1 response to V2 format."""
        # Add V2 enhancements
        transformed = {}
        
        for key, value in data.items():
            # Convert snake_case to camelCase
            components = key.split("_")
            camel_key = components[0] + "".join(c.title() for c in components[1:])
            transformed[camel_key] = value
        
        # Add V2-specific fields
        transformed["metadata"] = {
            "version": "2",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return transformed


# Version negotiation

def negotiate_version(
    requested: Optional[str],
    accept_header: Optional[str],
    supported: list[APIVersion] = None
) -> APIVersion:
    """
    Negotiate the best API version based on client preferences.
    
    Args:
        requested: Explicitly requested version (from header or query)
        accept_header: Accept header for content negotiation
        supported: List of supported versions (defaults to all)
    
    Returns:
        Best matching API version
    """
    if supported is None:
        supported = [v for v in APIVersion if VERSION_CONFIG[v]["supported"]]
    
    # Explicit request takes precedence
    if requested:
        try:
            version = APIVersion.from_string(requested)
            if version in supported:
                return version
        except ValueError:
            pass
    
    # Parse accept header for version preferences
    # Format: application/vnd.idkit.v2+json
    if accept_header:
        import re
        match = re.search(r"vnd\.idkit\.v(\d+)", accept_header)
        if match:
            try:
                version = APIVersion.from_string(match.group(1))
                if version in supported:
                    return version
            except ValueError:
                pass
    
    # Default to latest supported
    return APIVersion.latest()
