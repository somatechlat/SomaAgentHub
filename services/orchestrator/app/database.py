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
from sqlmodel.ext.asyncio.session import AsyncSession, async_sessionmaker

# ---------------------------------------------------------------------------
# Configuration – read from environment (or default to a local dev DB).
# ---------------------------------------------------------------------------
POSTGRES_URL: str = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/soma_orchestrator",
)

# Create a *synchronous* engine for ``metadata.create_all`` – SQLModel creates the
# tables using a sync connection, then we use the async engine for runtime.
sync_engine = create_engine(POSTGRES_URL, echo=False, future=True)

# Async engine and session factory used throughout the codebase.
async_engine = create_engine(POSTGRES_URL, echo=False, future=True, connect_args={"async": True})
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Create tables on startup if they do not exist.

    ``SQLModel.metadata.create_all`` works with a sync engine, so we open a sync
    connection, run the creation, and then close it. This function is intended to
    be called from the FastAPI ``startup`` event.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


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
