"""
Tests for Tax Documentation API

Profile, W-9 submission, and document generation for FEAT-057.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from datetime import datetime


def _mock_profile(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "business_type": "sole_proprietor",
        "legal_name": "Test Creator",
        "tax_id": "***-**-1234",
        "w9_submitted": True,
        "w9_submitted_at": datetime.now().isoformat(),
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_document(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": "doc_123",
        "type": "1099-NEC",
        "year": 2024,
        "total_amount_cents": 500000,
        "status": "generated",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestTaxProfile:
    """Tests for tax profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_profile = AsyncMock(return_value=_mock_profile())
            response = await async_client.get(
                "/api/v1/tax/profile", headers=auth_headers
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_profile_not_exists(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_profile = AsyncMock(return_value=None)
            response = await async_client.get(
                "/api/v1/tax/profile", headers=auth_headers
            )
        assert response.status_code == 200
        assert response.json()["profile"] is None

    @pytest.mark.asyncio
    async def test_update_profile(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.update_profile = AsyncMock(return_value=_mock_profile())
            response = await async_client.put(
                "/api/v1/tax/profile",
                json={"business_type": "llc", "legal_name": "My LLC"},
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_w9(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        mock_p = _mock_profile()
        mock_p.w9_submitted_at = datetime.now().isoformat()
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.submit_w9 = AsyncMock(return_value=mock_p)
            response = await async_client.post(
                "/api/v1/tax/profile/w9", headers=auth_headers
            )
        assert response.status_code == 200
        assert response.json()["w9_submitted"] is True


class TestTaxDocuments:
    """Tests for tax document endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_documents = AsyncMock(return_value=[_mock_document()])
            response = await async_client.get(
                "/api/v1/tax/documents", headers=auth_headers
            )
        assert response.status_code == 200
        assert "documents" in response.json()

    @pytest.mark.asyncio
    async def test_generate_document(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.tax.TaxService") as MockSvc:
            instance = MockSvc.return_value
            instance.generate_document = AsyncMock(return_value=_mock_document())
            response = await async_client.post(
                "/api/v1/tax/documents/generate",
                json={"type": "1099-NEC", "year": 2024, "total_amount_cents": 500000},
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/tax/profile")
        assert response.status_code == 401
