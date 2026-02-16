"""
Tests for authentication endpoints.

Tests:
- POST /auth/register — success, duplicate email, short password
- POST /auth/login — success, wrong password, missing user
- GET /auth/me — authenticated response
"""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Registration with valid email and password should return tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Registration with password < 8 chars should return 400."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Registering with an existing email should return 409."""
        payload = {
            "email": "dup@example.com",
            "password": "securepassword123",
        }
        # First registration
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        # Duplicate registration
        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409
        assert "already registered" in resp2.json()["detail"]


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Login after registration should return tokens."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "securepassword123",
            },
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Login with wrong password should return 401."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "securepassword123",
            },
        )

        # Wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpw@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with non-existent email should return 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 401


class TestMe:
    """Tests for GET /api/v1/auth/me."""

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """GET /me without auth should return 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient):
        """GET /me with valid token should return user info."""
        # Register
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "metest@example.com",
                "password": "securepassword123",
                "full_name": "Me Test",
            },
        )
        token = reg_response.json()["access_token"]

        # Call /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "metest@example.com"
