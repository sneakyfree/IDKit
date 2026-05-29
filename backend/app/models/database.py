"""
Database Connection Management

Provides async SQLAlchemy engine and session factory.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# --- Dev-only: SQLite compile shims for postgres-specific types -----------------
# Allows init_db() to create tables on sqlite (preview / tests) without needing PG.
try:
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PGUUID, INET, CIDR
    @compiles(JSONB, "sqlite")
    def _sqlite_jsonb(element, compiler, **kw):
        return "JSON"
    @compiles(ARRAY, "sqlite")
    def _sqlite_array(element, compiler, **kw):
        return "JSON"
    @compiles(PGUUID, "sqlite")
    def _sqlite_uuid(element, compiler, **kw):
        return "VARCHAR(36)"
    @compiles(INET, "sqlite")
    def _sqlite_inet(element, compiler, **kw):
        return "VARCHAR(45)"
    @compiles(CIDR, "sqlite")
    def _sqlite_cidr(element, compiler, **kw):
        return "VARCHAR(45)"
except Exception:
    pass
# --------------------------------------------------------------------------------


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set True only for local SQL debugging
    pool_pre_ping=True,  # Check connection health
    pool_size=10,
    max_overflow=20,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Note: In production, use Alembic migrations instead.
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
