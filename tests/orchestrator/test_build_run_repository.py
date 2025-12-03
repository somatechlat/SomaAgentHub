import pytest
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from services.orchestrator.app.repository.build_run import SQLBuildRunRepository
from services.orchestrator.app.repository.models import BuildRun

@pytest.mark.asyncio
async def test_build_run_repository_crud():
    # Setup async database
    # Use port 10004 as defined in docker-compose.yml for app-postgres
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://somaagent:somaagent@localhost:10004/somaagent")
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
        repo = SQLBuildRunRepository(session)
        
        build_id = str(uuid.uuid4())
        project_id = "proj-1"
        
        # Test create
        created = await repo.create_build_run(
            build_id=build_id,
            tenant="test-tenant",
            project_id=project_id,
            pricing_snapshot_id="price-123",
            workflow_type="test-workflow",
            status="pending",
            emit_event=True
        )
        
        assert created.id == uuid.UUID(build_id)
        assert created.project_id == project_id
        assert created.status == "pending"
        
        await session.commit()
        
        # Test get
        fetched = await repo.get_build_run(build_id)
        assert fetched is not None
        assert fetched.id == uuid.UUID(build_id)
        
        # Test update
        updated = await repo.update_build_run_status(
            build_id=build_id,
            status="running",
            metadata={"duration": 10},
            emit_event=True
        )
        assert updated.status == "running"
        assert updated.metadata_json["duration"] == 10
        
        # Test list by project
        runs = await repo.get_build_runs_by_project(project_id)
        assert len(runs) >= 1
        assert runs[0].id == uuid.UUID(build_id)
