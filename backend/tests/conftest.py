"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests:
- Async test client for API testing
- Database session fixtures
- Mock fixtures for external services
- User authentication fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.main import create_app
from app.models.base import Base
from app.models.database import get_db


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

# Use SQLite for testing (in-memory for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# =============================================================================
# Application Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def app(db_session: AsyncSession) -> FastAPI:
    """Create a test FastAPI application."""
    test_app = create_app()

    # Override the database dependency
    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    return test_app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def mock_user_data() -> dict:
    """Generate mock user data for testing."""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "free",
    }


@pytest.fixture
def mock_auth_headers(mock_user_data: dict) -> dict:
    """Generate mock authentication headers."""
    from app.services.auth.jwt import create_access_token

    token = create_access_token(subject=mock_user_data["id"])
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(
    app: FastAPI,
    mock_user_data: dict,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test client."""
    from app.services.auth.jwt import create_access_token

    token = create_access_token(subject=mock_user_data["id"])
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac


# =============================================================================
# Mock Service Fixtures
# =============================================================================

@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client for testing."""
    mock = mocker.MagicMock()
    mock.get = mocker.AsyncMock(return_value=None)
    mock.set = mocker.AsyncMock(return_value=True)
    mock.delete = mocker.AsyncMock(return_value=1)
    mock.exists = mocker.AsyncMock(return_value=0)
    mock.expire = mocker.AsyncMock(return_value=True)
    mock.incr = mocker.AsyncMock(return_value=1)
    mock.zadd = mocker.AsyncMock(return_value=1)
    mock.zrangebyscore = mocker.AsyncMock(return_value=[])
    mock.zremrangebyscore = mocker.AsyncMock(return_value=0)
    mock.zcard = mocker.AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_s3_client(mocker):
    """Mock S3 client for testing."""
    mock = mocker.MagicMock()
    mock.upload_fileobj = mocker.AsyncMock()
    mock.download_fileobj = mocker.AsyncMock()
    mock.generate_presigned_url = mocker.MagicMock(
        return_value="https://s3.example.com/presigned-url"
    )
    mock.delete_object = mocker.AsyncMock()
    return mock


@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for testing."""
    mock = mocker.MagicMock()

    # Mock completion response
    mock_completion = mocker.MagicMock()
    mock_completion.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="Generated content")
        )
    ]
    mock.chat.completions.create = mocker.AsyncMock(return_value=mock_completion)

    return mock


# =============================================================================
# Utility Functions
# =============================================================================

def assert_response_ok(response, expected_status: int = 200):
    """Assert response status and return JSON body."""
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
    )
    return response.json()


def assert_validation_error(response, field: str = None):
    """Assert response is a validation error."""
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    if field:
        assert any(
            field in str(err.get("loc", []))
            for err in body["detail"]
        )
    return body
