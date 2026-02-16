"""
Tests for Sponsorship Management API

CRUD + deliverables + analytics for FEAT-052.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime


def _mock_sponsorship(overrides: dict | None = None):
    """Create a mock sponsorship object."""
    s = MagicMock()
    base = {
        "id": str(uuid4()),
        "brand_name": "TestBrand",
        "status": "active",
        "value_cents": 100000,
        "currency": "usd",
        "start_date": None,
        "end_date": None,
        "notes": None,
        "created_at": datetime.now().isoformat(),
        "deliverables": [],
        "user_id": None,
    }
    base.update(overrides or {})
    s.to_dict.return_value = base
    s.user_id = base.get("user_id")
    return s


class TestSponsorshipList:
    """Tests for GET /api/v1/sponsorships."""

    @pytest.mark.asyncio
    async def test_list_sponsorships_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.sponsorships.SponsorshipService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_sponsorships = AsyncMock(return_value=[_mock_sponsorship()])
            response = await async_client.get(
                "/api/v1/sponsorships", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "sponsorships" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_sponsorships_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/sponsorships")
        assert response.status_code == 401


class TestSponsorshipCreate:
    """Tests for POST /api/v1/sponsorships."""

    @pytest.mark.asyncio
    async def test_create_sponsorship_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.sponsorships.SponsorshipService") as MockSvc:
            instance = MockSvc.return_value
            instance.create = AsyncMock(return_value=_mock_sponsorship())
            response = await async_client.post(
                "/api/v1/sponsorships",
                json={"brand_name": "NewBrand", "value_cents": 50000},
                headers=auth_headers,
            )
        assert response.status_code == 201
        assert response.json()["brand_name"] == "TestBrand"

    @pytest.mark.asyncio
    async def test_create_sponsorship_invalid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/sponsorships",
            json={"brand_name": "", "value_cents": -1},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestSponsorshipCRUD:
    """Tests for GET/PATCH/DELETE /api/v1/sponsorships/{id}."""

    @pytest.mark.asyncio
    async def test_get_sponsorship_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.sponsorships.SponsorshipService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/sponsorships/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_sponsorship_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.sponsorships.SponsorshipService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.delete(
                f"/api/v1/sponsorships/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestSponsorshipAnalytics:
    """Tests for GET /api/v1/sponsorships/analytics/summary."""

    @pytest.mark.asyncio
    async def test_analytics_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.sponsorships.SponsorshipService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_analytics = AsyncMock(
                return_value={"total_value": 500000, "active_count": 3}
            )
            response = await async_client.get(
                "/api/v1/sponsorships/analytics/summary", headers=auth_headers
            )
        assert response.status_code == 200
