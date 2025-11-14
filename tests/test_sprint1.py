"""
Sprint 1 Test Suite
Tests PostgreSQL migration and agent management functionality
"""

import pytest
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from services.task_capsule_repo.app.models import Capsule, CapsuleType
from services.task_capsule_repo.app.repository import CapsuleRepository
from services.orchestrator.app.models.agent_instance import AgentInstance, AgentStatus


class TestSprint1:
    """Comprehensive tests for Sprint 1 functionality"""
    
    @pytest.mark.asyncio
    async def test_capsule_creation(self, db_session: AsyncSession):
        """Test creating a capsule in PostgreSQL"""
        repo = CapsuleRepository(db_session)
        
        capsule_data = {
            "capsule_id": str(uuid.uuid4()),
            "version": "1.0.0",
            "type": CapsuleType.WORKFLOW,
            "manifest_yaml": "apiVersion: argoproj.io/v1alpha1\nkind: Workflow",
            "metadata": {"description": "Test workflow"}
        }
        
        # Create capsule
        capsule = await repo.create_capsule(**capsule_data)
        
        assert capsule.id is not None
        assert capsule.capsule_id == capsule_data["capsule_id"]
        assert capsule.version == capsule_data["version"]
        assert capsule.type == CapsuleType.WORKFLOW
        
        # Retrieve capsule
        retrieved = await repo.get_capsule(capsule.capsule_id, capsule.version)
        assert retrieved is not None
        assert retrieved.id == capsule.id
    
    @pytest.mark.asyncio
    async def test_capsule_versioning(self, db_session: AsyncSession):
        """Test capsule versioning functionality"""
        repo = CapsuleRepository(db_session)
        capsule_id = str(uuid.uuid4())
        
        # Create multiple versions
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        for version in versions:
            await repo.create_capsule(
                capsule_id=capsule_id,
                version=version,
                type=CapsuleType.WORKFLOW,
                manifest_yaml=f"version: {version}"
            )
        
        # List versions
        capsule_versions = await repo.list_capsules(capsule_id=capsule_id)
        assert len(capsule_versions) == 3
        assert [c.version for c in capsule_versions] == versions
    
    @pytest.mark.asyncio
    async def test_agent_instance_model(self, db_session: AsyncSession):
        """Test AgentInstance model with PostgreSQL"""
        instance = AgentInstance(
            agent_type="code-generator",
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            image="python:3.11-slim",
            execution_mode="batch",
            namespace="test-namespace",
            job_name="test-job-123",
            status=AgentStatus.RUNNING,
            metadata={"task": "test_task"}
        )
        
        db_session.add(instance)
        await db_session.commit()
        
        assert instance.id is not None
        assert instance.created_at is not None
        assert instance.updated_at is not None
        
        # Query agent instance
        query = await db_session.execute(
            "SELECT * FROM agent_instances WHERE id = :id",
            {"id": instance.id}
        )
        result = query.fetchone()
        assert result is not None
        assert result.agent_type == "code-generator"
    
    @pytest.mark.asyncio
    async def test_api_endpoints(self):
        """Test API endpoints for capsule registry"""
        async with AsyncClient(base_url="http://localhost:8000") as client:
            # Health check
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            
            # Create capsule
            capsule_data = {
                "capsule_id": str(uuid.uuid4()),
                "version": "1.0.0",
                "type": "workflow",
                "manifest_yaml": "test: manifest",
                "metadata": {"test": True}
            }
            
            response = await client.post("/v1/capsules", json=capsule_data)
            assert response.status_code == 201
            
            # List capsules
            response = await client.get("/v1/capsules")
            assert response.status_code == 200
            capsules = response.json()
            assert "total" in capsules
            assert "items" in capsules
    
    @pytest.mark.asyncio
    async def test_agent_spawner_api(self):
        """Test agent spawner API endpoints"""
        async with AsyncClient(base_url="http://localhost:8001") as client:
            # Health check
            response = await client.get("/health")
            assert response.status_code == 200
            
            # Spawn agent
            spawn_data = {
                "agent_type": "test-agent",
                "tenant_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "image": "python:3.11-slim",
                "execution_mode": "batch",
                "namespace": "test-namespace",
                "env_vars": {"TEST": "true"}
            }
            
            response = await client.post("/v1/spawn", json=spawn_data)
            if response.status_code == 200:
                result = response.json()
                assert "instance_id" in result
                
                # Get agent status
                instance_id = result["instance_id"]
                status_response = await client.get(f"/v1/agents/{instance_id}")
                assert status_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_database_connection(self, db_session: AsyncSession):
        """Test PostgreSQL database connection"""
        # Test connection
        result = await db_session.execute("SELECT version()")
        version = result.scalar()
        assert version is not None
        assert "PostgreSQL" in version
        
        # Test table existence
        result = await db_session.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('capsules', 'agent_instances')
            """
        )
        tables = [row[0] for row in result.fetchall()]
        assert "capsules" in tables
        assert "agent_instances" in tables
    
    @pytest.mark.asyncio
    async def test_capsule_types_enum(self, db_session: AsyncSession):
        """Test capsule type enum values"""
        repo = CapsuleRepository(db_session)
        
        # Test each capsule type
        for capsule_type in CapsuleType:
            capsule = await repo.create_capsule(
                capsule_id=str(uuid.uuid4()),
                version="1.0.0",
                type=capsule_type,
                manifest_yaml=f"type: {capsule_type.value}"
            )
            
            retrieved = await repo.get_capsule(capsule.capsule_id, capsule.version)
            assert retrieved.type == capsule_type
    
    @pytest.mark.asyncio
    async def test_agent_status_transitions(self, db_session: AsyncSession):
        """Test agent status transitions"""
        instance = AgentInstance(
            agent_type="test-agent",
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            image="test-image",
            execution_mode="batch",
            namespace="test",
            status=AgentStatus.PENDING
        )
        
        db_session.add(instance)
        await db_session.commit()
        
        # Update status
        instance.status = AgentStatus.RUNNING
        await db_session.commit()
        
        # Check updated timestamp
        assert instance.updated_at > instance.created_at
        assert instance.status == AgentStatus.RUNNING
    
    def test_uuid_generation(self):
        """Test UUID generation for primary keys"""
        capsule_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        
        assert len(capsule_id) == 36
        assert len(tenant_id) == 36
        assert uuid.UUID(capsule_id)
        assert uuid.UUID(tenant_id)


@pytest.fixture(scope="session")
def event_loop():
    """Create an async event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a database session for tests"""
    # This would typically use a test database
    # For now, we'll use the development database
    from services.task_capsule_repo.app.database import get_db
    async for session in get_db():
        yield session
        break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])