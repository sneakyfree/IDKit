"""
Tests for Contract Management API

CRUD + templates + signing for FEAT-058/078.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime


def _mock_contract(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "title": "Brand Deal Contract",
        "brand_name": "TestBrand",
        "status": "draft",
        "value_cents": 200000,
        "terms_text": "Standard terms",
        "expires_at": None,
        "created_at": datetime.now().isoformat(),
        "user_id": None,
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    obj.user_id = base.get("user_id")
    return obj


def _mock_template(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Standard Template",
        "content_template": "Template content {{brand}}",
        "category": "general",
        "description": None,
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestContractList:
    """Tests for GET /api/v1/contracts."""

    @pytest.mark.asyncio
    async def test_list_contracts_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_contracts = AsyncMock(return_value=[_mock_contract()])
            response = await async_client.get(
                "/api/v1/contracts", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "contracts" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_contracts_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/contracts")
        assert response.status_code == 401


class TestContractCreate:
    """Tests for POST /api/v1/contracts."""

    @pytest.mark.asyncio
    async def test_create_contract_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.create = AsyncMock(return_value=_mock_contract())
            response = await async_client.post(
                "/api/v1/contracts",
                json={"title": "New Deal", "brand_name": "BrandX"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_contract_invalid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/contracts",
            json={"title": "", "brand_name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestContractCRUD:
    """Tests for GET/PATCH/DELETE /api/v1/contracts/{id}."""

    @pytest.mark.asyncio
    async def test_get_contract_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/contracts/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contract_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.delete(
                f"/api/v1/contracts/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestContractTemplates:
    """Tests for template endpoints."""

    @pytest.mark.asyncio
    async def test_list_templates_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_templates = AsyncMock(return_value=[_mock_template()])
            response = await async_client.get(
                "/api/v1/contracts/templates/list", headers=auth_headers
            )
        assert response.status_code == 200
        assert "templates" in response.json()

    @pytest.mark.asyncio
    async def test_create_template_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.contracts.ContractService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_template = AsyncMock(return_value=_mock_template())
            response = await async_client.post(
                "/api/v1/contracts/templates",
                json={
                    "name": "New Tmpl",
                    "content_template": "Hello {{name}}",
                },
                headers=auth_headers,
            )
        assert response.status_code == 201
