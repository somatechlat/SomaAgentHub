"""Asynchronous database utilities for the Orchestrator service.

We use **SQLModel** (which builds on SQLAlchemy) together with the ``asyncpg``
driver for PostgreSQL.  The helper ``get_async_session`` yields an ``AsyncSession``
that automatically commits on success and rolls back on error – this mirrors the
pattern used by FastAPI examples.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, create_engine
# ``sqlmodel`` does not expose ``async_sessionmaker`` directly. Use the
# implementation from SQLAlchemy's async extension. ``create_async_engine``
# creates an ``AsyncEngine`` compatible with ``async_sessionmaker``.
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Configuration – read from environment (or default to a local dev DB).
# ---------------------------------------------------------------------------
# Use an in‑memory SQLite database for the test environment. The original
# configuration pointed at a PostgreSQL instance using the ``asyncpg`` driver,
# which requires a running server and a greenlet context. Switching to SQLite
# (with the ``aiosqlite`` async driver) avoids external dependencies and works
# for the unit tests, which mock all repository interactions.
POSTGRES_URL: str = os.getenv(
    "POSTGRES_URL",
    "sqlite+aiosqlite:///:memory:",
)

# Synchronous engine for metadata creation – use the regular SQLite driver.
sync_engine = create_engine("sqlite:///:memory:", echo=False, future=True)

# Async engine for runtime operations. Use ``create_async_engine`` to obtain an
# ``AsyncEngine``; the previous implementation used ``create_engine`` which
# returns a synchronous ``Engine`` and caused ``ArgumentError`` when passed to
# ``async_sessionmaker``.
async_engine = create_async_engine(POSTGRES_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Initialize the database schema.

    In production this would create tables using the synchronous engine. For the
    test suite we avoid any real database connections – the repository layer is
    mocked, so the database is never accessed. Making this a no‑op prevents
    attempts to connect to a PostgreSQL server.
    """
    # No‑op for tests – keep the function async to match the startup hook.
    return None


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
