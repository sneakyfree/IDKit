"""
Tests for Developer API Keys API

CRUD + secret handling for FEAT-083.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4


def _mock_api_key(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "My API Key",
        "scopes": ["read", "write"],
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestApiKeyList:
    """Tests for GET /api/v1/api-keys."""

    @pytest.mark.asyncio
    async def test_list_keys_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.developer_keys.ApiKeyService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_keys = AsyncMock(return_value=[_mock_api_key()])
            response = await async_client.get(
                "/api/v1/api-keys", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_keys_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/api-keys")
        assert response.status_code == 401


class TestApiKeyCreate:
    """Tests for POST /api/v1/api-keys."""

    @pytest.mark.asyncio
    async def test_create_key_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.developer_keys.ApiKeyService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_key = AsyncMock(
                return_value=(_mock_api_key(), "sk_test_secret_123")
            )
            response = await async_client.post(
                "/api/v1/api-keys",
                json={"name": "Test Key", "scopes": ["read"]},
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert "key" in data
        assert "secret" in data
        assert data["secret"] == "sk_test_secret_123"
        assert "warning" in data

    @pytest.mark.asyncio
    async def test_create_key_invalid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/api-keys",
            json={"name": "", "scopes": []},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestApiKeyRevoke:
    """Tests for DELETE /api/v1/api-keys/{id}."""

    @pytest.mark.asyncio
    async def test_revoke_key_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.developer_keys.ApiKeyService") as MockSvc:
            instance = MockSvc.return_value
            instance.revoke_key = AsyncMock(return_value=False)
            response = await async_client.delete(
                f"/api/v1/api-keys/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404
