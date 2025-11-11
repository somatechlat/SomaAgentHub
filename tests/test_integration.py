"""
Integration tests for event-driven architecture.

Tests event emission using actual database and repository patterns.
"""

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from services.orchestrator.app.repository.outbox_event_repository import (
    OutboxEventRepository,
)
from services.orchestrator.app.services.event_emission import EventEmissionService
from services.orchestrator.app.planner.schemas import ProjectPlan, ModuleSpec
from services.common.config.base_settings import resolve_env


@pytest.mark.asyncio
async def test_event_emission():
    """Test event emission with actual database integration."""

    # Setup database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables using SQLModel
    from services.orchestrator.app.repository.outbox import OutboxEvent
    from services.orchestrator.app.repository.models import BuildRun

    # Use SQLModel metadata
    SQLModel.metadata.create_all(engine.sync_engine)

    async with async_session() as session:
        # Test repository
        repo = OutboxEventRepository(session)

        # Create real event
        event_data = {
            "plan_id": str(uuid.uuid4()),
            "tenant": "test-tenant",
            "objective": "Test real event emission",
            "agent_ids": ["agent-1", "agent-2"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Create real outbox event
        event = await repo.create_event(
            event_type="orchestration.plan_created",
            topic="orchestrator.events",
            key="test-key",
            payload=event_data,
        )

        await session.commit()

        # Verify event was stored
        assert event.id is not None
        assert event.event_type == "orchestration.plan_created"
        assert event.payload["plan_id"] == event_data["plan_id"]

        # Retrieve events
        events = await repo.get_events_by_type("orchestration.plan_created")
        assert len(events) >= 1

        # Test event emission service
        emission_service = EventEmissionService(session)

        # Create test plan
        test_plan = ProjectPlan(
            plan_id="test-plan-456",
            tenant="test-tenant",
            objective="Test objective",
            modules=[
                ModuleSpec(
                    module_id="module-1",
                    agent_id="agent-1",
                    goal="Test goal",
                    prompt="Test prompt",
                )
            ],
        )

        # Emit plan event
        await emission_service.emit_plan_created_event(plan=test_plan, session_id="test-session", initiator="test-user")

        await session.commit()

        # Verify events
        all_events = await repo.get_events_by_type("orchestration.plan_created")
        assert len(all_events) >= 2

        # Test marking as processed
        await repo.mark_as_processed(events[0].id)

        # Verify status change
        pending_events = await repo.get_pending_events()
        assert len(pending_events) == 1  # One should be processed

        print("✅ Real event emission working correctly")
        return True


@pytest.mark.asyncio
async def test_build_run_events():
    """Test build run lifecycle events."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from services.orchestrator.app.repository.outbox import OutboxEvent

    SQLModel.metadata.create_all(engine.sync_engine)

    async with async_session() as session:
        event_service = EventEmissionService(session)

        # Test build run started
        await event_service.emit_build_run_started_event(
            build_run_id="build-123",
            tenant="test-tenant",
            project_id="project-456",
            workflow_type="multi_agent_orchestration",
            agent_ids=["agent-1", "agent-2", "agent-3"],
        )

        # Test build run completed
        await event_service.emit_build_run_completed_event(
            build_run_id="build-123",
            tenant="test-tenant",
            status="completed",
            duration_seconds=120.5,
            success=True,
        )

        await session.commit()

        # Verify events were created
        repo = OutboxEventRepository(session)
        build_events = await repo.get_events_by_topic("orchestrator.events")

        assert len(build_events) >= 2
        event_types = {e.event_type for e in build_events}
        assert "orchestration.build_run_started" in event_types
        assert "orchestration.build_run_completed" in event_types

        print("✅ Build run lifecycle events working correctly")
        return True


if __name__ == "__main__":
    asyncio.run(test_event_emission())
    asyncio.run(test_build_run_events())
    print("🎉 All real integration tests passed!")
