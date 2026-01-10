"""
Tests for health and core API endpoints.

Tests:
- Health check endpoint
- Metrics endpoint
- Root endpoint
- Security headers
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client: AsyncClient):
        """Health check should return 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self, client: AsyncClient):
        """Health check should return status field."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_returns_version(self, client: AsyncClient):
        """Health check should include version."""
        response = await client.get("/health")
        data = response.json()
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check_returns_environment(self, client: AsyncClient):
        """Health check should include environment."""
        response = await client.get("/health")
        data = response.json()
        assert "environment" in data


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_returns_200(self, client: AsyncClient):
        """Metrics endpoint should return 200 OK."""
        response = await client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_returns_prometheus_format(self, client: AsyncClient):
        """Metrics should be in Prometheus format."""
        response = await client.get("/metrics")
        # Prometheus format uses text/plain with specific content type
        assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_metrics_contains_app_info(self, client: AsyncClient):
        """Metrics should contain application info."""
        response = await client.get("/metrics")
        content = response.text
        assert "idkit_app_info" in content

    @pytest.mark.asyncio
    async def test_metrics_contains_http_metrics(self, client: AsyncClient):
        """Metrics should contain HTTP request metrics."""
        # Make a request first to generate metrics
        await client.get("/health")

        response = await client.get("/metrics")
        content = response.text
        assert "idkit_http_requests_total" in content


class TestRootEndpoint:
    """Tests for the / root endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, client: AsyncClient):
        """Root endpoint should return 200 OK."""
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_returns_welcome_message(self, client: AsyncClient):
        """Root should return welcome message."""
        response = await client.get("/")
        data = response.json()
        assert "message" in data
        assert "IDKit" in data["message"]

    @pytest.mark.asyncio
    async def test_root_returns_name(self, client: AsyncClient):
        """Root should return application name."""
        response = await client.get("/")
        data = response.json()
        assert "name" in data


class TestSecurityHeaders:
    """Tests for security headers on responses."""

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client: AsyncClient):
        """Response should have X-Content-Type-Options header."""
        response = await client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, client: AsyncClient):
        """Response should have X-Frame-Options header."""
        response = await client.get("/health")
        # In debug mode it's SAMEORIGIN, in prod it's DENY
        assert response.headers.get("x-frame-options") in ["DENY", "SAMEORIGIN"]

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, client: AsyncClient):
        """Response should have X-XSS-Protection header."""
        response = await client.get("/health")
        assert "1" in response.headers.get("x-xss-protection", "")

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client: AsyncClient):
        """Response should have Referrer-Policy header."""
        response = await client.get("/health")
        assert response.headers.get("referrer-policy") is not None

    @pytest.mark.asyncio
    async def test_content_security_policy(self, client: AsyncClient):
        """Response should have Content-Security-Policy header."""
        response = await client.get("/health")
        csp = response.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src" in csp

    @pytest.mark.asyncio
    async def test_permissions_policy(self, client: AsyncClient):
        """Response should have Permissions-Policy header."""
        response = await client.get("/health")
        assert response.headers.get("permissions-policy") is not None


class TestCORS:
    """Tests for CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_preflight(self, client: AsyncClient):
        """OPTIONS request should return CORS headers."""
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not fail
        assert response.status_code in [200, 204]
