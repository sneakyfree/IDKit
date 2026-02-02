"""
Tests for ROI Calculator API

Tests for ROI calculation, cost management, and projections endpoints.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestROICalculation:
    """Tests for ROI calculation endpoint."""

    @pytest.mark.asyncio
    async def test_calculate_roi_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test successful ROI calculation."""
        today = date.today()
        start = today - timedelta(days=30)

        response = await unauthenticated_client.post(
            "/api/v1/roi/calculate",
            json={
                "start_date": start.isoformat(),
                "end_date": today.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "revenue" in data
        assert "costs" in data
        assert "metrics" in data

        # Verify revenue breakdown structure
        assert "brand_deals" in data["revenue"]
        assert "affiliate" in data["revenue"]
        assert "subscriptions" in data["revenue"]
        assert "royalties" in data["revenue"]
        assert "total" in data["revenue"]

        # Verify metrics structure
        assert "net_profit_cents" in data["metrics"]
        assert "roi_percentage" in data["metrics"]
        assert "profit_margin" in data["metrics"]

    @pytest.mark.asyncio
    async def test_calculate_roi_invalid_dates(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test ROI calculation with end date before start date."""
        today = date.today()

        response = await unauthenticated_client.post(
            "/api/v1/roi/calculate",
            json={
                "start_date": today.isoformat(),
                "end_date": (today - timedelta(days=30)).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "end date" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_calculate_roi_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test ROI calculation without authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/roi/calculate",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

        assert response.status_code == 401


class TestROISummary:
    """Tests for ROI summary endpoint."""

    @pytest.mark.asyncio
    async def test_get_summary_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting ROI summary."""
        response = await async_client.get(
            "/api/v1/roi/summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "current_period" in data
        assert "revenue_change_percent" in data
        assert "profit_change_percent" in data
        assert "roi_change_percent" in data


class TestROIHistory:
    """Tests for ROI history endpoint."""

    @pytest.mark.asyncio
    async def test_get_history_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting ROI history."""
        response = await async_client.get(
            "/api/v1/roi/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_history_with_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting ROI history with custom limit."""
        response = await async_client.get(
            "/api/v1/roi/history?limit=6",
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestROIProjections:
    """Tests for ROI projections endpoint."""

    @pytest.mark.asyncio
    async def test_get_projections_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting ROI projections."""
        response = await async_client.get(
            "/api/v1/roi/projections",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "projections" in data
        assert "average_monthly_revenue" in data
        assert "average_monthly_costs" in data
        assert "trend" in data
        assert "confidence_score" in data


class TestCostEntries:
    """Tests for cost entry management."""

    @pytest.mark.asyncio
    async def test_add_cost_entry_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test adding a cost entry."""
        response = await unauthenticated_client.post(
            "/api/v1/roi/costs",
            json={
                "amount_cents": 9999,
                "category": "software",
                "expense_date": date.today().isoformat(),
                "description": "Adobe subscription",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["amount_cents"] == 9999
        assert data["category"] == "software"
        assert data["description"] == "Adobe subscription"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_add_cost_entry_invalid_amount(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test adding cost entry with invalid amount."""
        response = await unauthenticated_client.post(
            "/api/v1/roi/costs",
            json={
                "amount_cents": -100,
                "category": "software",
                "expense_date": date.today().isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_cost_entries_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting cost entries."""
        response = await async_client.get(
            "/api/v1/roi/costs",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "entries" in data
        assert "total_cents" in data
        assert "by_category" in data
        assert isinstance(data["entries"], list)

    @pytest.mark.asyncio
    async def test_get_cost_entries_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting cost entries with filters."""
        today = date.today()
        response = await unauthenticated_client.get(
            f"/api/v1/roi/costs?start_date={today.isoformat()}&category=software",
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_cost_entry_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting a cost entry."""
        # First create an entry
        create_response = await unauthenticated_client.post(
            "/api/v1/roi/costs",
            json={
                "amount_cents": 5000,
                "category": "equipment",
                "expense_date": date.today().isoformat(),
            },
            headers=auth_headers,
        )

        if create_response.status_code == 200:
            entry_id = create_response.json()["id"]

            # Delete it
            delete_response = await async_client.delete(
                f"/api/v1/roi/costs/{entry_id}",
                headers=auth_headers,
            )

            assert delete_response.status_code == 200
            assert delete_response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_delete_cost_entry_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent cost entry."""
        fake_id = str(uuid4())

        response = await async_client.delete(
            f"/api/v1/roi/costs/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
