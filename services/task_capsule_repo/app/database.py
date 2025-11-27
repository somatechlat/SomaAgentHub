"""Asynchronous database utilities for the Task Capsule Repository service.

We use **SQLModel** with the ``asyncpg`` driver for a
PostgreSQL backend. The utilities provide an async engine, session factory, and
helpers for FastAPI dependency injection. The implementation mirrors the pattern
used in other services (e.g., the orchestrator) but is scoped to the Capsule
Repository's models.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from services.common.config.settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – read from environment via the shared settings helper.
# ---------------------------------------------------------------------------
settings = get_settings()
DATABASE_URL: str = settings.database_url

# Validate the URL uses the asyncpg driver.
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise RuntimeError(
        "DATABASE_URL must use asyncpg driver (postgresql+asyncpg://). Got: "
        + DATABASE_URL
    )

# Asynchronous engine for runtime operations.
async_engine = create_async_engine(
    DATABASE_URL,
    echo=getattr(settings, "database_echo", False),
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_session_factory() -> sessionmaker:
    """Return the async session factory for service initialization."""
    return AsyncSessionLocal


async def init_db() -> None:
    """Create all tables defined by SQLModel models.

    This should be called once at application startup (via the FastAPI
    lifespan event) to ensure the database schema exists.
    """
    async with async_engine.begin() as conn:
        # Create tables from the declarative Base defined in models.py
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Task Capsule Repository DB schema initialized")


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session, committing on success and rolling back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# FastAPI dependency helper
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session for route handlers."""
    async with get_async_session() as session:
        yield session


# Backwards-compatible alias expected by tests
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alias for `get_session` used by the test harness to obtain an async DB session."""
    async with get_async_session() as session:
        yield session
