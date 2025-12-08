from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from services.common.config.base_settings import resolve_env
from services.orchestrator.app.main import build_app

# Use a test database URL (would be configured in env)
TEST_DATABASE_URL = resolve_env(
    "TEST_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test_db"
)
SYNC_TEST_DATABASE_URL = resolve_env(
    "SYNC_TEST_DATABASE_URL", "postgresql://user:password@localhost:5432/test_db"
)


@pytest.fixture
def api_client():
    app = build_app()
    client = TestClient(app)
    return client, app


@pytest.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture for async database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sync_db_session() -> Generator[Session, None, None]:
    """Fixture for sync database session"""
    engine = create_engine(SYNC_TEST_DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
