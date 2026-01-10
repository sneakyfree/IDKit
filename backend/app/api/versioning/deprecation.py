"""
Deprecation Warning System

Handles deprecation warnings for API versions and endpoints.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from enum import Enum

from fastapi import Response


class DeprecationType(str, Enum):
    """Type of deprecation."""
    VERSION = "version"
    ENDPOINT = "endpoint"
    FIELD = "field"
    PARAMETER = "parameter"


@dataclass
class DeprecationWarning:
    """
    Represents a deprecation warning.

    Attributes:
        type: Type of deprecation
        message: Human-readable deprecation message
        deprecated_at: When this was deprecated
        sunset_at: When this will be removed
        replacement: Suggested replacement (if any)
        docs_url: URL to documentation about this deprecation
    """
    type: DeprecationType
    message: str
    deprecated_at: Optional[date] = None
    sunset_at: Optional[date] = None
    replacement: Optional[str] = None
    docs_url: Optional[str] = None

    def to_header_value(self) -> str:
        """
        Format the deprecation as a Deprecation header value.

        Uses RFC 8594 format for the Deprecation header.
        """
        parts = []

        if self.deprecated_at:
            parts.append(f'date="{self.deprecated_at.isoformat()}"')

        return ", ".join(parts) if parts else "true"

    def to_sunset_header(self) -> Optional[str]:
        """
        Format the sunset date as a Sunset header value.

        Uses RFC 8594 format for the Sunset header.
        """
        if self.sunset_at:
            return self.sunset_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return None

    def to_link_header(self) -> Optional[str]:
        """
        Format documentation link as a Link header.

        Returns a Link header pointing to deprecation docs.
        """
        if self.docs_url:
            return f'<{self.docs_url}>; rel="deprecation"'
        return None


def add_deprecation_warning(
    response: Response,
    warning: DeprecationWarning,
) -> None:
    """
    Add deprecation warning headers to a response.

    Adds the following headers:
    - Deprecation: RFC 8594 deprecation notice
    - Sunset: When the feature will be removed (if known)
    - Link: Link to deprecation documentation
    - X-Deprecation-Message: Human-readable message

    Args:
        response: The FastAPI response to add headers to.
        warning: The deprecation warning to add.
    """
    # Add Deprecation header
    response.headers["Deprecation"] = warning.to_header_value()

    # Add Sunset header if sunset date is known
    sunset = warning.to_sunset_header()
    if sunset:
        response.headers["Sunset"] = sunset

    # Add Link header to documentation
    link = warning.to_link_header()
    if link:
        existing_link = response.headers.get("Link")
        if existing_link:
            response.headers["Link"] = f"{existing_link}, {link}"
        else:
            response.headers["Link"] = link

    # Add human-readable message
    response.headers["X-Deprecation-Message"] = warning.message

    # Add replacement suggestion if available
    if warning.replacement:
        response.headers["X-Deprecation-Replacement"] = warning.replacement


def create_version_deprecation(
    version_str: str,
    deprecated_at: date,
    sunset_at: Optional[date] = None,
    replacement: Optional[str] = None,
) -> DeprecationWarning:
    """
    Create a deprecation warning for an API version.

    Args:
        version_str: The deprecated version string
        deprecated_at: When this version was deprecated
        sunset_at: When this version will be removed
        replacement: Suggested replacement version

    Returns:
        A DeprecationWarning for the version.
    """
    message = f"API version {version_str} is deprecated"
    if sunset_at:
        message += f" and will be removed on {sunset_at.isoformat()}"
    message += "."

    if replacement:
        message += f" Please migrate to {replacement}."

    return DeprecationWarning(
        type=DeprecationType.VERSION,
        message=message,
        deprecated_at=deprecated_at,
        sunset_at=sunset_at,
        replacement=replacement,
        docs_url=f"/docs/migration/{version_str}",
    )


def create_endpoint_deprecation(
    endpoint: str,
    deprecated_at: date,
    sunset_at: Optional[date] = None,
    replacement: Optional[str] = None,
) -> DeprecationWarning:
    """
    Create a deprecation warning for an endpoint.

    Args:
        endpoint: The deprecated endpoint path
        deprecated_at: When this endpoint was deprecated
        sunset_at: When this endpoint will be removed
        replacement: Suggested replacement endpoint

    Returns:
        A DeprecationWarning for the endpoint.
    """
    message = f"Endpoint {endpoint} is deprecated"
    if sunset_at:
        message += f" and will be removed on {sunset_at.isoformat()}"
    message += "."

    if replacement:
        message += f" Please use {replacement} instead."

    return DeprecationWarning(
        type=DeprecationType.ENDPOINT,
        message=message,
        deprecated_at=deprecated_at,
        sunset_at=sunset_at,
        replacement=replacement,
        docs_url=f"/docs/endpoints{endpoint}",
    )


def create_field_deprecation(
    field: str,
    deprecated_at: date,
    sunset_at: Optional[date] = None,
    replacement: Optional[str] = None,
) -> DeprecationWarning:
    """
    Create a deprecation warning for a response field.

    Args:
        field: The deprecated field name
        deprecated_at: When this field was deprecated
        sunset_at: When this field will be removed
        replacement: Suggested replacement field

    Returns:
        A DeprecationWarning for the field.
    """
    message = f"Response field '{field}' is deprecated"
    if sunset_at:
        message += f" and will be removed on {sunset_at.isoformat()}"
    message += "."

    if replacement:
        message += f" Please use '{replacement}' instead."

    return DeprecationWarning(
        type=DeprecationType.FIELD,
        message=message,
        deprecated_at=deprecated_at,
        sunset_at=sunset_at,
        replacement=replacement,
    )
