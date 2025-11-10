"""Asynchronous database utilities for the Orchestrator service.

We use **SQLModel** (which builds on SQLAlchemy) together with the ``asyncpg``
driver for PostgreSQL.  The helper ``get_async_session`` yields an ``AsyncSession``
that automatically commits on success and rolls back on error – this mirrors the
pattern used by FastAPI examples.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel, create_engine
import logging

logger = logging.getLogger(__name__)

# ``sqlmodel`` does not expose ``async_sessionmaker`` directly. Use the
# implementation from SQLAlchemy's async extension. ``create_async_engine``
# creates an ``AsyncEngine`` compatible with ``async_sessionmaker``.
# SQLModel provides its own ``AsyncSession`` implementation that includes the
# ``exec`` helper used throughout the repository layer. Importing the generic
# ``AsyncSession`` from SQLAlchemy (as was previously done) lacks this method,
# causing an ``AttributeError`` at runtime. We therefore import the async
# session class from ``sqlmodel.ext.asyncio.session`` while keeping the
# ``async_sessionmaker`` and ``create_async_engine`` utilities from SQLAlchemy.
from sqlmodel.ext.asyncio.session import AsyncSession

# Adjusted import path: models are in `repository/outbox.py` not `models/outbox`.
from .repository.outbox import OutboxEvent
from .services.circuit_breaker import DATABASE_CIRCUIT_BREAKER

# ---------------------------------------------------------------------------
# Configuration – read from environment with production defaults.
# ---------------------------------------------------------------------------
from .core.config import get_settings

settings = get_settings()
DATABASE_URL: str = settings.database_url

# Synchronous engine for metadata creation – use the regular SQLite driver.
sync_engine = create_engine("sqlite:///:memory:", echo=False, future=True)

# Async engine for runtime operations with production pooling
_db_url = DATABASE_URL
if not _db_url.startswith("postgresql+asyncpg://"):
    raise RuntimeError(
        "DATABASE_URL must use asyncpg driver (postgresql+asyncpg://). Got: " + _db_url
    )

async_engine = create_async_engine(
    _db_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# Alias for backward compatibility
def get_session_factory():
    """Return the async session factory for service initialization."""
    return AsyncSessionLocal


async def init_db() -> None:
    """Initialize the database schema including outbox table."""
    # Create all tables including OutboxEvent
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info(f"Database schema initialized with URL: {DATABASE_URL}")


async def check_database_health() -> bool:
    """Check database connectivity for health checks with circuit breaker."""

    @DATABASE_CIRCUIT_BREAKER
    async def _check_db() -> bool:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
            return True

    try:
        return await _check_db()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


@asynccontextmanager
async def get_async_session() -> AsyncSession:
    """Yield an async session; commit on success, rollback on exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# FastAPI dependency injection helper
async def get_session() -> AsyncSession:
    """FastAPI dependency for getting database session."""
    async with get_async_session() as session:
        yield session
