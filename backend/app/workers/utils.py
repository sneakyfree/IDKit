"""
Celery Worker Utilities

Helper functions for running async code in Celery tasks.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Create async engine for worker processes
_worker_engine = None
_worker_session_factory = None


def get_worker_engine():
    """Get or create async engine for worker processes."""
    global _worker_engine
    if _worker_engine is None:
        _worker_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _worker_engine


def get_worker_session_factory():
    """Get or create session factory for worker processes."""
    global _worker_session_factory
    if _worker_session_factory is None:
        engine = get_worker_engine()
        _worker_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _worker_session_factory


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions in Celery tasks.

    Usage:
        async with get_async_db() as db:
            result = await db.execute(...)
    """
    session_factory = get_worker_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def run_async(coro):
    """
    Run an async coroutine in a sync context.

    Handles event loop creation for Celery tasks.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def cleanup_worker_connections():
    """Cleanup database connections when worker shuts down."""
    global _worker_engine
    if _worker_engine is not None:
        await _worker_engine.dispose()
        _worker_engine = None
