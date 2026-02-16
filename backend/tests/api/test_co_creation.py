"""
Tests for Content Co-Creation API

Projects, invitations, and messaging for FEAT-075.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4


def _mock_project(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Collab Project",
        "description": "A cool collab",
        "project_type": "content",
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_member(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "role": "member",
        "status": "accepted",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_message(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "content": "Hello team!",
        "message_type": "text",
        "sender_id": str(uuid4()),
        "created_at": "2024-01-01T00:00:00",
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestProjectCRUD:
    """Tests for project CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_projects(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_projects = AsyncMock(return_value=[_mock_project()])
            response = await async_client.get(
                "/api/v1/co-creation/projects", headers=auth_headers
            )
        assert response.status_code == 200
        assert "projects" in response.json()

    @pytest.mark.asyncio
    async def test_create_project(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.create = AsyncMock(return_value=_mock_project())
            response = await async_client.post(
                "/api/v1/co-creation/projects",
                json={"name": "New Project"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.get = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/co-creation/projects/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.delete_project = AsyncMock(return_value=False)
            response = await async_client.delete(
                f"/api/v1/co-creation/projects/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestProjectMembers:
    """Tests for invite and accept endpoints."""

    @pytest.mark.asyncio
    async def test_invite_member(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        pid = uuid4()
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.invite_member = AsyncMock(return_value=_mock_member())
            response = await async_client.post(
                f"/api/v1/co-creation/projects/{pid}/invite",
                json={"user_id": str(uuid4()), "role": "editor"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_accept_invite_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        pid = uuid4()
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.accept_invite = AsyncMock(return_value=None)
            response = await async_client.post(
                f"/api/v1/co-creation/projects/{pid}/accept", headers=auth_headers
            )
        assert response.status_code == 404


class TestProjectMessages:
    """Tests for project messaging endpoints."""

    @pytest.mark.asyncio
    async def test_send_message(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        pid = uuid4()
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.send_message = AsyncMock(return_value=_mock_message())
            response = await async_client.post(
                f"/api/v1/co-creation/projects/{pid}/messages",
                json={"content": "Hello!"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_messages(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        pid = uuid4()
        with patch("app.api.v1.co_creation.CollaborationService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_messages = AsyncMock(return_value=[_mock_message()])
            response = await async_client.get(
                f"/api/v1/co-creation/projects/{pid}/messages", headers=auth_headers
            )
        assert response.status_code == 200
        assert "messages" in response.json()

    @pytest.mark.asyncio
    async def test_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/co-creation/projects")
        assert response.status_code == 401
