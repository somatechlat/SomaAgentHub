import pytest
import uuid
from datetime import datetime
from services.common.models.identity import TenantRef, PrincipalRef, TenantStatus, PrincipalType
from services.common.models.hitl import HumanReviewerAssignment, HumanDecisionRecord, ReviewerAssignmentStatus, ReviewDecision
from services.orchestrator.app.models.schema import GraphWorkflowModel, WorkflowInstanceModel, HumanReviewSessionModel

# Mark as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
class TestHITLFlow:
    async def test_hitl_lifecycle(self, async_db_session):
        """Test HITL session, assignment, and decision"""
        
        # 1. Setup Context
        tenant = TenantRef(name=f"HITL Tenant {uuid.uuid4()}", status=TenantStatus.ACTIVE)
        async_db_session.add(tenant)
        await async_db_session.commit()
        await async_db_session.refresh(tenant)
        tenant_id = tenant.id

        reviewer = PrincipalRef(
            tenant_id=tenant_id,
            principal_type=PrincipalType.USER,
            principal_id=f"reviewer-{uuid.uuid4()}",
            display_name="Reviewer Bob",
            roles=["reviewer"]
        )
        async_db_session.add(reviewer)
        await async_db_session.commit()
        await async_db_session.refresh(reviewer)

        wf_def = GraphWorkflowModel(
            tenant_id=tenant_id,
            name="HITL Workflow",
            definition={}
        )
        async_db_session.add(wf_def)
        await async_db_session.commit()
        await async_db_session.refresh(wf_def)

        wf_inst = WorkflowInstanceModel(
            tenant_id=tenant_id,
            workflow_id=wf_def.id,
            status="WAITING_FOR_HUMAN",
            started_at=datetime.utcnow()
        )
        async_db_session.add(wf_inst)
        await async_db_session.commit()
        await async_db_session.refresh(wf_inst)

        # 2. Create Review Session
        session = HumanReviewSessionModel(
            tenant_id=tenant_id,
            instance_id=wf_inst.id,
            node_id="approval-node",
            payload={"risk_score": 0.9},
            status="PENDING"
        )
        async_db_session.add(session)
        await async_db_session.commit()
        await async_db_session.refresh(session)

        # 3. Assign Reviewer
        assignment = HumanReviewerAssignment(
            tenant_id=tenant_id,
            review_session_id=session.id,
            reviewer_principal_id=reviewer.id,
            status=ReviewerAssignmentStatus.ASSIGNED
        )
        async_db_session.add(assignment)
        await async_db_session.commit()
        await async_db_session.refresh(assignment)

        # 4. Make Decision
        decision = HumanDecisionRecord(
            tenant_id=tenant_id,
            review_session_id=session.id,
            reviewer_principal_id=reviewer.id,
            decision=ReviewDecision.APPROVE,
            comment="Looks good to me"
        )
        async_db_session.add(decision)
        
        # Update session status
        session.status = "APPROVED"
        session.resolved_at = datetime.utcnow()
        
        await async_db_session.commit()
        await async_db_session.refresh(decision)

        # 5. Verify
        assert decision.id is not None
        assert decision.decision == ReviewDecision.APPROVE
        assert session.status == "APPROVED"
