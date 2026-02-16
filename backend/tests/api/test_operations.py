"""
Tests for Compliance Reporting & Backup Management API

Audit, compliance checks, and backups for FEAT-106/108.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4


def _mock_report(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "type": "gdpr",
        "status": "passed",
        "score": 95,
        "created_at": "2024-01-01T00:00:00",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_backup(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "type": "full",
        "status": "completed",
        "size_bytes": 1024000,
        "created_at": "2024-01-01T00:00:00",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_check(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Data Encryption",
        "category": "security",
        "status": "passed",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_schedule(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Nightly Backup",
        "frequency": "daily",
        "backup_type": "full",
        "retention_days": 30,
        "enabled": True,
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestComplianceAudit:
    """Tests for compliance audit endpoints."""

    @pytest.mark.asyncio
    async def test_run_audit(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.ComplianceService") as MockSvc:
            instance = MockSvc.return_value
            instance.run_compliance_audit = AsyncMock(return_value=_mock_report())
            response = await async_client.post(
                "/api/v1/ops/compliance/audit",
                json={"type": "gdpr"},
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_reports(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.ComplianceService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_reports = AsyncMock(return_value=[_mock_report()])
            response = await async_client.get(
                "/api/v1/ops/compliance/reports", headers=auth_headers
            )
        assert response.status_code == 200
        assert "reports" in response.json()

    @pytest.mark.asyncio
    async def test_list_checks(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.ComplianceService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_checks = AsyncMock(return_value=[_mock_check()])
            response = await async_client.get(
                "/api/v1/ops/compliance/checks", headers=auth_headers
            )
        assert response.status_code == 200
        assert "checks" in response.json()


class TestBackups:
    """Tests for backup endpoints."""

    @pytest.mark.asyncio
    async def test_trigger_backup(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_backup = AsyncMock(return_value=_mock_backup())
            response = await async_client.post(
                "/api/v1/ops/backups",
                json={"type": "full"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_backups(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_backups = AsyncMock(return_value=[_mock_backup()])
            response = await async_client.get(
                "/api/v1/ops/backups", headers=auth_headers
            )
        assert response.status_code == 200
        assert "backups" in response.json()

    @pytest.mark.asyncio
    async def test_get_backup_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_backup = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/ops/backups/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestBackupSchedules:
    """Tests for backup schedule endpoints."""

    @pytest.mark.asyncio
    async def test_list_schedules(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_schedules = AsyncMock(return_value=[_mock_schedule()])
            response = await async_client.get(
                "/api/v1/ops/backups/schedules/list", headers=auth_headers
            )
        assert response.status_code == 200
        assert "schedules" in response.json()

    @pytest.mark.asyncio
    async def test_create_schedule(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_schedule = AsyncMock(return_value=_mock_schedule())
            response = await async_client.post(
                "/api/v1/ops/backups/schedules",
                json={
                    "name": "Nightly",
                    "frequency": "daily",
                    "backup_type": "full",
                    "retention_days": 30,
                },
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_toggle_schedule_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.operations.BackupService") as MockSvc:
            instance = MockSvc.return_value
            instance.toggle_schedule = AsyncMock(return_value=None)
            response = await async_client.post(
                f"/api/v1/ops/backups/schedules/{uuid4()}/toggle",
                headers=auth_headers,
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/ops/backups")
        assert response.status_code == 401
