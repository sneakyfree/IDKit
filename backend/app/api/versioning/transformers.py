"""
Version-specific Response Transformers

Handles transforming responses between API versions.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from functools import wraps

from fastapi import Request

from .version import APIVersion, CURRENT_VERSION


T = TypeVar("T")


class VersionTransformer(ABC):
    """
    Base class for version-specific response transformers.

    Transformers modify response data to match the expected format
    for a specific API version.
    """

    # The target version this transformer handles
    target_version: APIVersion

    @abstractmethod
    def transform(self, data: Any, request: Request) -> Any:
        """
        Transform response data for the target version.

        Args:
            data: The original response data
            request: The request (for context)

        Returns:
            The transformed response data.
        """
        pass

    @abstractmethod
    def reverse_transform(self, data: Any, request: Request) -> Any:
        """
        Transform request data from the target version to current.

        Args:
            data: The incoming request data in target version format
            request: The request (for context)

        Returns:
            The data transformed to current version format.
        """
        pass


# Registry of transformers by response type and version
_transformers: Dict[str, Dict[APIVersion, Type[VersionTransformer]]] = {}


def register_transformer(
    response_type: str,
    version: APIVersion,
) -> Callable[[Type[VersionTransformer]], Type[VersionTransformer]]:
    """
    Decorator to register a version transformer.

    Args:
        response_type: The response type this transformer handles
        version: The API version this transformer targets

    Returns:
        Decorator function.
    """
    def decorator(cls: Type[VersionTransformer]) -> Type[VersionTransformer]:
        if response_type not in _transformers:
            _transformers[response_type] = {}

        cls.target_version = version
        _transformers[response_type][version] = cls

        return cls

    return decorator


def get_transformer(
    response_type: str,
    version: APIVersion,
) -> Optional[VersionTransformer]:
    """
    Get a transformer for a specific response type and version.

    Args:
        response_type: The response type
        version: The target API version

    Returns:
        A transformer instance, or None if no transformation needed.
    """
    if response_type not in _transformers:
        return None

    transformer_class = _transformers[response_type].get(version)
    if transformer_class:
        return transformer_class()

    return None


def transform_response(
    data: Any,
    response_type: str,
    request: Request,
) -> Any:
    """
    Transform response data for the requested API version.

    Args:
        data: The response data
        response_type: The type of response
        request: The request (contains version info)

    Returns:
        Transformed response data.
    """
    # Get the requested version from request state
    version = getattr(request.state, "api_version", CURRENT_VERSION)

    # If current version, no transformation needed
    if version == CURRENT_VERSION:
        return data

    # Get transformer for this response type and version
    transformer = get_transformer(response_type, version)
    if transformer:
        return transformer.transform(data, request)

    return data


def transform_request_data(
    data: Any,
    request_type: str,
    request: Request,
) -> Any:
    """
    Transform incoming request data from the client's API version.

    Args:
        data: The incoming request data
        request_type: The type of request
        request: The request (contains version info)

    Returns:
        Transformed request data in current version format.
    """
    # Get the requested version from request state
    version = getattr(request.state, "api_version", CURRENT_VERSION)

    # If current version, no transformation needed
    if version == CURRENT_VERSION:
        return data

    # Get transformer for this request type and version
    transformer = get_transformer(request_type, version)
    if transformer:
        return transformer.reverse_transform(data, request)

    return data


def versioned_response(response_type: str):
    """
    Decorator to automatically transform responses based on API version.

    Usage:
        @versioned_response("user")
        async def get_user(...):
            return user_data

    Args:
        response_type: The type of response for transformer lookup.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            # Call original function
            result = await func(*args, **kwargs)

            # Transform if request is available
            if request:
                result = transform_response(result, response_type, request)

            return result

        return wrapper

    return decorator


# =============================================================================
# Example Transformers
# =============================================================================


class UserResponseV1_0Transformer(VersionTransformer):
    """
    Transforms User responses for v1.0 compatibility.

    v1.0 used snake_case for some fields that are now camelCase,
    and didn't include some newer fields.
    """

    def transform(self, data: Any, request: Request) -> Any:
        """Transform current version user data to v1.0 format."""
        if isinstance(data, dict):
            transformed = data.copy()

            # v1.0 didn't have 'displayName', used 'display_name'
            if "displayName" in transformed:
                transformed["display_name"] = transformed.pop("displayName")

            # v1.0 didn't have 'avatarUrl', used 'avatar_url'
            if "avatarUrl" in transformed:
                transformed["avatar_url"] = transformed.pop("avatarUrl")

            # Remove fields that didn't exist in v1.0
            transformed.pop("twoFactorEnabled", None)
            transformed.pop("lastActivityAt", None)

            return transformed

        return data

    def reverse_transform(self, data: Any, request: Request) -> Any:
        """Transform v1.0 user data to current format."""
        if isinstance(data, dict):
            transformed = data.copy()

            # Convert snake_case to camelCase
            if "display_name" in transformed:
                transformed["displayName"] = transformed.pop("display_name")

            if "avatar_url" in transformed:
                transformed["avatarUrl"] = transformed.pop("avatar_url")

            return transformed

        return data


class PaginationV1_0Transformer(VersionTransformer):
    """
    Transforms pagination responses for v1.0 compatibility.

    v1.0 used offset-based pagination, current version uses cursor-based.
    """

    def transform(self, data: Any, request: Request) -> Any:
        """Transform cursor pagination to offset pagination for v1.0."""
        if isinstance(data, dict) and "cursor" in data:
            transformed = data.copy()

            # Replace cursor with offset/limit
            cursor = transformed.pop("cursor", None)
            next_cursor = transformed.pop("nextCursor", None)

            # Estimate offset from cursor (if numeric)
            try:
                offset = int(cursor) if cursor else 0
            except (ValueError, TypeError):
                offset = 0

            transformed["offset"] = offset
            transformed["limit"] = len(data.get("items", []))
            transformed["hasMore"] = next_cursor is not None

            return transformed

        return data

    def reverse_transform(self, data: Any, request: Request) -> Any:
        """Transform offset pagination params to cursor format."""
        if isinstance(data, dict):
            transformed = data.copy()

            # Convert offset to cursor
            offset = transformed.pop("offset", 0)
            limit = transformed.pop("limit", 20)

            transformed["cursor"] = str(offset) if offset else None
            transformed["pageSize"] = limit

            return transformed

        return data
