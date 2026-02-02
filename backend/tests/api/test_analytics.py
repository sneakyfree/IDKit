"""
Tests for Analytics API

Tests for analytics export and enhanced dashboard endpoints.
"""

import pytest
from datetime import datetime, timedelta
import base64
import json

from httpx import AsyncClient


class TestAnalyticsExport:
    """Tests for analytics export endpoint."""

    @pytest.mark.asyncio
    async def test_export_csv_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test exporting analytics as CSV."""
        response = await async_client.get(
            "/api/v1/analytics/export?format=csv",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["format"] == "csv"
        assert data["filename"].endswith(".csv")
        assert "data" in data
        assert "generated_at" in data

        # Verify base64 encoded data
        decoded = base64.b64decode(data["data"])
        assert b"Analytics Export Report" in decoded

    @pytest.mark.asyncio
    async def test_export_json_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test exporting analytics as JSON."""
        response = await async_client.get(
            "/api/v1/analytics/export?format=json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["format"] == "json"
        assert data["filename"].endswith(".json")

        # Parse the nested JSON data
        export_data = json.loads(data["data"])
        assert "generated_at" in export_data
        assert "period" in export_data
        assert "overview" in export_data
        assert "platform_breakdown" in export_data

    @pytest.mark.asyncio
    async def test_export_with_date_range(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test export with custom date range."""
        end = datetime.now()
        start = end - timedelta(days=7)

        response = await async_client.get(
            f"/api/v1/analytics/export?format=json"
            f"&start_date={start.isoformat()}"
            f"&end_date={end.isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_without_timeseries(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test export without time series data."""
        response = await async_client.get(
            "/api/v1/analytics/export?format=json&include_timeseries=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        export_data = json.loads(data["data"])

        assert export_data["timeseries"] == []

    @pytest.mark.asyncio
    async def test_export_invalid_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test export with invalid format."""
        response = await async_client.get(
            "/api/v1/analytics/export?format=xml",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_export_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test export without authentication."""
        response = await unauthenticated_client.get(
            "/api/v1/analytics/export?format=csv",
        )

        assert response.status_code == 401


class TestAnalyticsOverview:
    """Tests for analytics overview endpoint."""

    @pytest.mark.asyncio
    async def test_overview_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting analytics overview."""
        response = await async_client.get(
            "/api/v1/analytics/overview",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_impressions" in data
        assert "total_engagement" in data
        assert "total_followers" in data
        assert "average_engagement_rate" in data
        assert "platform_breakdown" in data

    @pytest.mark.asyncio
    async def test_overview_with_date_range(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test overview with custom date range."""
        end = datetime.now()
        start = end - timedelta(days=90)

        response = await async_client.get(
            f"/api/v1/analytics/overview"
            f"?start_date={start.isoformat()}"
            f"&end_date={end.isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestAnalyticsTrends:
    """Tests for analytics trends endpoint."""

    @pytest.mark.asyncio
    async def test_trends_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting analytics trends."""
        response = await async_client.get(
            "/api/v1/analytics/trends",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            trend = data[0]
            assert "metric" in trend
            assert "current_value" in trend
            assert "previous_value" in trend
            assert "change_percent" in trend
            assert "trend_direction" in trend

    @pytest.mark.asyncio
    async def test_trends_custom_period(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test trends with custom comparison period."""
        response = await async_client.get(
            "/api/v1/analytics/trends?period_days=7",
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestAnalyticsTimeSeries:
    """Tests for analytics time series endpoint."""

    @pytest.mark.asyncio
    async def test_timeseries_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting time series data."""
        response = await async_client.get(
            "/api/v1/analytics/timeseries?metric=engagement",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_timeseries_invalid_metric(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test time series with invalid metric."""
        response = await async_client.get(
            "/api/v1/analytics/timeseries?metric=invalid",
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_timeseries_granularity(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test time series with different granularities."""
        for granularity in ["day", "week", "month"]:
            response = await async_client.get(
                f"/api/v1/analytics/timeseries?metric=impressions&granularity={granularity}",
                headers=auth_headers,
            )

            assert response.status_code == 200
