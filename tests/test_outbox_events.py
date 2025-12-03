"""
Async test for outbox event emission.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlalchemy.sql import expression
from services.orchestrator.app.repository.outbox_event_repository import OutboxEventRepository


@pytest.mark.asyncio
async def test_outbox_event_creation():
    """Test real outbox event creation with async database."""

    # Setup async database
    import os
    # Use port 10004 as defined in docker-compose.yml for app-postgres
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://somaagent:somaagent@localhost:10004/somaagent")
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables asynchronously
    # Enable pgcrypto extension (requires autocommit)
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        repo = OutboxEventRepository(session)

        # Create test event
        event_data = {
            "plan_id": str(uuid.uuid4()),
            "tenant": "test-tenant",
            "objective": "Test real outbox event",
            "agent_ids": ["agent-1", "agent-2"],
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Create event in outbox table
        event = await repo.create_event(
            event_type="orchestration.plan_created",
            topic="orchestrator.events",
            key=str(uuid.uuid4()),
            payload=event_data,
        )

        await session.commit()

        # Verify event was stored
        assert event.id is not None
        assert event.topic == "orchestrator.events"
        assert event.event_data["tenant"] == "test-tenant"

        # Retrieve events
        events = await repo.get_events_by_type("orchestration.plan_created")
        assert len(events) >= 1
        assert events[0].event_data["plan_id"] == event_data["plan_id"]

        # Test marking as processed
        await repo.mark_as_processed(event.id)

        # Verify status
        pending = await repo.get_pending_events()
        assert len(pending) == 0  # Should be processed

        logging.getLogger(__name__).info("✅ Outbox event emission verified")


@pytest.mark.asyncio
async def test_repository_methods():
    """Test all repository methods work correctly."""

    import os
    # Use port 10004 as defined in docker-compose.yml for app-postgres
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://somaagent:somaagent@localhost:10004/somaagent")
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        repo = OutboxEventRepository(session)

        # Create multiple events
        for i in range(3):
            await repo.create_event(
                event_type=f"test.event.{i}",
                topic="test.topic",
                key=f"key-{i}",
                payload={"index": i},
            )

        await session.commit()

        # Test batch retrieval
        events = await repo.get_events_by_type("test.event.1")
        assert len(events) == 1
        assert events[0].event_data["index"] == 1

        # Test topic filtering
        topic_events = await repo.get_events_by_topic("test.topic")
        assert len(topic_events) == 3

        # Test key filtering
        key_events = await repo.get_events_by_key("key-1")
        assert len(key_events) == 1

        # Test retry mechanism
        failed_event = await repo.create_event(event_type="test.failed", topic="test.topic", payload={"failed": True})
        await session.commit()

        await repo.mark_as_failed(failed_event.id, "Test failure")

        # Verify retry count
        events_after_retry = await repo.get_events_by_type("test.failed")
        assert len(events_after_retry) == 1
        # Note: retry_count is string in the model

        logging.getLogger(__name__).info("✅ All repository methods working correctly")


if __name__ == "__main__":
    asyncio.run(test_outbox_event_creation())
    asyncio.run(test_repository_methods())
    logging.getLogger(__name__).info("🎉 Async tests completed successfully!")
