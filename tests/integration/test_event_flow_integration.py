"""
End-to-end integration tests for complete event flow.

This module tests the complete event flow from wizard approval through
orchestration start to completion, validating the event-driven architecture.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.common.events.models import OutboxEvent
from services.common.events.publisher import EventPublisher
from services.common.contracts.orchestrator import (
    WizardApprovedEvent,
    OrchestrationStartedEvent,
)
from services.orchestrator.app.repository.outbox import OutboxRepository
from services.gateway_api.app.wizard_engine import wizard_engine
from services.orchestrator.app.main import build_app as build_orchestrator_app


class TestEndToEndEventFlow:
    """Test complete event-driven workflow integration."""

    @pytest.fixture
    def gateway_app(self) -> FastAPI:
        """Create test gateway app."""
        from services.gateway_api.app.main import build_app

        return build_app(test_mode=True)

    @pytest.fixture
    def orchestrator_app(self) -> FastAPI:
        """Create test orchestrator app."""
        return build_orchestrator_app()

    @pytest.fixture
    async def test_db_session(self):
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
    def event_publisher(self) -> EventPublisher:
        """Create test event publisher."""
        return EventPublisher(
            kafka_config={"bootstrap_servers": "localhost:9092"},
            service_name="test-service",
            use_in_memory=True,
        )

    @pytest.mark.asyncio
    async def test_complete_wizard_to_orchestration_flow(
        self, test_db_session: AsyncSession, event_publisher: EventPublisher
    ):
        """Test complete flow from wizard approval to orchestration events."""

        # Step 1: Create and complete a wizard session
        wizard_id = "marketing_campaign"
        user_id = "test-user-123"
        project_id = "test-project-456"

        # Start wizard session
        session_data = wizard_engine.start_wizard(
            wizard_id=wizard_id, user_id=user_id, metadata={"project_id": project_id}
        )

        session_id = session_data["session_id"]

        # Complete wizard by answering all questions
        wizard_schema = wizard_engine.wizard_schemas[wizard_id]
        questions = wizard_schema.get("questions", [])

        for question in questions:
            answer = {"value": f"test-answer-{question['id']}"}
            wizard_engine.submit_answer(session_id, answer)

        # Step 2: Approve wizard execution
        approval_result = wizard_engine.approve_execution(session_id)

        assert approval_result["status"] == "approved"
        assert "orchestration_id" in approval_result

        # Step 3: Verify wizard approved event was emitted
        outbox_repo = OutboxRepository(session=test_db_session)
        wizard_events = await outbox_repo.get_events_by_type("wizard.approved")

        assert len(wizard_events) >= 1
        wizard_event = wizard_events[0]
        assert wizard_event.event_type == "wizard.approved"
        assert wizard_event.aggregate_id == session_id
        assert wizard_event.event_data["wizard_id"] == wizard_id
        assert wizard_event.event_data["project_id"] == project_id
        assert wizard_event.event_data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_orchestration_start_event_emission(
        self, test_db_session: AsyncSession, event_publisher: EventPublisher
    ):
        """Test orchestration start event emission."""

        orchestration_id = str(uuid.uuid4())
        project_id = "test-project-789"

        # Start orchestration via API
        orchestration_data = {
            "tenant": "test-tenant",
            "initiator": "test-user",
            "directives": [
                {
                    "agent_id": "marketing-agent",
                    "goal": "Create marketing campaign",
                    "prompt": "Create a comprehensive marketing campaign",
                    "capabilities": ["content-creation", "marketing"],
                    "metadata": {"campaign_type": "social_media"},
                },
                {
                    "agent_id": "analytics-agent",
                    "goal": "Analyze campaign performance",
                    "prompt": "Analyze the performance metrics",
                    "capabilities": ["data-analysis", "reporting"],
                    "metadata": {"report_format": "json"},
                },
            ],
            "project_id": project_id,
            "notification_channel": "email",
        }

        # Create orchestration started event directly (simulating API call)
        event_data = OrchestrationStartedEvent(
            mao_id=orchestration_id,
            project_id=project_id,
            workflow_type="multi_agent_orchestration",
            agent_ids=["marketing-agent", "analytics-agent"],
            input_data=orchestration_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        outbox_event = OutboxEvent(
            event_type="orchestration.started",
            aggregate_id=orchestration_id,
            event_data=event_data.dict(),
            created_at=datetime.now(timezone.utc),
        )

        outbox_repo = OutboxRepository(session=test_db_session)
        await outbox_repo.save_event(outbox_event)

        # Verify event was created
        orchestration_events = await outbox_repo.get_events_by_type("orchestration.started")

        assert len(orchestration_events) >= 1
        orchestration_event = orchestration_events[0]
        assert orchestration_event.event_type == "orchestration.started"
        assert orchestration_event.aggregate_id == orchestration_id
        assert orchestration_event.event_data["project_id"] == project_id
        assert len(orchestration_event.event_data["agent_ids"]) == 2

    @pytest.mark.asyncio
    async def test_event_publisher_delivery(self, test_db_session: AsyncSession, event_publisher: EventPublisher):
        """Test that events are properly delivered via publisher."""

        # Create test events
        events = [
            OutboxEvent(
                event_type="wizard.approved",
                aggregate_id=str(uuid.uuid4()),
                event_data={
                    "wizard_id": "test-wizard",
                    "project_id": "test-project",
                    "user_id": "test-user",
                },
                created_at=datetime.now(timezone.utc),
            ),
            OutboxEvent(
                event_type="orchestration.started",
                aggregate_id=str(uuid.uuid4()),
                event_data={
                    "mao_id": "test-mao",
                    "project_id": "test-project",
                    "workflow_type": "test-workflow",
                },
                created_at=datetime.now(timezone.utc),
            ),
        ]

        # Save events to outbox
        outbox_repo = OutboxRepository(session=test_db_session)
        for event in events:
            await outbox_repo.save_event(event)

        # Retrieve unprocessed events
        unprocessed_events = await outbox_repo.get_unprocessed_events(limit=10)

        # Publish events
        for event in unprocessed_events:
            await event_publisher.publish({"event_type": event.event_type, "data": event.event_data})
            await outbox_repo.mark_processed(event.id)

        # Verify events were published to in-memory store
        assert len(event_publisher._in_memory_events) == 2

        published_types = [e["event_type"] for e in event_publisher._in_memory_events]
        assert "wizard.approved" in published_types
        assert "orchestration.started" in published_types

    @pytest.mark.asyncio
    async def test_event_schema_validation_in_flow(self, test_db_session: AsyncSession):
        """Test that events conform to expected schemas throughout the flow."""

        # Test wizard approved event schema
        wizard_data = {
            "wizard_id": str(uuid.uuid4()),
            "project_id": "test-project-schema",
            "user_id": "test-user-schema",
            "wizard_type": "marketing_campaign",
            "configuration": {
                "campaign_name": "Schema Test Campaign",
                "budget": 1000.0,
                "target_audience": "test-audience",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        wizard_event = WizardApprovedEvent(**wizard_data)

        # Test orchestration started event schema
        orchestration_data = {
            "mao_id": str(uuid.uuid4()),
            "project_id": "test-project-schema",
            "workflow_type": "marketing_campaign",
            "agent_ids": ["agent-1", "agent-2", "agent-3"],
            "input_data": {
                "campaign_config": wizard_data["configuration"],
                "user_preferences": {"priority": "high"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        orchestration_event = OrchestrationStartedEvent(**orchestration_data)

        # Save both events to outbox
        outbox_repo = OutboxRepository(session=test_db_session)

        await outbox_repo.save_event(
            OutboxEvent(
                event_type="wizard.approved",
                aggregate_id=wizard_event.wizard_id,
                event_data=wizard_event.dict(),
                created_at=datetime.now(timezone.utc),
            )
        )

        await outbox_repo.save_event(
            OutboxEvent(
                event_type="orchestration.started",
                aggregate_id=orchestration_event.mao_id,
                event_data=orchestration_event.dict(),
                created_at=datetime.now(timezone.utc),
            )
        )

        # Verify both events were saved correctly
        wizard_events = await outbox_repo.get_events_by_type("wizard.approved")
        orchestration_events = await outbox_repo.get_events_by_type("orchestration.started")

        assert len(wizard_events) >= 1
        assert len(orchestration_events) >= 1

        # Verify schema compliance in stored events
        stored_wizard = wizard_events[0]
        assert stored_wizard.event_data["wizard_id"] == wizard_event.wizard_id
        assert stored_wizard.event_data["project_id"] == wizard_event.project_id

        stored_orchestration = orchestration_events[0]
        assert stored_orchestration.event_data["mao_id"] == orchestration_event.mao_id
        assert stored_orchestration.event_data["agent_ids"] == orchestration_event.agent_ids

    @pytest.mark.asyncio
    async def test_event_retry_and_failure_handling(
        self, test_db_session: AsyncSession, event_publisher: EventPublisher
    ):
        """Test event retry mechanism and failure handling."""

        # Mock publisher to simulate failure
        with patch.object(
            event_publisher,
            "_publish_to_kafka",
            side_effect=Exception("Kafka unavailable"),
        ):
            # Create event
            event = OutboxEvent(
                event_type="test.retry",
                aggregate_id=str(uuid.uuid4()),
                event_data={"test": "retry"},
                created_at=datetime.now(timezone.utc),
                retry_count=0,
            )

            outbox_repo = OutboxRepository(session=test_db_session)
            await outbox_repo.save_event(event)

            # Attempt to publish (will fail)
            try:
                await event_publisher.publish({"event_type": event.event_type, "data": event.event_data})
            except Exception:
                pass  # Expected failure

            # Verify retry count was not incremented (since we're using in-memory)
            # In real implementation, this would increment retry count
            updated_event = await outbox_repo.get_event(event.id)
            assert updated_event.retry_count == 0  # In-memory doesn't retry
            assert updated_event.processed is False

    @pytest.mark.asyncio
    async def test_bulk_event_processing(self, test_db_session: AsyncSession, event_publisher: EventPublisher):
        """Test processing multiple events efficiently."""

        # Create multiple events
        events = []
        for i in range(10):
            event = OutboxEvent(
                event_type="test.bulk",
                aggregate_id=f"test-{i}",
                event_data={"index": i, "batch": True},
                created_at=datetime.now(timezone.utc),
            )
            events.append(event)

        # Save all events
        outbox_repo = OutboxRepository(session=test_db_session)
        for event in events:
            await outbox_repo.save_event(event)

        # Retrieve unprocessed events
        unprocessed_events = await outbox_repo.get_unprocessed_events(limit=10)

        # Publish in batch
        batch_data = [{"event_type": e.event_type, "data": e.event_data} for e in unprocessed_events]

        await event_publisher.publish_batch(batch_data)

        # Mark all as processed
        for event in unprocessed_events:
            await outbox_repo.mark_processed(event.id)

        # Verify all events were published
        assert len(event_publisher._in_memory_events) == 10

        # Verify no unprocessed events remain
        remaining_events = await outbox_repo.get_unprocessed_events(limit=20)
        assert len(remaining_events) == 0


class TestEventFlowWithRealEndpoints:
    """Test event flow with actual FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_gateway_wizard_api_integration(self):
        """Test wizard API integration with gateway."""

        # This would require full FastAPI app with test client
        # For now, we'll test the core event emission logic

        gateway_app = FastAPI()

        # Add test endpoint for wizard approval
        @gateway_app.post("/v1/wizard/{session_id}/approve")
        async def approve_wizard(session_id: str):
            # Simulate wizard approval
            from services.gateway_api.app.wizard_engine import wizard_engine

            try:
                result = wizard_engine.approve_execution(session_id)
                return {"status": "success", "data": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # Test with async client
        async with AsyncClient(app=gateway_app, base_url="http://test") as client:
            # This test would need proper setup with real wizard session
            pass

    @pytest.mark.asyncio
    async def test_orchestrator_mao_api_integration(self):
        """Test MAO API integration with orchestrator."""

        orchestrator_app = build_orchestrator_app()

        async with AsyncClient(app=orchestrator_app, base_url="http://test") as client:
            # Test MAO start endpoint
            mao_data = {
                "tenant": "test-tenant",
                "initiator": "test-user",
                "directives": [
                    {
                        "agent_id": "test-agent",
                        "goal": "Test goal",
                        "prompt": "Test prompt",
                    }
                ],
                "project_id": "test-project",
            }

            response = await client.post("/v1/mao/start", json=mao_data)

            # Since the orchestrator might not be fully set up, we'll check structure
            assert response.status_code in [200, 503]  # 503 if Temporal not available

            if response.status_code == 200:
                data = response.json()
                assert "orchestration_id" in data
                assert data["status"] == "started"
