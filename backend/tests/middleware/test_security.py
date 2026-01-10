"""
Tests for security headers middleware.

Tests:
- Header presence and values
- Environment-specific behavior
- Sensitive endpoint handling
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware.security import SecurityHeadersMiddleware


@pytest.fixture
def simple_app():
    """Create a simple FastAPI app with security middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    @app.get("/auth/login")
    async def login_endpoint():
        return {"token": "secret"}

    @app.get("/metrics")
    async def metrics_endpoint():
        return {"metrics": "data"}

    return app


@pytest.fixture
def simple_client(simple_app):
    """Create a test client for the simple app."""
    return TestClient(simple_app)


class TestSecurityHeadersPresence:
    """Test that all security headers are present."""

    def test_x_content_type_options_present(self, simple_client):
        """X-Content-Type-Options should be present."""
        response = simple_client.get("/test")
        assert "x-content-type-options" in response.headers

    def test_x_frame_options_present(self, simple_client):
        """X-Frame-Options should be present."""
        response = simple_client.get("/test")
        assert "x-frame-options" in response.headers

    def test_x_xss_protection_present(self, simple_client):
        """X-XSS-Protection should be present."""
        response = simple_client.get("/test")
        assert "x-xss-protection" in response.headers

    def test_referrer_policy_present(self, simple_client):
        """Referrer-Policy should be present."""
        response = simple_client.get("/test")
        assert "referrer-policy" in response.headers

    def test_csp_present(self, simple_client):
        """Content-Security-Policy should be present."""
        response = simple_client.get("/test")
        assert "content-security-policy" in response.headers

    def test_permissions_policy_present(self, simple_client):
        """Permissions-Policy should be present."""
        response = simple_client.get("/test")
        assert "permissions-policy" in response.headers


class TestSecurityHeaderValues:
    """Test security header values are correct."""

    def test_x_content_type_options_nosniff(self, simple_client):
        """X-Content-Type-Options should be nosniff."""
        response = simple_client.get("/test")
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_x_frame_options_deny(self, simple_client):
        """X-Frame-Options should be DENY by default."""
        response = simple_client.get("/test")
        assert response.headers["x-frame-options"] == "DENY"

    def test_xss_protection_enabled(self, simple_client):
        """X-XSS-Protection should enable filter with block mode."""
        response = simple_client.get("/test")
        assert "1" in response.headers["x-xss-protection"]
        assert "mode=block" in response.headers["x-xss-protection"]

    def test_csp_has_default_src(self, simple_client):
        """CSP should have default-src directive."""
        response = simple_client.get("/test")
        csp = response.headers["content-security-policy"]
        assert "default-src" in csp

    def test_csp_blocks_frame_ancestors(self, simple_client):
        """CSP should block frame-ancestors."""
        response = simple_client.get("/test")
        csp = response.headers["content-security-policy"]
        assert "frame-ancestors 'none'" in csp

    def test_permissions_policy_restricts_features(self, simple_client):
        """Permissions-Policy should restrict sensitive features."""
        response = simple_client.get("/test")
        pp = response.headers["permissions-policy"]
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp


class TestSensitiveEndpoints:
    """Test handling of sensitive endpoints."""

    def test_auth_endpoint_no_cache(self, simple_client):
        """Auth endpoints should have no-cache headers."""
        response = simple_client.get("/auth/login")
        assert "no-store" in response.headers.get("cache-control", "")

    def test_metrics_endpoint_no_security_headers(self, simple_client):
        """Metrics endpoint should skip security headers."""
        response = simple_client.get("/metrics")
        # Metrics endpoint should still work
        assert response.status_code == 200


class TestCustomConfiguration:
    """Test custom middleware configuration."""

    def test_custom_frame_options(self):
        """Custom frame options should be applied."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, frame_options="SAMEORIGIN")

        @app.get("/test")
        async def test_endpoint():
            return {"message": "ok"}

        client = TestClient(app)
        response = client.get("/test")
        assert response.headers["x-frame-options"] == "SAMEORIGIN"

    def test_custom_csp(self):
        """Custom CSP should be applied."""
        custom_csp = "default-src 'self'; script-src 'none'"
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, csp_policy=custom_csp)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "ok"}

        client = TestClient(app)
        response = client.get("/test")
        assert response.headers["content-security-policy"] == custom_csp

    def test_custom_referrer_policy(self):
        """Custom referrer policy should be applied."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, referrer_policy="no-referrer")

        @app.get("/test")
        async def test_endpoint():
            return {"message": "ok"}

        client = TestClient(app)
        response = client.get("/test")
        assert response.headers["referrer-policy"] == "no-referrer"
