"""
Tests for Social Listening API

CRUD queries, mentions, and sentiment for FEAT-048.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime


def _mock_query(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "name": "Brand Mentions",
        "keywords": ["idkit", "creator"],
        "platforms": ["twitter", "instagram"],
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


def _mock_mention(overrides: dict | None = None):
    obj = MagicMock()
    base = {
        "id": str(uuid4()),
        "platform": "twitter",
        "author_name": "user1",
        "content": "Great product!",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "engagement": 42,
        "posted_at": datetime.now().isoformat(),
    }
    base.update(overrides or {})
    obj.to_dict.return_value = base
    return obj


class TestListeningQueries:
    """Tests for listening query CRUD."""

    @pytest.mark.asyncio
    async def test_list_queries_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_queries = AsyncMock(return_value=[_mock_query()])
            response = await async_client.get(
                "/api/v1/listening/queries", headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_create_query_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.create_query = AsyncMock(return_value=_mock_query())
            response = await async_client.post(
                "/api/v1/listening/queries",
                json={
                    "name": "Brand Tracker",
                    "keywords": ["idkit"],
                    "platforms": ["twitter"],
                },
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_query_invalid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        response = await async_client.post(
            "/api/v1/listening/queries",
            json={"name": "", "keywords": [], "platforms": []},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_query_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_query = AsyncMock(return_value=None)
            response = await async_client.get(
                f"/api/v1/listening/queries/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_query_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.delete_query = AsyncMock(return_value=False)
            response = await async_client.delete(
                f"/api/v1/listening/queries/{uuid4()}", headers=auth_headers
            )
        assert response.status_code == 404


class TestMentions:
    """Tests for mention endpoints."""

    @pytest.mark.asyncio
    async def test_get_mentions_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        qid = uuid4()
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_mentions = AsyncMock(return_value=[_mock_mention()])
            response = await async_client.get(
                f"/api/v1/listening/queries/{qid}/mentions", headers=auth_headers
            )
        assert response.status_code == 200
        assert "mentions" in response.json()

    @pytest.mark.asyncio
    async def test_add_mention_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        qid = uuid4()
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.add_mention = AsyncMock(return_value=_mock_mention())
            response = await async_client.post(
                f"/api/v1/listening/queries/{qid}/mentions",
                json={
                    "platform": "twitter",
                    "author_name": "user1",
                    "content": "Great!",
                    "posted_at": datetime.now().isoformat(),
                },
                headers=auth_headers,
            )
        assert response.status_code == 201


class TestSentiment:
    """Tests for sentiment summary."""

    @pytest.mark.asyncio
    async def test_sentiment_summary(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        qid = uuid4()
        with patch("app.api.v1.social_listening.SocialListeningService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_sentiment_summary = AsyncMock(
                return_value={"positive": 60, "neutral": 30, "negative": 10}
            )
            response = await async_client.get(
                f"/api/v1/listening/queries/{qid}/sentiment", headers=auth_headers
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_queries_unauthorized(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.get("/api/v1/listening/queries")
        assert response.status_code == 401
