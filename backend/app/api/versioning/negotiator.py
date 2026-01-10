"""
Version Negotiation

Handles version negotiation from request headers and URL paths.
"""

from typing import Optional, Tuple
import re

from fastapi import Request

from .version import (
    APIVersion,
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    parse_version,
    is_version_supported,
)


class VersionNegotiationError(Exception):
    """Raised when version negotiation fails."""

    def __init__(
        self,
        message: str,
        requested_version: Optional[str] = None,
        supported_versions: Optional[list[str]] = None,
    ):
        super().__init__(message)
        self.requested_version = requested_version
        self.supported_versions = supported_versions or list(SUPPORTED_VERSIONS.keys())


class VersionNegotiator:
    """
    Negotiates the API version to use for a request.

    Supports multiple methods of version specification:
    1. Accept-Version header (highest priority)
    2. X-API-Version header
    3. URL path prefix (e.g., /api/v1/...)
    4. Default to current version
    """

    # Header names for version specification
    ACCEPT_VERSION_HEADER = "Accept-Version"
    API_VERSION_HEADER = "X-API-Version"

    # Regex to extract version from URL path
    URL_VERSION_PATTERN = re.compile(r"/api/(v\d+(?:\.\d+)?)/")

    def __init__(self, default_version: APIVersion = CURRENT_VERSION):
        """
        Initialize the version negotiator.

        Args:
            default_version: Default version to use if none specified.
        """
        self.default_version = default_version

    def negotiate(self, request: Request) -> Tuple[APIVersion, str]:
        """
        Negotiate the API version for a request.

        Args:
            request: The incoming FastAPI request.

        Returns:
            Tuple of (negotiated_version, source) where source indicates
            how the version was determined ('header', 'url', 'default').

        Raises:
            VersionNegotiationError: If requested version is not supported.
        """
        # Try headers first (highest priority)
        version, source = self._from_headers(request)
        if version:
            return version, source

        # Try URL path
        version, source = self._from_url(request)
        if version:
            return version, source

        # Fall back to default
        return self.default_version, "default"

    def _from_headers(self, request: Request) -> Tuple[Optional[APIVersion], str]:
        """
        Extract version from request headers.

        Checks Accept-Version first, then X-API-Version.
        """
        # Check Accept-Version header
        accept_version = request.headers.get(self.ACCEPT_VERSION_HEADER)
        if accept_version:
            version = self._parse_and_validate(accept_version)
            if version:
                return version, "header:Accept-Version"

        # Check X-API-Version header
        api_version = request.headers.get(self.API_VERSION_HEADER)
        if api_version:
            version = self._parse_and_validate(api_version)
            if version:
                return version, "header:X-API-Version"

        return None, ""

    def _from_url(self, request: Request) -> Tuple[Optional[APIVersion], str]:
        """Extract version from URL path."""
        path = request.url.path
        match = self.URL_VERSION_PATTERN.search(path)

        if match:
            version_str = match.group(1)
            version = parse_version(version_str)
            if version and is_version_supported(version):
                return version, "url"

        return None, ""

    def _parse_and_validate(self, version_str: str) -> Optional[APIVersion]:
        """
        Parse a version string and validate it's supported.

        Raises VersionNegotiationError if version is not supported.
        """
        version = parse_version(version_str)

        if version is None:
            raise VersionNegotiationError(
                f"Unknown API version: {version_str}",
                requested_version=version_str,
            )

        if not is_version_supported(version):
            raise VersionNegotiationError(
                f"API version {version_str} is no longer supported",
                requested_version=version_str,
            )

        return version


# Global negotiator instance
_negotiator = VersionNegotiator()


def get_requested_version(request: Request) -> APIVersion:
    """
    Get the API version for a request.

    This is the primary function to use in route handlers.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The negotiated API version.
    """
    version, _ = _negotiator.negotiate(request)

    # Store version info in request state for later use
    request.state.api_version = version

    return version


def get_version_source(request: Request) -> str:
    """Get the source of the version negotiation for a request."""
    _, source = _negotiator.negotiate(request)
    return source
