"""
Security Headers Middleware

Adds essential HTTP security headers to all responses:
- Content-Security-Policy (CSP)
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Headers added:
    - Strict-Transport-Security: Enforces HTTPS
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: XSS filter (legacy browsers)
    - Referrer-Policy: Controls referrer information
    - Content-Security-Policy: Controls resource loading
    - Permissions-Policy: Controls browser features
    """

    def __init__(
        self,
        app,
        csp_policy: Optional[str] = None,
        hsts_max_age: int = 31536000,  # 1 year
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None,
    ):
        super().__init__(app)

        self.hsts_max_age = hsts_max_age
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy

        # Default CSP - restrictive but functional for an API
        self.csp_policy = csp_policy or self._default_csp()

        # Default permissions policy
        self.permissions_policy = permissions_policy or self._default_permissions()

    def _default_csp(self) -> str:
        """
        Generate default Content-Security-Policy.

        For API servers, we're restrictive but allow:
        - self for scripts/styles (Swagger UI)
        - data: for inline images (Swagger)
        - CDN for Swagger assets
        """
        if settings.debug:
            # More permissive in development for Swagger UI
            return "; ".join([
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src 'self' data: https:",
                "font-src 'self' https://cdn.jsdelivr.net",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ])
        else:
            # Strict production CSP
            return "; ".join([
                "default-src 'none'",
                "script-src 'self'",
                "style-src 'self'",
                "img-src 'self' data:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ])

    def _default_permissions(self) -> str:
        """
        Generate default Permissions-Policy.

        Restricts access to sensitive browser APIs.
        """
        return ", ".join([
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Skip security headers for metrics endpoint (Prometheus scraper)
        if request.url.path == "/metrics":
            return response

        # Add security headers
        response.headers["X-Content-Type-Options"] = self.content_type_options
        response.headers["X-Frame-Options"] = self.frame_options
        response.headers["X-XSS-Protection"] = self.xss_protection
        response.headers["Referrer-Policy"] = self.referrer_policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Only add HSTS in production (when HTTPS is enforced)
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        # Prevent caching of sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint contains sensitive data that shouldn't be cached."""
        sensitive_patterns = [
            "/auth/",
            "/users/me",
            "/tokens",
            "/social/accounts",
            "/api/v1/twins",
            "/api/v1/content",
        ]
        return any(pattern in path for pattern in sensitive_patterns)


def get_security_middleware_config() -> dict:
    """
    Get security middleware configuration based on environment.

    Returns kwargs for SecurityHeadersMiddleware initialization.
    """
    if settings.debug:
        # Development: more permissive
        return {
            "hsts_max_age": 0,  # Disable HSTS in development
            "frame_options": "SAMEORIGIN",  # Allow iframes from same origin
        }
    else:
        # Production: strict defaults
        return {
            "hsts_max_age": 31536000,
            "frame_options": "DENY",
        }
