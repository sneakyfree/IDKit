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

# Fix for SQLite: JSONB and ARRAY are PostgreSQL-specific, SQLite uses JSON
# We patch SQLiteTypeCompiler to handle these by rendering as JSON
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

def visit_JSONB(self, type_, **kw):
    """Render JSONB as JSON for SQLite compatibility."""
    return self.visit_JSON(type_, **kw)

def visit_ARRAY(self, type_, **kw):
    """Render ARRAY as JSON for SQLite compatibility."""
    return 'JSON'  # Store arrays as JSON strings in SQLite

# Only add if not already present
if not hasattr(SQLiteTypeCompiler, 'visit_JSONB'):
    SQLiteTypeCompiler.visit_JSONB = visit_JSONB
if not hasattr(SQLiteTypeCompiler, 'visit_ARRAY'):
    SQLiteTypeCompiler.visit_ARRAY = visit_ARRAY


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
    """Create a test FastAPI application with mocked dependencies."""
    test_app = create_app()

    # Override the database dependency from ALL possible import paths
    async def override_get_db():
        yield db_session

    # Import all possible get_db functions and override them
    from app.models.database import get_db as get_db_models
    from app.api.v1.deps import get_db as get_db_deps
    
    # Try to import from app.dependencies if it exists
    try:
        from app.dependencies import get_db as get_db_app
        test_app.dependency_overrides[get_db_app] = override_get_db
    except ImportError:
        pass
    
    test_app.dependency_overrides[get_db_models] = override_get_db
    test_app.dependency_overrides[get_db_deps] = override_get_db

    return test_app


# =============================================================================
# Mock User for Authentication Tests
# =============================================================================

class MockUser:
    """Mock user object for testing authenticated endpoints."""
    
    def __init__(self, user_id: str):
        from uuid import UUID
        self.id = UUID(user_id)
        self.email = "test@example.com"
        self.full_name = "Test User"
        self.oauth_provider = "google"
        self.oauth_provider_id = "google_test_123"
        self.is_active = True
        self.is_verified = True
        self.subscription_tier = "pro"
        self.avatar_url = None
        self.last_login_at = None
        self.created_at = None
        self.updated_at = None
        # Mock relationships as None to avoid SQLAlchemy issues
        self.profile = None
        self.connect_account = None
        self.scheduled_posts = []


@pytest.fixture(scope="function")
def authenticated_app(db_session: AsyncSession) -> tuple[FastAPI, str]:
    """
    Create a test FastAPI application with authentication mocked.
    Returns (app, user_id) tuple.
    """
    test_app = create_app()
    test_user_id = str(uuid4())

    # Override the database dependency
    async def override_get_db():
        yield db_session

    # Mock get_current_user to return our mock user
    async def override_get_current_user():
        return MockUser(test_user_id)

    # Import all dependencies and override them
    from app.models.database import get_db as get_db_models
    from app.api.v1.deps import get_db as get_db_deps, get_current_user as get_current_user_deps
    
    try:
        from app.dependencies import get_db as get_db_app, get_current_user as get_current_user_app
        test_app.dependency_overrides[get_db_app] = override_get_db
        test_app.dependency_overrides[get_current_user_app] = override_get_current_user
    except ImportError:
        pass
    
    test_app.dependency_overrides[get_db_models] = override_get_db
    test_app.dependency_overrides[get_db_deps] = override_get_db
    test_app.dependency_overrides[get_current_user_deps] = override_get_current_user

    return test_app, test_user_id


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client (unauthenticated)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def unauthenticated_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an unauthenticated test client for testing 401 responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a test user in the database using raw SQL to avoid relationship issues."""
    from sqlalchemy import text
    from datetime import datetime
    
    user_id = uuid4()
    now = datetime.utcnow()
    
    # For SQLite, UUID column stores as blob/bytes, use .bytes for proper serialization
    await db_session.execute(
        text("""
            INSERT INTO users (id, email, oauth_provider, oauth_provider_id, 
                             full_name, is_active, is_verified, subscription_tier,
                             created_at, updated_at)
            VALUES (:id, :email, :oauth_provider, :oauth_provider_id,
                   :full_name, :is_active, :is_verified, :subscription_tier,
                   :created_at, :updated_at)
        """),
        {
            "id": user_id.bytes,  # Store as bytes for SQLAlchemy UUID compatibility
            "email": "test@example.com",
            "oauth_provider": "google",
            "oauth_provider_id": "google_test_123",
            "full_name": "Test User",
            "is_active": True,
            "is_verified": True,
            "subscription_tier": "pro",
            "created_at": now,
            "updated_at": now,
        }
    )
    await db_session.commit()
    
    return {
        "id": str(user_id),
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "pro",
    }


@pytest.fixture
def mock_user_data() -> dict:
    """Generate mock user data for testing (without DB insertion)."""
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
    from app.api.v1.auth import create_access_token
    from uuid import UUID

    token = create_access_token(user_id=UUID(mock_user_data["id"]))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(
    app: FastAPI,
    test_user: dict,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test client with user in DB."""
    from app.api.v1.auth import create_access_token
    from uuid import UUID

    token = create_access_token(user_id=UUID(test_user["id"]))
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac


# Fixture aliases for compatibility with different test naming conventions
# IMPORTANT: async_client uses authenticated_app with mocked get_current_user
@pytest_asyncio.fixture(scope="function")
async def async_client(
    authenticated_app: tuple[FastAPI, str],
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with mocked authentication."""
    app, user_id = authenticated_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(authenticated_app: tuple[FastAPI, str]) -> dict:
    """Generate auth headers (token not validated since get_current_user is mocked)."""
    from app.api.v1.auth import create_access_token
    from uuid import UUID
    
    app, user_id = authenticated_app
    token = create_access_token(user_id=UUID(user_id))
    return {"Authorization": f"Bearer {token}"}


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
