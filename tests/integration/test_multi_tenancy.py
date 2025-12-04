import pytest
import uuid
from services.orchestrator.app.services.task_service import TaskService
from services.common.models.task import TaskRecordCreate, TaskPriority
from services.common.models.identity import TenantRef, PrincipalRef, TenantStatus, PrincipalType

# Mark as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
class TestMultiTenancy:
    async def test_task_isolation(self, async_db_session):
        """Test that tasks are isolated between tenants"""
        # 1. Setup Tenant A
        tenant_a = TenantRef(name=f"Tenant A {uuid.uuid4()}", status=TenantStatus.ACTIVE)
        async_db_session.add(tenant_a)
        await async_db_session.commit()
        await async_db_session.refresh(tenant_a)
        
        principal_a = PrincipalRef(
            tenant_id=tenant_a.id,
            principal_type=PrincipalType.USER,
            principal_id=f"user-a-{uuid.uuid4()}",
            display_name="User A",
            roles=["user"]
        )
        async_db_session.add(principal_a)
        await async_db_session.commit()
        await async_db_session.refresh(principal_a)

        # 2. Setup Tenant B
        tenant_b = TenantRef(name=f"Tenant B {uuid.uuid4()}", status=TenantStatus.ACTIVE)
        async_db_session.add(tenant_b)
        await async_db_session.commit()
        await async_db_session.refresh(tenant_b)

        # 3. Create Task in Tenant A
        service = TaskService(async_db_session)
        task_create = TaskRecordCreate(
            tenant_id=tenant_a.id,
            user_principal_id=principal_a.id,
            source_application="test-app",
            original_request_text="Secret Task A",
            task_type="general",
            priority=TaskPriority.NORMAL
        )
        task_a = await service.create_task(task_create)
        assert task_a.id is not None

        # 4. Verify Tenant A can see it
        fetched_a = await service.get_task(task_a.id, tenant_a.id)
        assert fetched_a is not None
        assert fetched_a.id == task_a.id

        # 5. Verify Tenant B CANNOT see it
        fetched_b = await service.get_task(task_a.id, tenant_b.id)
        assert fetched_b is None

        # 6. Verify List Isolation
        list_a = await service.list_tasks(tenant_a.id)
        assert len(list_a) >= 1
        assert any(t.id == task_a.id for t in list_a)

        list_b = await service.list_tasks(tenant_b.id)
        assert not any(t.id == task_a.id for t in list_b)
