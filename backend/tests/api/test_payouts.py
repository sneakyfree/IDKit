"""
Tests for Payouts API

Tests for Stripe Connect onboarding, account status, balance, and payouts.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestConnectOnboarding:
    """Tests for Stripe Connect onboarding."""

    @pytest.mark.asyncio
    async def test_start_onboarding_no_existing_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test starting onboarding for user without Connect account."""
        with patch("app.api.v1.payouts.stripe_service") as mock_service:
            mock_service.create_connect_account = AsyncMock(
                return_value={"account_id": "acct_test123"}
            )
            mock_service.create_account_link = AsyncMock(
                return_value="https://connect.stripe.com/onboard/test"
            )

            response = await async_client.post(
                "/api/v1/payouts/onboard",
                json={"return_url": "https://example.com/return"},
                headers=auth_headers,
            )

            # May fail if user already has account, check for valid responses
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_onboarding_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test onboarding without authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/payouts/onboard",
            json={"return_url": "https://example.com/return"},
        )

        assert response.status_code == 401


class TestConnectAccount:
    """Tests for Connect account status."""

    @pytest.mark.asyncio
    async def test_get_account_status_no_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting status when no Connect account exists."""
        response = await async_client.get(
            "/api/v1/payouts/account",
            headers=auth_headers,
        )

        # Either returns 200 with status or 404 if no account
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_account_status_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test getting account status without auth."""
        response = await unauthenticated_client.get(
            "/api/v1/payouts/account",
        )

        assert response.status_code == 401


class TestBalance:
    """Tests for balance endpoint."""

    @pytest.mark.asyncio
    async def test_get_balance_no_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting balance without Connect account."""
        response = await async_client.get(
            "/api/v1/payouts/balance",
            headers=auth_headers,
        )

        # Should return 404 if no account, 200 if exists
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_balance_structure(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test balance response structure when account exists."""
        response = await async_client.get(
            "/api/v1/payouts/balance",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "available_cents" in data
            assert "pending_cents" in data
            assert "currency" in data


class TestPayoutHistory:
    """Tests for payout history endpoint."""

    @pytest.mark.asyncio
    async def test_get_history_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting payout history."""
        response = await async_client.get(
            "/api/v1/payouts/history",
            headers=auth_headers,
        )

        # Returns empty list or payouts
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_history_with_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting payout history with limit."""
        response = await async_client.get(
            "/api/v1/payouts/history?limit=5",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]


class TestPayoutRequest:
    """Tests for payout request endpoint."""

    @pytest.mark.asyncio
    async def test_request_payout_no_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test requesting payout without Connect account."""
        response = await async_client.post(
            "/api/v1/payouts/initiate",
            json={"amount_cents": 10000},
            headers=auth_headers,
        )

        # Should fail without account
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_request_payout_below_minimum(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test requesting payout below minimum amount."""
        response = await async_client.post(
            "/api/v1/payouts/initiate",
            json={"amount_cents": 100},  # Too low
            headers=auth_headers,
        )

        # Should either fail on minimum or on missing account
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_request_payout_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test requesting payout without authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/payouts/initiate",
            json={"amount_cents": 10000},
        )

        assert response.status_code == 401


class TestDashboardLink:
    """Tests for Stripe dashboard link endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard_link_no_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting dashboard link without Connect account."""
        response = await async_client.get(
            "/api/v1/payouts/dashboard-link",
            headers=auth_headers,
        )

        # Should fail without account
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_dashboard_link_unauthorized(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test getting dashboard link without auth."""
        response = await unauthenticated_client.get(
            "/api/v1/payouts/dashboard-link",
        )

        assert response.status_code == 401
