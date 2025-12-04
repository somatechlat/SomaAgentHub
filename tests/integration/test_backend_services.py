import pytest
import uuid
from datetime import datetime
from services.orchestrator.app.services.role_service import RoleService
from services.orchestrator.app.services.task_service import TaskService
from services.common.models.role import RoleDefinitionCreate, AgentBindingCreate
from services.common.models.task import TaskRecordCreate, TaskStatus, TaskPriority
from services.common.models.identity import TenantRef, PrincipalRef, ExternalRef, TenantStatus, PrincipalType, ExternalSystem
from services.common.models.capsule_complete import CapsuleDefinition

# Mark as integration tests
pytestmark = pytest.mark.integration

class TestRoleService:
    def test_create_role_and_binding(self, sync_db_session):
        """Test creating a role and binding an agent to it"""
        # 0. Create Tenant and ExternalRef
        tenant = TenantRef(
            name=f"Test Tenant {uuid.uuid4()}",
            status=TenantStatus.ACTIVE
        )
        sync_db_session.add(tenant)
        sync_db_session.commit()
        sync_db_session.refresh(tenant)
        tenant_id = tenant.id

        agent_ref = ExternalRef(
            tenant_id=tenant_id,
            system=ExternalSystem.SOMA_AGENT01,
            type="AGENT",
            external_id=f"agent-{uuid.uuid4()}",
            meta_data={}
        )
        sync_db_session.add(agent_ref)
        sync_db_session.commit()
        sync_db_session.refresh(agent_ref)
        agent_ref_id = str(agent_ref.id)

        service = RoleService(sync_db_session)
        
        # 1. Create Role
        role_create = RoleDefinitionCreate(
            tenant_id=tenant_id,
            name="Test Role",
            description="A test role",
            expected_behavior="Be helpful"
        )
        role = service.create_role_definition(role_create)
        
        assert role.id is not None
        assert role.name == "Test Role"
        assert role.tenant_id == tenant_id
        
        # 2. Create Agent Binding
        binding_create = AgentBindingCreate(
            tenant_id=tenant_id,
            role_id=role.id,
            agent01_agent_ref_id=agent_ref_id,
            supported_task_types=["general"],
            supported_domains=["test"]
        )
        binding = service.create_agent_binding(binding_create)
        
        assert binding.id is not None
        assert binding.role_id == role.id
        
        # 3. List Bindings
        bindings = service.list_bindings_for_role(role.id, tenant_id)
        assert len(bindings) == 1
        assert bindings[0].id == binding.id

@pytest.mark.asyncio
class TestTaskService:
    async def test_task_lifecycle(self, async_db_session):
        """Test the full lifecycle of a task"""
        # 0. Create Tenant and Principal
        tenant = TenantRef(
            name=f"Test Tenant Lifecycle {uuid.uuid4()}",
            status=TenantStatus.ACTIVE
        )
        async_db_session.add(tenant)
        await async_db_session.commit()
        await async_db_session.refresh(tenant)
        tenant_id = tenant.id

        principal = PrincipalRef(
            tenant_id=tenant_id,
            principal_type=PrincipalType.USER,
            principal_id=f"user-lifecycle-{uuid.uuid4()}",
            display_name="Lifecycle User",
            roles=["user"]
        )
        async_db_session.add(principal)
        await async_db_session.commit()
        await async_db_session.refresh(principal)
        user_id = principal.id

        service = TaskService(async_db_session)
        
        # 1. Create Task
        task_create = TaskRecordCreate(
            tenant_id=tenant_id,
            user_principal_id=user_id,
            source_application="lifecycle-app",
            original_request_text="Lifecycle test",
            task_type="test",
            priority=TaskPriority.HIGH
        )
        task = await service.create_task(task_create)
        assert task.status == TaskStatus.RECEIVED
        
        # 2. Update Status
        from services.common.models.task import TaskRecordUpdate
        update = TaskRecordUpdate(
            status=TaskStatus.ANALYZING,
            reason="Starting analysis",
            actor_principal_id=user_id
        )
        updated_task = await service.update_task_status(task.id, tenant_id, update)
        assert updated_task.status == TaskStatus.ANALYZING
        
        # 3. Verify History
        history = await service.get_task_history(task.id, tenant_id)
        assert len(history) == 2  # Initial + Update
        assert history[0].new_status == TaskStatus.RECEIVED
        assert history[1].new_status == TaskStatus.ANALYZING
        assert history[1].reason == "Starting analysis"

    async def test_create_and_get_task(self, async_db_session):
        """Test creating and retrieving a task"""
        # 0. Create Tenant and Principal
        tenant = TenantRef(
            name=f"Test Tenant Async {uuid.uuid4()}",
            status=TenantStatus.ACTIVE
        )
        async_db_session.add(tenant)
        await async_db_session.commit()
        await async_db_session.refresh(tenant)
        tenant_id = tenant.id

        principal = PrincipalRef(
            tenant_id=tenant_id,
            principal_type=PrincipalType.USER,
            principal_id=f"user-{uuid.uuid4()}",
            display_name="Test User",
            roles=["admin"]
        )
        async_db_session.add(principal)
        await async_db_session.commit()
        await async_db_session.refresh(principal)
        user_id = principal.id

        service = TaskService(async_db_session)
        
        task_create = TaskRecordCreate(
            tenant_id=tenant_id,
            user_principal_id=user_id,
            source_application="test-app",
            original_request_text="Do something",
            task_type="general",
            domain="test",
            priority=TaskPriority.NORMAL
        )
        
        try:
            task = await service.create_task(task_create)
            assert task.id is not None
            assert task.status == TaskStatus.RECEIVED
            
            fetched = await service.get_task(task.id, tenant_id)
            assert fetched is not None
            assert fetched.id == task.id
        except Exception as e:
            pytest.fail(f"Task creation failed: {e}")
