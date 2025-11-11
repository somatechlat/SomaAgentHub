"""
Working event emission tests using actual project structure.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.common.events.outbox import OutboxEvent, OutboxRepository
from services.common.events.publisher import InMemoryEventPublisher
from services.common.config.base_settings import resolve_env


class BuildRunStatus(str, Enum):
PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"


@pytest.mark.asyncio
async def test_outbox_event_workflow():
"""Test complete outbox event workflow."""

# Setup database
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create tables
from services.common.events.outbox import Base

async with engine.begin() as conn:
await conn.run_sync(Base.metadata.create_all)

async with async_session() as session:
outbox_repo = OutboxRepository(session)
publisher = InMemoryEventPublisher("test-service")

# Test 1: Create and save events
events = []
for i in range(3):
event = OutboxEvent(
event_type="wizard.approved",
aggregate_id=str(uuid.uuid4()),
event_data={
    "wizard_id": f"wizard-{i}",
    "project_id": f"project-{i}",
    "user_id": f"user-{i}",
    "status": BuildRunStatus.PENDING.value,
},
created_at=datetime.now(timezone.utc),
)
events.append(event)

# Save events
saved_events = []
for event in events:
saved = await outbox_repo.save_event(event)
saved_events.append(saved)

await session.commit()

# Test 2: Retrieve unprocessed events
unprocessed = await outbox_repo.get_unprocessed_events(limit=10)
assert len(unprocessed) == 3
assert all(not e.processed for e in unprocessed)

# Test 3: Process events with publisher
for event in unprocessed:
await publisher.publish(
{"event_type": event.event_type, "data": event.event_data}
)
await outbox_repo.mark_processed(event.id)

# Test 4: Verify events were published
assert len(publisher.events) == 3
assert all(e["event_type"] == "wizard.approved" for e in publisher.events)

# Test 5: Verify no unprocessed events remain
remaining = await outbox_repo.get_unprocessed_events(limit=10)
assert len(remaining) == 0

# Test 6: Get events by type
wizard_events = await outbox_repo.get_events_by_type("wizard.approved")
assert len(wizard_events) == 3

print("✅ All outbox workflow tests passed!")


@pytest.mark.asyncio
async def test_event_publisher_functionality():
"""Test event publisher capabilities."""

publisher = InMemoryEventPublisher("test-service")

# Test single event
event_data = {
"event_type": "orchestration.started",
"data": {
"mao_id": str(uuid.uuid4()),
"project_id": "test-project",
"agents": ["agent1", "agent2"],
},
}

await publisher.publish(event_data)
assert len(publisher.events) == 1
assert publisher.events[0]["service"] == "test-service"

# Test batch publishing
batch_events = [
{"event_type": "wizard.completed", "data": {"id": str(uuid.uuid4())}},
{"event_type": "agent.started", "data": {"agent_id": "agent-123"}},
]

await publisher.publish_batch(batch_events)
assert len(publisher.events) == 3

print("✅ Event publisher tests passed!")


if __name__ == "__main__":
asyncio.run(test_outbox_event_workflow())
asyncio.run(test_event_publisher_functionality())
print("🎉 All tests completed successfully!")
