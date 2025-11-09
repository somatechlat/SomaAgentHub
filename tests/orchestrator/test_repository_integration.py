"""
Integration tests for repository abstraction layer.

Tests the complete repository layer including:
- BuildRunRepository interface
- SQL implementation with proper isolation
- Transaction handling
- Event emission integration
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from enum import Enum


class BuildRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


from services.orchestrator.app.repository.build_run import (
    BuildRunRepository,
    SQLBuildRunRepository,
    BuildRunModel,
)
from services.orchestrator.app.repository.outbox import OutboxRepository
from services.common.events.models import OutboxEvent


@pytest.fixture
def sqlite_engine():
    """Create SQLite engine for testing."""
    return create_async_engine("sqlite+aiosqlite:///:memory:")


@pytest.fixture
async def db_session(sqlite_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Create tables
    from services.common.events.models import SQLModel

    async with sqlite_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def build_run_repo(db_session: AsyncSession) -> BuildRunRepository:
    """Create build run repository instance."""
    return SQLBuildRunRepository(session=db_session)


@pytest.fixture
def outbox_repo(db_session: AsyncSession) -> OutboxRepository:
    """Create outbox repository instance."""
    return OutboxRepository(session=db_session)


class TestBuildRunRepository:
    """Test build run repository functionality."""

    @pytest.mark.asyncio
    async def test_create_build_run(self, build_run_repo: BuildRunRepository):
        """Test creating a new build run."""
        build_id = str(uuid.uuid4())
        project_id = "test-project-123"

        build_run = await build_run_repo.create_build_run(
            build_id=build_id,
            project_id=project_id,
            workflow_type="marketing_campaign",
            status=BuildRunStatus.PENDING,
        )

        assert build_run.id == build_id
        assert build_run.project_id == project_id
        assert build_run.workflow_type == "marketing_campaign"
        assert build_run.status == BuildRunStatus.PENDING
        assert build_run.created_at is not None

    @pytest.mark.asyncio
    async def test_get_build_run(self, build_run_repo: BuildRunRepository):
        """Test retrieving a build run by ID."""
        build_id = str(uuid.uuid4())

        # Create build run
        created = await build_run_repo.create_build_run(
            build_id=build_id,
            project_id="test-project",
            workflow_type="test_type",
            status=BuildRunStatus.RUNNING,
        )

        # Retrieve it
        retrieved = await build_run_repo.get_build_run(build_id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.project_id == created.project_id
        assert retrieved.status == BuildRunStatus.RUNNING

    @pytest.mark.asyncio
    async def test_update_build_run_status(self, build_run_repo: BuildRunRepository):
        """Test updating build run status."""
        build_id = str(uuid.uuid4())

        # Create build run
        await build_run_repo.create_build_run(
            build_id=build_id,
            project_id="test-project",
            workflow_type="test_type",
            status=BuildRunStatus.PENDING,
        )

        # Update status
        updated = await build_run_repo.update_build_run_status(
            build_id=build_id,
            status=BuildRunStatus.COMPLETED,
            metadata={"completion_time": "2024-01-01T00:00:00Z"},
        )

        assert updated.status == BuildRunStatus.COMPLETED
        assert updated.metadata["completion_time"] == "2024-01-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_get_build_runs_by_project(self, build_run_repo: BuildRunRepository):
        """Test retrieving build runs by project ID."""
        project_id = "test-project-456"

        # Create multiple build runs
        for i in range(3):
            await build_run_repo.create_build_run(
                build_id=str(uuid.uuid4()),
                project_id=project_id,
                workflow_type="test_type",
                status=BuildRunStatus.PENDING,
            )

        # Retrieve by project
        build_runs = await build_run_repo.get_build_runs_by_project(project_id)

        assert len(build_runs) == 3
        assert all(br.project_id == project_id for br in build_runs)

    @pytest.mark.asyncio
    async def test_get_build_runs_by_status(self, build_run_repo: BuildRunRepository):
        """Test retrieving build runs by status."""
        # Create build runs with different statuses
        statuses = [
            BuildRunStatus.PENDING,
            BuildRunStatus.RUNNING,
            BuildRunStatus.FAILED,
        ]

        for status in statuses:
            await build_run_repo.create_build_run(
                build_id=str(uuid.uuid4()),
                project_id="test-project",
                workflow_type="test_type",
                status=status,
            )

        # Retrieve by status
        running_runs = await build_run_repo.get_build_runs_by_status(BuildRunStatus.RUNNING)

        assert len(running_runs) == 1
        assert running_runs[0].status == BuildRunStatus.RUNNING


class TestRepositoryTransactionHandling:
    """Test repository transaction handling and isolation."""

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_session: AsyncSession, build_run_repo: BuildRunRepository):
        """Test transaction rollback on error."""
        build_id = str(uuid.uuid4())

        try:
            async with db_session.begin():
                # Create build run
                await build_run_repo.create_build_run(
                    build_id=build_id,
                    project_id="test-project",
                    workflow_type="test_type",
                    status=BuildRunStatus.PENDING,
                )

                # Simulate an error
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify build run was not created due to rollback
        retrieved = await build_run_repo.get_build_run(build_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_concurrent_access_isolation(self, sqlite_engine):
        """Test concurrent access isolation."""
        async_session = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)

        build_id = str(uuid.uuid4())

        # First session creates build run
        async with async_session() as session1:
            repo1 = SQLBuildRunRepository(session=session1)
            await repo1.create_build_run(
                build_id=build_id,
                project_id="test-project",
                workflow_type="test_type",
                status=BuildRunStatus.PENDING,
            )
            await session1.commit()

        # Second session reads build run
        async with async_session() as session2:
            repo2 = SQLBuildRunRepository(session=session2)
            retrieved = await repo2.get_build_run(build_id)
            assert retrieved is not None
            assert retrieved.status == BuildRunStatus.PENDING


class TestEventEmissionIntegration:
    """Test integration between repository and event emission."""

    @pytest.mark.asyncio
    async def test_build_run_creation_emits_event(
        self, build_run_repo: BuildRunRepository, outbox_repo: OutboxRepository
    ):
        """Test that build run creation emits orchestration started event."""
        build_id = str(uuid.uuid4())
        project_id = "test-project-789"

        # Create build run with event emission
        build_run = await build_run_repo.create_build_run(
            build_id=build_id,
            project_id=project_id,
            workflow_type="data_analysis",
            status=BuildRunStatus.RUNNING,
            emit_event=True,
        )

        # Verify event was created in outbox
        events = await outbox_repo.get_unprocessed_events(limit=10)
        orchestration_events = [e for e in events if e.event_type == "orchestration.started"]

        assert len(orchestration_events) == 1
        event = orchestration_events[0]
        assert event.aggregate_id == build_id
        assert event.event_data["mao_id"] == build_id
        assert event.event_data["project_id"] == project_id
        assert event.event_data["workflow_type"] == "data_analysis"

    @pytest.mark.asyncio
    async def test_build_run_completion_emits_event(
        self, build_run_repo: BuildRunRepository, outbox_repo: OutboxRepository
    ):
        """Test that build run completion emits completion event."""
        build_id = str(uuid.uuid4())

        # Create build run
        await build_run_repo.create_build_run(
            build_id=build_id,
            project_id="test-project",
            workflow_type="test_type",
            status=BuildRunStatus.RUNNING,
        )

        # Update to completed with event emission
        await build_run_repo.update_build_run_status(
            build_id=build_id,
            status=BuildRunStatus.COMPLETED,
            metadata={"duration": 120},
            emit_event=True,
        )

        # Verify completion event
        events = await outbox_repo.get_unprocessed_events(limit=10)
        completion_events = [e for e in events if e.event_type == "orchestration.completed"]

        assert len(completion_events) == 1
        event = completion_events[0]
        assert event.aggregate_id == build_id
        assert event.event_data["status"] == "completed"
        assert event.event_data["duration"] == 120

    @pytest.mark.asyncio
    async def test_bulk_operation_with_events(self, build_run_repo: BuildRunRepository, outbox_repo: OutboxRepository):
        """Test bulk operation with event emission."""
        project_id = "bulk-test-project"

        # Create multiple build runs
        build_ids = [str(uuid.uuid4()) for _ in range(3)]

        for build_id in build_ids:
            await build_run_repo.create_build_run(
                build_id=build_id,
                project_id=project_id,
                workflow_type="test_type",
                status=BuildRunStatus.PENDING,
                emit_event=True,
            )

        # Verify events were created
        events = await outbox_repo.get_unprocessed_events(limit=10)
        orchestration_events = [e for e in events if e.event_type == "orchestration.started"]

        assert len(orchestration_events) == 3
        event_build_ids = {e.event_data["mao_id"] for e in orchestration_events}
        assert event_build_ids == set(build_ids)


class TestRepositoryPerformance:
    """Test repository performance and scalability."""

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, build_run_repo: BuildRunRepository):
        """Test handling of large datasets."""
        project_id = "performance-test"

        # Create 100 build runs
        for i in range(100):
            await build_run_repo.create_build_run(
                build_id=str(uuid.uuid4()),
                project_id=project_id,
                workflow_type="test_type",
                status=BuildRunStatus.PENDING,
            )

        # Retrieve all runs for project
        build_runs = await build_run_repo.get_build_runs_by_project(project_id)

        assert len(build_runs) == 100
        assert all(br.project_id == project_id for br in build_runs)

    @pytest.mark.asyncio
    async def test_pagination_support(self, build_run_repo: BuildRunRepository):
        """Test pagination support in repository queries."""
        project_id = "pagination-test"

        # Create 50 build runs
        for i in range(50):
            await build_run_repo.create_build_run(
                build_id=str(uuid.uuid4()),
                project_id=project_id,
                workflow_type="test_type",
                status=BuildRunStatus.PENDING,
            )

        # Test pagination
        page1 = await build_run_repo.get_build_runs_by_project(project_id, limit=20, offset=0)
        page2 = await build_run_repo.get_build_runs_by_project(project_id, limit=20, offset=20)

        assert len(page1) == 20
        assert len(page2) == 20
        assert page1[0].id != page2[0].id  # Different pages
