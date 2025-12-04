import pytest
import uuid
from datetime import datetime
from services.common.models.identity import TenantRef, TenantStatus
from services.common.models.capsule_complete import CapsuleDefinition, CapsuleStatus, CapsuleScope, CapsuleInstance
from services.common.models.rl import TrajectoryRecord, TrajectoryOutcome
from services.orchestrator.app.models.schema import GraphWorkflowModel, WorkflowInstanceModel

# Mark as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
class TestRLTrajectory:
    async def test_trajectory_recording(self, async_db_session):
        """Test creating and retrieving RL trajectories"""
        
        # 1. Setup Context
        tenant = TenantRef(name=f"RL Tenant {uuid.uuid4()}", status=TenantStatus.ACTIVE)
        async_db_session.add(tenant)
        await async_db_session.commit()
        await async_db_session.refresh(tenant)
        tenant_id = tenant.id

        wf_def = GraphWorkflowModel(
            tenant_id=tenant_id,
            name="RL Workflow",
            definition={}
        )
        async_db_session.add(wf_def)
        await async_db_session.commit()
        await async_db_session.refresh(wf_def)

        wf_inst = WorkflowInstanceModel(
            tenant_id=tenant_id,
            workflow_id=wf_def.id,
            status="COMPLETED",
            started_at=datetime.utcnow()
        )
        async_db_session.add(wf_inst)
        await async_db_session.commit()
        await async_db_session.refresh(wf_inst)

        capsule_def = CapsuleDefinition(
            tenant_id=tenant_id,
            name="RL Capsule",
            status=CapsuleStatus.ACTIVE
        )
        async_db_session.add(capsule_def)
        await async_db_session.commit()
        await async_db_session.refresh(capsule_def)

        capsule_inst = CapsuleInstance(
            tenant_id=tenant_id,
            capsule_definition_id=capsule_def.id,
            capsule_definition_version=capsule_def.version,
            scope=CapsuleScope.WORKFLOW,
            scope_reference=str(wf_inst.id),
            effective_config={}
        )
        async_db_session.add(capsule_inst)
        await async_db_session.commit()
        await async_db_session.refresh(capsule_inst)

        # 2. Create Trajectory Record
        traj = TrajectoryRecord(
            tenant_id=tenant_id,
            workflow_instance_id=wf_inst.id,
            capsule_instance_id=capsule_inst.id,
            final_outcome=TrajectoryOutcome.CORRECT,
            global_reward=1.0,
            role_returns={"solver": 0.8, "verifier": 0.2},
            meta={"difficulty": "hard"},
            storage_ref="s3://bucket/traj-123.json"
        )
        async_db_session.add(traj)
        await async_db_session.commit()
        await async_db_session.refresh(traj)

        # 3. Verify
        assert traj.id is not None
        assert traj.global_reward == 1.0
        assert traj.role_returns["solver"] == 0.8
