"""Basic event emission tests – simplified for current project structure."""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from services.common.events.outbox import OutboxEvent, OutboxRepository
from services.common.events.publisher import InMemoryEventPublisher


@pytest.mark.asyncio
async def test_basic_outbox_event_creation() -> None:
    """Test basic outbox event creation."""
    import os
    # Use port 10004 as defined in docker-compose.yml for app-postgres
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://somaagent:somaagent@localhost:10004/somaagent")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    from sqlalchemy.sql import expression
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.execute(expression.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        outbox_repo = OutboxRepository(session)

        # Create event
        event_data = {
            "wizard_id": str(uuid.uuid4()),
            "project_id": "test-project",
            "user_id": "test-user",
        }

        event = OutboxEvent(
            event_type="wizard.approved",
            aggregate_id=str(uuid.uuid4()),
            event_data=event_data,
            created_at=datetime.now(UTC),
        )

        # Save event
        saved_event = await outbox_repo.save_event(event)
        await session.commit()

        # Verify event was saved
        assert saved_event.id is not None
        assert saved_event.event_type == "wizard.approved"
        assert saved_event.processed is False

        # Retrieve events
        events = await outbox_repo.get_unprocessed_events()
        assert len(events) == 1
        assert events[0].event_type == "wizard.approved"


@pytest.mark.asyncio
async def test_event_publisher_basic() -> None:
    """Test basic event publisher functionality."""
    publisher = InMemoryEventPublisher(service_name="test-service")

    event_data = {"event_type": "test.event", "data": {"test": "payload"}}

    await publisher.publish(event_data)

    # Verify event was published
    assert len(publisher.events) == 1
    assert publisher.events[0] == event_data


if __name__ == "__main__":
    # Run basic tests when executed directly
    asyncio.run(test_basic_outbox_event_creation())
    asyncio.run(test_event_publisher_basic())
    print("Basic tests passed!")
