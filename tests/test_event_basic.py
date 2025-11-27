"""Basic event emission tests – simplified for current project structure.
"""

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.common.events.outbox import OutboxEvent, OutboxRepository
from services.common.events.publisher import InMemoryEventPublisher
from services.common.config.base_settings import resolve_env


@pytest.mark.asyncio
async def test_basic_outbox_event_creation() -> None:
	"""Test basic outbox event creation."""
	engine = create_async_engine("sqlite+aiosqlite:///:memory:")
	async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

	# Create tables
	from services.common.events.outbox import Base

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

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
			created_at=datetime.now(timezone.utc),
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
