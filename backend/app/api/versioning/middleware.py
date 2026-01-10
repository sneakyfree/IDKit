"""
API Version Middleware

Middleware for handling API version negotiation and deprecation warnings.
"""

from datetime import date
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .version import APIVersion, CURRENT_VERSION, VersionStatus
from .negotiator import VersionNegotiator, VersionNegotiationError
from .deprecation import add_deprecation_warning, create_version_deprecation


class VersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that handles API version negotiation.

    Features:
    - Negotiates API version from headers or URL
    - Adds version info to response headers
    - Issues deprecation warnings for old versions
    - Rejects requests for unsupported versions
    """

    # Response header names
    API_VERSION_HEADER = "X-API-Version"
    LATEST_VERSION_HEADER = "X-API-Latest-Version"
    SUPPORTED_VERSIONS_HEADER = "X-API-Supported-Versions"

    def __init__(
        self,
        app: ASGIApp,
        negotiator: VersionNegotiator = None,
        add_headers: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize the version middleware.

        Args:
            app: The ASGI application
            negotiator: Custom version negotiator (optional)
            add_headers: Whether to add version headers to responses
            strict_mode: If True, reject requests with invalid versions
        """
        super().__init__(app)
        self.negotiator = negotiator or VersionNegotiator()
        self.add_headers = add_headers
        self.strict_mode = strict_mode

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process the request with version negotiation.
        """
        try:
            # Negotiate version
            version, source = self.negotiator.negotiate(request)

            # Store version info in request state
            request.state.api_version = version
            request.state.api_version_source = source

        except VersionNegotiationError as e:
            if self.strict_mode:
                # Return error response for invalid versions
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "invalid_api_version",
                        "message": str(e),
                        "requested_version": e.requested_version,
                        "supported_versions": e.supported_versions,
                    },
                    headers={
                        self.SUPPORTED_VERSIONS_HEADER: ", ".join(
                            e.supported_versions
                        ),
                    },
                )
            else:
                # Fall back to current version
                version = CURRENT_VERSION
                source = "fallback"
                request.state.api_version = version
                request.state.api_version_source = source

        # Process the request
        response = await call_next(request)

        # Add version headers if enabled
        if self.add_headers:
            self._add_version_headers(response, version, source)

        # Add deprecation warnings if applicable
        if version.is_deprecated:
            self._add_deprecation_warning(response, version)

        return response

    def _add_version_headers(
        self,
        response: Response,
        version: APIVersion,
        source: str,
    ) -> None:
        """Add version information headers to response."""
        from .version import SUPPORTED_VERSIONS

        # Current request version
        response.headers[self.API_VERSION_HEADER] = version.version_string

        # Latest available version
        response.headers[self.LATEST_VERSION_HEADER] = CURRENT_VERSION.version_string

        # All supported versions
        supported = [v.version_string for v in SUPPORTED_VERSIONS.values()]
        response.headers[self.SUPPORTED_VERSIONS_HEADER] = ", ".join(
            sorted(set(supported))
        )

        # Version source (for debugging)
        response.headers["X-API-Version-Source"] = source

    def _add_deprecation_warning(
        self,
        response: Response,
        version: APIVersion,
    ) -> None:
        """Add deprecation warning headers for deprecated versions."""
        warning = create_version_deprecation(
            version_str=version.version_string,
            deprecated_at=version.deprecated_date or date.today(),
            sunset_at=version.sunset_date,
            replacement=CURRENT_VERSION.version_string,
        )

        add_deprecation_warning(response, warning)


def get_version_middleware(
    strict_mode: bool = False,
    add_headers: bool = True,
) -> type:
    """
    Factory function to create configured VersionMiddleware.

    Usage:
        app.add_middleware(get_version_middleware(strict_mode=True))

    Args:
        strict_mode: If True, reject invalid versions with 400 error
        add_headers: If True, add version info headers to responses

    Returns:
        Configured VersionMiddleware class.
    """
    class ConfiguredVersionMiddleware(VersionMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(
                app,
                add_headers=add_headers,
                strict_mode=strict_mode,
            )

    return ConfiguredVersionMiddleware
