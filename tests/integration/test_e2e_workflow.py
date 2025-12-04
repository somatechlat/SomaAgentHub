import pytest
import uuid
from datetime import datetime
from services.orchestrator.app.services.task_service import TaskService
from services.orchestrator.app.services.role_service import RoleService
from services.common.models.identity import TenantRef, PrincipalRef, ExternalRef, TenantStatus, PrincipalType, ExternalSystem
from services.common.models.task import TaskRecordCreate, TaskStatus, TaskPriority, TaskRecordUpdate
from services.common.models.role import RoleDefinitionCreate, AgentBindingCreate, AgentSessionBindingCreate, AgentSessionStatus
from services.common.models.capsule_complete import CapsuleDefinition, CapsuleStatus, CapsuleScope
from services.common.models.node_execution import NodeExecution, NodeExecutionStatus
from services.common.models.tool import ToolDefinition, ToolType, ToolInvocationRecord, ToolInvocationStatus
from services.orchestrator.app.models.schema import GraphWorkflowModel, WorkflowInstanceModel

# Mark as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
class TestE2EWorkflow:
    async def test_complete_workflow_cycle(self, async_db_session):
        """
        Test a complete end-to-end flow:
        Tenant -> Role -> Task -> Workflow -> Node -> Agent Session -> Tool -> Completion
        """
        # 1. SETUP: Tenant & Identity
        tenant = TenantRef(name=f"E2E Tenant {uuid.uuid4()}", status=TenantStatus.ACTIVE)
        async_db_session.add(tenant)
        await async_db_session.commit()
        await async_db_session.refresh(tenant)
        tenant_id = tenant.id

        user = PrincipalRef(
            tenant_id=tenant_id,
            principal_type=PrincipalType.USER,
            principal_id=f"user-e2e-{uuid.uuid4()}",
            display_name="E2E User",
            roles=["admin"]
        )
        async_db_session.add(user)
        
        agent01_ref = ExternalRef(
            tenant_id=tenant_id,
            system=ExternalSystem.SOMA_AGENT01,
            type="AGENT",
            external_id=f"agent01-{uuid.uuid4()}",
            meta_data={"capabilities": ["research"]}
        )
        async_db_session.add(agent01_ref)
        await async_db_session.commit()
        await async_db_session.refresh(agent01_ref)

        # 2. DEFINE: Role & Capsule
        capsule_def = CapsuleDefinition(
            tenant_id=tenant_id,
            name="E2E Capsule",
            status=CapsuleStatus.ACTIVE,
            allowed_tools=["search_tool"]
        )
        async_db_session.add(capsule_def)
        await async_db_session.commit()
        await async_db_session.refresh(capsule_def)

        role_service = RoleService(async_db_session) # Use sync session wrapper if needed, but here we use async session directly for setup
        # Note: RoleService is currently sync in implementation but we are in async test. 
        # For this test, we will insert Role/Binding directly via async session to avoid sync/async mix issues 
        # or we should update RoleService to be async. 
        # Given RoleService is sync, let's just use direct DB insertion for speed and correctness in this async test context.
        
        role = services.common.models.role.RoleDefinition(
            tenant_id=tenant_id,
            name="E2E Researcher",
            description="Researches things"
        )
        async_db_session.add(role)
        await async_db_session.commit()
        await async_db_session.refresh(role)

        binding = services.common.models.role.AgentBinding(
            tenant_id=tenant_id,
            role_id=role.id,
            agent01_agent_ref_id=agent01_ref.id,
            default_capsule_definition_id=capsule_def.id
        )
        async_db_session.add(binding)
        await async_db_session.commit()
        await async_db_session.refresh(binding)

        # 3. PLAN: Create Task
        task_service = TaskService(async_db_session)
        task_create = TaskRecordCreate(
            tenant_id=tenant_id,
            user_principal_id=user.id,
            source_application="e2e-test",
            original_request_text="Research quantum physics",
            task_type="research",
            priority=TaskPriority.HIGH
        )
        task = await task_service.create_task(task_create)
        assert task.status == TaskStatus.RECEIVED

        # 4. EXECUTE: Workflow & Node
        # Create Workflow Definition
        wf_def = GraphWorkflowModel(
            tenant_id=tenant_id,
            name="Research Workflow",
            definition={"nodes": [], "edges": []}
        )
        async_db_session.add(wf_def)
        await async_db_session.commit()
        await async_db_session.refresh(wf_def)

        # Create Workflow Instance
        wf_inst = WorkflowInstanceModel(
            tenant_id=tenant_id,
            workflow_id=wf_def.id,
            status="RUNNING",
            started_at=datetime.utcnow()
        )
        async_db_session.add(wf_inst)
        await async_db_session.commit()
        await async_db_session.refresh(wf_inst)

        # Link Task to Workflow
        await task_service.link_workflow_to_task(task.id, tenant_id, wf_inst.id)
        
        # Update Task Status
        await task_service.update_task_status(
            task.id, 
            tenant_id, 
            TaskRecordUpdate(status=TaskStatus.RUNNING, reason="Workflow started", actor_principal_id=user.id)
        )

        # Create Capsule Instance (Runtime)
        from services.common.models.capsule_complete import CapsuleInstance
        capsule_inst = CapsuleInstance(
            tenant_id=tenant_id,
            capsule_definition_id=capsule_def.id,
            capsule_definition_version=capsule_def.version,
            scope=CapsuleScope.NODE,
            scope_reference="node-1",
            effective_config={"timeout": 300}
        )
        async_db_session.add(capsule_inst)
        await async_db_session.commit()
        await async_db_session.refresh(capsule_inst)

        # Create Agent Session (Binding Node -> Agent)
        # Need a session ref for Agent01
        agent_session_ref = ExternalRef(
            tenant_id=tenant_id,
            system=ExternalSystem.SOMA_AGENT01,
            type="SESSION",
            external_id=f"session-{uuid.uuid4()}",
            meta_data={}
        )
        async_db_session.add(agent_session_ref)
        await async_db_session.commit()
        await async_db_session.refresh(agent_session_ref)

        agent_session = services.common.models.role.AgentSessionBinding(
            tenant_id=tenant_id,
            agent_binding_id=binding.id,
            workflow_instance_id=wf_inst.id,
            node_execution_id=None, # Will link next
            capsule_instance_id=capsule_inst.id,
            agent01_session_ref_id=agent_session_ref.id,
            status=AgentSessionStatus.OPEN
        )
        async_db_session.add(agent_session)
        await async_db_session.commit()
        await async_db_session.refresh(agent_session)

        # Create Node Execution
        node_exec = NodeExecution(
            tenant_id=tenant_id,
            workflow_instance_id=wf_inst.id,
            node_id="node-1",
            status=NodeExecutionStatus.RUNNING,
            agent_session_binding_id=agent_session.id,
            started_at=datetime.utcnow()
        )
        async_db_session.add(node_exec)
        await async_db_session.commit()
        await async_db_session.refresh(node_exec)

        # Update Session with Node Execution ID
        agent_session.node_execution_id = node_exec.id
        async_db_session.add(agent_session)

        # 5. TOOL: Tool Invocation
        # Create Tool Definition
        tool_def = ToolDefinition(
            tenant_id=tenant_id,
            name="search_tool",
            type=ToolType.NATIVE,
            description="Search the web"
        )
        async_db_session.add(tool_def)
        await async_db_session.commit()
        await async_db_session.refresh(tool_def)

        # Record Invocation
        tool_inv = ToolInvocationRecord(
            tenant_id=tenant_id,
            tool_definition_id=tool_def.id,
            workflow_instance_id=wf_inst.id,
            node_execution_id=node_exec.id,
            capsule_instance_id=capsule_inst.id,
            status=ToolInvocationStatus.SUCCEEDED,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        async_db_session.add(tool_inv)
        await async_db_session.commit()

        # 6. VERIFY
        # Verify Task History
        history = await task_service.get_task_history(task.id, tenant_id)
        assert len(history) >= 2
        assert history[-1].new_status == TaskStatus.RUNNING

        # Verify Node Execution
        assert node_exec.id is not None
        assert node_exec.agent_session_binding_id == agent_session.id

        # Verify Tool Invocation
        assert tool_inv.id is not None
        assert tool_inv.node_execution_id == node_exec.id
        assert tool_inv.capsule_instance_id == capsule_inst.id

import services.common.models.role # Import for direct access in test
