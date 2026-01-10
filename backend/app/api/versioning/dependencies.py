"""
FastAPI Dependencies for API Versioning

Provides injectable dependencies for accessing version information in routes.
"""

from typing import Annotated

from fastapi import Depends, Request

from .version import APIVersion, CURRENT_VERSION
from .negotiator import get_requested_version


def get_api_version(request: Request) -> APIVersion:
    """
    FastAPI dependency to get the current API version.

    Usage:
        @router.get("/users")
        async def get_users(version: APIVersion = Depends(get_api_version)):
            if version.major == 1 and version.minor == 0:
                # Handle v1.0 specific logic
                pass

    Args:
        request: The FastAPI request.

    Returns:
        The negotiated API version.
    """
    # Check if already negotiated and stored in state
    if hasattr(request.state, "api_version"):
        return request.state.api_version

    # Otherwise, negotiate now
    return get_requested_version(request)


def require_minimum_version(min_version: APIVersion):
    """
    Create a dependency that requires a minimum API version.

    Usage:
        @router.get("/new-feature", dependencies=[Depends(require_minimum_version(V1_1))])
        async def new_feature():
            # Only available in v1.1+
            pass

    Args:
        min_version: The minimum required version.

    Returns:
        A dependency function that raises HTTPException if version is too old.
    """
    async def check_version(request: Request):
        from fastapi import HTTPException

        version = get_api_version(request)

        if version < min_version:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "version_too_old",
                    "message": f"This endpoint requires API version {min_version.version_string} or later",
                    "current_version": version.version_string,
                    "minimum_version": min_version.version_string,
                },
            )

    return check_version


def require_exact_version(exact_version: APIVersion):
    """
    Create a dependency that requires an exact API version.

    Useful for version-specific endpoints during migrations.

    Args:
        exact_version: The required version.

    Returns:
        A dependency function that raises HTTPException if version doesn't match.
    """
    async def check_version(request: Request):
        from fastapi import HTTPException

        version = get_api_version(request)

        if version != exact_version:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "version_mismatch",
                    "message": f"This endpoint is only available in API version {exact_version.version_string}",
                    "current_version": version.version_string,
                    "required_version": exact_version.version_string,
                },
            )

    return check_version


# Type alias for cleaner route signatures
APIVersionDep = Annotated[APIVersion, Depends(get_api_version)]


def is_version(request: Request, major: int, minor: int = None) -> bool:
    """
    Check if the current request is for a specific version.

    Usage in routes:
        if is_version(request, 1, 0):
            # v1.0 specific handling
            pass

    Args:
        request: The FastAPI request
        major: Major version to check
        minor: Minor version to check (optional, matches any if None)

    Returns:
        True if version matches.
    """
    version = get_api_version(request)

    if minor is None:
        return version.major == major

    return version.major == major and version.minor == minor


def version_switch(
    request: Request,
    v1_0=None,
    v1_1=None,
    default=None,
):
    """
    Select a value based on the API version.

    Usage:
        response_schema = version_switch(
            request,
            v1_0=UserResponseV1_0,
            v1_1=UserResponseV1_1,
            default=UserResponse,
        )

    Args:
        request: The FastAPI request
        v1_0: Value for v1.0
        v1_1: Value for v1.1
        default: Default value if no match

    Returns:
        The value for the matching version.
    """
    version = get_api_version(request)

    if version.major == 1:
        if version.minor == 0 and v1_0 is not None:
            return v1_0
        if version.minor == 1 and v1_1 is not None:
            return v1_1

    return default
