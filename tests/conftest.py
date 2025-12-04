import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import httpx

# Use a test database URL (would be configured in env)
# Default to the docker-compose mapped port 10004
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://somaagent:somaagent@localhost:10004/somaagent")
SYNC_TEST_DATABASE_URL = os.environ.get("SYNC_TEST_DATABASE_URL", "postgresql://somaagent:somaagent@localhost:10004/somaagent")

@pytest_asyncio.fixture
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

@pytest_asyncio.fixture
async def async_client(async_db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture for async HTTP client with DB session override"""
    from services.orchestrator.app.main import build_app
    from services.orchestrator.app.database import get_async_session
    import httpx

    app = build_app()
    
    # Override the database session dependency
    async def override_get_async_session():
        yield async_db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
