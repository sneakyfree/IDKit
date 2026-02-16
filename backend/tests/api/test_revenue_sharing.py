"""
Tests for Revenue Sharing API

Agreements, distributions, and payments for FEAT-076.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime


def _mock_agreement(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "partner_id": str(uuid4()),
        "name": "50/50 Split",
        "split_percentage": 50.0,
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_distribution(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "amount_cents": 50000,
        "owner_share_cents": 25000,
        "partner_share_cents": 25000,
        "status": "pending",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestAgreementList:
    """Tests for GET /api/v1/revenue-sharing."""

    @pytest.mark.asyncio
    async def test_list_agreements(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_agreements = AsyncMock(return_value=[_mock_agreement()])
            response = await async_client.get(
                "/api/v1/revenue-sharing", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "agreements" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/revenue-sharing")
        assert response.status_code == 401


class TestAgreementCreate:
    """Tests for POST /api/v1/revenue-sharing."""

    @pytest.mark.asyncio
    async def test_create_agreement(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_agreement = AsyncMock(return_value=_mock_agreement())
            response = await async_client.post(
                "/api/v1/revenue-sharing",
                json={
                    "partner_id": str(uuid4()),
                    "name": "New Split",
                    "split_percentage": 30.0,
                },
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_invalid_split(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/revenue-sharing",
            json={
                "partner_id": str(uuid4()),
                "name": "",
                "split_percentage": 150.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestAgreementCRUD:
    """Tests for GET/PATCH /api/v1/revenue-sharing/{id}."""

    @pytest.mark.asyncio
    async def test_get_agreement_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/revenue-sharing/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.update_status = AsyncMock(return_value=None)
            response = await async_client.patch(
                f"/api/v1/revenue-sharing/{uuid4()}/status",
                json={"status": "paused"},
                headers=auth_headers,
            )
        assert response.status_code == 404


class TestRevenueDistribution:
    """Tests for revenue recording and payment."""

    @pytest.mark.asyncio
    async def test_record_revenue(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        aid = uuid4()
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.record_revenue = AsyncMock(return_value=_mock_distribution())
            response = await async_client.post(
                f"/api/v1/revenue-sharing/{aid}/revenue",
                json={
                    "amount_cents": 100000,
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-01-31T23:59:59",
                },
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_record_revenue_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        aid = uuid4()
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.record_revenue = AsyncMock(return_value=None)
            response = await async_client.post(
                f"/api/v1/revenue-sharing/{aid}/revenue",
                json={
                    "amount_cents": 100000,
                    "period_start": "2024-01-01T00:00:00",
                    "period_end": "2024-01-31T23:59:59",
                },
                headers=auth_headers,
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pay_distribution_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.revenue_sharing.RevenueSharingService") as MockSvc:
            instance = MockSvc.return_value
            instance.pay_distribution = AsyncMock(return_value=None)
            response = await async_client.post(
                f"/api/v1/revenue-sharing/distributions/{uuid4()}/pay",
                headers=auth_headers,
            )
        assert response.status_code == 404
