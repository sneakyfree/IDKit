"""
Tests for Custom Reporting API

CRUD + scheduling + generation for FEAT-067.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4


def _mock_report(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Monthly Performance",
        "description": "Monthly perf report",
        "metrics": ["followers", "engagement"],
        "platforms": ["instagram", "tiktok"],
        "export_format": "pdf",
        "status": "ready",
        "user_id": None,
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    obj.user_id = base.get("user_id")
    return obj


class TestReportList:
    """Tests for GET /api/v1/reports."""

    @pytest.mark.asyncio
    async def test_list_reports_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_reports = AsyncMock(return_value=[_mock_report()])
            response = await async_client.get(
                "/api/v1/reports", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_reports_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/reports")
        assert response.status_code == 401


class TestReportCreate:
    """Tests for POST /api/v1/reports."""

    @pytest.mark.asyncio
    async def test_create_report_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.create = AsyncMock(return_value=_mock_report())
            response = await async_client.post(
                "/api/v1/reports",
                json={
                    "name": "Weekly Stats",
                    "metrics": ["followers"],
                    "platforms": ["instagram"],
                },
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_report_invalid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/reports",
            json={"name": "", "metrics": [], "platforms": []},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestReportCRUD:
    """Tests for GET/DELETE /api/v1/reports/{id}."""

    @pytest.mark.asyncio
    async def test_get_report_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/reports/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_report_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.delete = AsyncMock(return_value=False)
            response = await async_client.delete(
                f"/api/v1/reports/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestReportSchedule:
    """Tests for report scheduling and generation."""

    @pytest.mark.asyncio
    async def test_generate_report(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        rid = uuid4()
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.generate_report = AsyncMock(return_value=_mock_report())
            response = await async_client.post(
                f"/api/v1/reports/{rid}/generate", headers=auth_headers
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_schedule_report(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        rid = uuid4()
        with patch("app.api.v1.reports.ReportingService") as MockSvc:
            instance = MockSvc.return_value
            instance.schedule_report = AsyncMock(return_value=_mock_report())
            response = await async_client.post(
                f"/api/v1/reports/{rid}/schedule",
                json={"frequency": "weekly", "day": "monday", "time": "09:00"},
                headers=auth_headers,
            )
        assert response.status_code == 200
