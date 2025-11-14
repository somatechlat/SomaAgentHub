"""
Test suite for event emissions using the outbox pattern.

This module tests the complete event emission flow:
1. Event creation and persistence in outbox
2. Event publisher delivery (Kafka + in-memory)
3. Event schema validation
4. Real-world integration scenarios
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.common.events.outbox import OutboxEvent, OutboxRepository
from services.common.events.publisher import InMemoryEventPublisher
from services.common.contracts.orchestrator import (
WizardApprovedEvent,
OrchestrationStartedEvent,
)
from services.orchestrator.app.main import create_app
from services.common.config.base_settings import resolve_env


@pytest.fixture
def test_app() -> FastAPI:
"""Create test FastAPI app with in-memory database."""
database_url = "sqlite+aiosqlite:///:memory:"
app = create_app(
settings={
"database_url": database_url,
"kafka_bootstrap_servers": "localhost:9092",
"service_name": "test-orchestrator",
}
)
return app


@pytest.fixture
async def test_client(test_app: FastAPI) -> AsyncClient:
"""Create async test client."""
async with AsyncClient(app=test_app, base_url="http://test") as client:
yield client


@pytest.fixture
async def test_db_session() -> AsyncSession:
"""Create test database session."""
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create tables
from services.common.events.models import SQLModel

async with engine.begin() as conn:
await conn.run_sync(SQLModel.metadata.create_all)

async with async_session() as session:
yield session


@pytest.fixture
def event_publisher() -> EventPublisher:
"""Create test event publisher with in-memory backend."""
return EventPublisher(
kafka_config={"bootstrap_servers": "localhost:9092"},
service_name="test-service",
use_in_memory=True,
)


@pytest.fixture
def outbox_repo(test_db_session: AsyncSession) -> OutboxRepository:
"""Create test outbox repository."""
return OutboxRepository(session=test_db_session)


class TestWizardApprovedEvent:
"""Test wizard approval event emissions."""

def test_wizard_approved_event_schema(self):
"""Test wizard approved event schema validation."""
event_data = {
"wizard_id": str(uuid.uuid4()),
"project_id": "test-project-123",
"user_id": "user-456",
"wizard_type": "marketing_campaign",
"configuration": {
"campaign_name": "Summer Sale 2024",
"target_audience": "millennial_shoppers",
"budget": 5000.0,
},
"timestamp": datetime.now(timezone.utc).isoformat(),
}

event = WizardApprovedEvent(**event_data)
assert event.wizard_id == event_data["wizard_id"]
assert event.project_id == "test-project-123"
assert event.wizard_type == "marketing_campaign"
assert event.configuration["budget"] == 5000.0

@pytest.mark.asyncio
async def test_wizard_approved_event_persistence(
self, outbox_repo: OutboxRepository
):
"""Test wizard approved event is persisted in outbox."""
wizard_id = str(uuid.uuid4())
event_data = {
"wizard_id": wizard_id,
"project_id": "test-project-123",
"user_id": "user-456",
"wizard_type": "marketing_campaign",
"configuration": {"key": "value"},
"timestamp": datetime.now(timezone.utc).isoformat(),
}

# Create outbox event
outbox_event = OutboxEvent(
event_type="wizard.approved",
aggregate_id=wizard_id,
event_data=event_data,
created_at=datetime.now(timezone.utc),
)

# Save to outbox
saved_event = await outbox_repo.save_event(outbox_event)

assert saved_event.id is not None
assert saved_event.event_type == "wizard.approved"
assert saved_event.aggregate_id == wizard_id
assert saved_event.event_data == event_data
assert saved_event.processed is False


class TestOrchestrationStartedEvent:
"""Test orchestration started event emissions."""

def test_orchestration_started_event_schema(self):
"""Test orchestration started event schema validation."""
event_data = {
"mao_id": str(uuid.uuid4()),
"project_id": "test-project-123",
"workflow_type": "marketing_campaign",
"agent_ids": ["agent-1", "agent-2", "agent-3"],
"input_data": {"campaign_config": "data"},
"timestamp": datetime.now(timezone.utc).isoformat(),
}

event = OrchestrationStartedEvent(**event_data)
assert event.mao_id == event_data["mao_id"]
assert event.workflow_type == "marketing_campaign"
assert len(event.agent_ids) == 3

@pytest.mark.asyncio
async def test_orchestration_started_event_persistence(
self, outbox_repo: OutboxRepository
):
"""Test orchestration started event is persisted in outbox."""
mao_id = str(uuid.uuid4())
event_data = {
"mao_id": mao_id,
"project_id": "test-project-123",
"workflow_type": "marketing_campaign",
"agent_ids": ["agent-1", "agent-2"],
"input_data": {"test": "data"},
"timestamp": datetime.now(timezone.utc).isoformat(),
}

outbox_event = OutboxEvent(
event_type="orchestration.started",
aggregate_id=mao_id,
event_data=event_data,
created_at=datetime.now(timezone.utc),
)

saved_event = await outbox_repo.save_event(outbox_event)

assert saved_event.id is not None
assert saved_event.event_type == "orchestration.started"
assert saved_event.aggregate_id == mao_id
assert saved_event.event_data == event_data


class TestEventPublisher:
"""Test event publisher functionality."""

@pytest.mark.asyncio
async def test_in_memory_publisher(self, event_publisher: EventPublisher):
"""Test in-memory event publisher."""
test_event = {"event_type": "test.event", "data": {"test": "payload"}}

await event_publisher.publish(test_event)

# Verify event was published to in-memory store
assert len(event_publisher._in_memory_events) == 1
assert event_publisher._in_memory_events[0] == test_event

@pytest.mark.asyncio
async def test_event_schema_validation_in_publisher(
self, event_publisher: EventPublisher
):
"""Test that publisher validates event schemas."""
invalid_event = {"invalid": "schema"}

with pytest.raises(ValueError):
await event_publisher.publish(invalid_event)

@pytest.mark.asyncio
async def test_kafka_publisher_with_mock(self):
"""Test Kafka publisher with mocked producer."""
with patch("aiokafka.AIOKafkaProducer") as mock_producer_class:
mock_producer = AsyncMock()
mock_producer_class.return_value = mock_producer

publisher = EventPublisher(
kafka_config={"bootstrap_servers": "localhost:9092"},
service_name="test-service",
use_in_memory=False,
)

test_event = {
"event_type": "wizard.approved",
"data": {"wizard_id": "test-123"},
}

await publisher.publish(test_event)

# Verify Kafka producer was called
mock_producer.send_and_wait.assert_called_once()
call_args = mock_producer.send_and_wait.call_args
assert call_args[0][0] == "test-service.events"


class TestEventFlowIntegration:
"""Integration tests for complete event flow."""

@pytest.mark.asyncio
async def test_complete_wizard_approval_flow(
self,
test_client: AsyncClient,
test_db_session: AsyncSession,
event_publisher: EventPublisher,
):
"""Test complete wizard approval flow with event emission."""
wizard_id = str(uuid.uuid4())

# Mock wizard approval endpoint
approval_data = {
"wizard_id": wizard_id,
"project_id": "test-project-123",
"user_id": "user-456",
"wizard_type": "marketing_campaign",
"configuration": {"campaign_name": "Test Campaign"},
}

# Simulate wizard approval (this would normally be in your API)
event_data = WizardApprovedEvent(**approval_data)

# Create outbox event
outbox_event = OutboxEvent(
event_type="wizard.approved",
aggregate_id=wizard_id,
event_data=event_data.dict(),
created_at=datetime.now(timezone.utc),
)

outbox_repo = OutboxRepository(session=test_db_session)
await outbox_repo.save_event(outbox_event)

# Verify event was persisted
events = await outbox_repo.get_unprocessed_events(limit=10)
assert len(events) == 1
assert events[0].event_type == "wizard.approved"

# Publish events
await event_publisher.publish_batch(
[{"event_type": e.event_type, "data": e.event_data} for e in events]
)

# Verify events were published
assert len(event_publisher._in_memory_events) == 1
published_event = event_publisher._in_memory_events[0]
assert published_event["event_type"] == "wizard.approved"
assert published_event["data"]["wizard_id"] == wizard_id

@pytest.mark.asyncio
async def test_event_retry_mechanism(
self, event_publisher: EventPublisher, outbox_repo: OutboxRepository
):
"""Test event retry mechanism for failed publishes."""
# Create a failed event
outbox_event = OutboxEvent(
event_type="test.retry",
aggregate_id=str(uuid.uuid4()),
event_data={"test": "data"},
created_at=datetime.now(timezone.utc),
retry_count=2,
processed=False,
)

await outbox_repo.save_event(outbox_event)

# Mock publisher to simulate failure
with patch.object(
event_publisher, "_publish_to_kafka", side_effect=Exception("Kafka down")
):
with patch("asyncio.sleep"):  # Speed up retries
await event_publisher.publish_with_retry(outbox_event)

# Verify retry count was incremented
updated_event = await outbox_repo.get_event(outbox_event.id)
assert updated_event.retry_count == 3
assert updated_event.processed is False


class TestEventValidation:
"""Test event schema validation and error handling."""

def test_invalid_event_type_raises_error(self):
"""Test invalid event type raises validation error."""
invalid_data = {
"wizard_id": "not-a-uuid",
"project_id": None,  # Missing required field
"user_id": "user-123",
}

with pytest.raises(ValueError):
WizardApprovedEvent(**invalid_data)

@pytest.mark.asyncio
async def test_malformed_event_data_handling(self, event_publisher: EventPublisher):
"""Test handling of malformed event data."""
malformed_event = {
"event_type": "wizard.approved",
"data": "invalid-string-instead-of-dict",
}

with pytest.raises(ValueError):
await event_publisher.publish(malformed_event)


class TestOutboxRepository:
"""Test outbox repository functionality."""

@pytest.mark.asyncio
async def test_get_unprocessed_events(self, outbox_repo: OutboxRepository):
"""Test retrieving unprocessed events."""
# Create test events
events = [
OutboxEvent(
event_type="test.event",
aggregate_id=str(uuid.uuid4()),
event_data={"test": f"data-{i}"},
created_at=datetime.now(timezone.utc),
processed=False,
)
for i in range(3)
]

# Save events
for event in events:
await outbox_repo.save_event(event)

# Retrieve unprocessed events
unprocessed = await outbox_repo.get_unprocessed_events(limit=10)
assert len(unprocessed) == 3
assert all(not e.processed for e in unprocessed)

@pytest.mark.asyncio
async def test_mark_event_processed(self, outbox_repo: OutboxRepository):
"""Test marking events as processed."""
event = OutboxEvent(
event_type="test.process",
aggregate_id=str(uuid.uuid4()),
event_data={"test": "data"},
created_at=datetime.now(timezone.utc),
processed=False,
)

saved_event = await outbox_repo.save_event(event)

# Mark as processed
await outbox_repo.mark_processed(saved_event.id)

# Verify
updated_event = await outbox_repo.get_event(saved_event.id)
assert updated_event.processed is True
assert updated_event.processed_at is not None
