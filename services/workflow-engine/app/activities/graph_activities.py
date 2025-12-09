import logging
from typing import Dict, Any
from temporalio import activity
from sqlmodel import select

from services.orchestrator.app.database import get_async_session
from services.orchestrator.app.models.schema import WorkflowCheckpointModel

logger = logging.getLogger(__name__)


class GraphActivities:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory

    @activity.defn
    async def save_checkpoint(
        self, workflow_id: str, node_id: str, state: Dict[str, Any]
    ) -> str:
        """Save workflow checkpoint to DB"""
        logger.info(f"Saving checkpoint for workflow {workflow_id} at node {node_id}")

        async with get_async_session() as session:
            # workflow_id from Temporal is a string UUID
            import uuid

            instance_uuid = uuid.UUID(workflow_id)

            checkpoint = WorkflowCheckpointModel(
                instance_id=instance_uuid,
                node_id=node_id,
                state_snapshot=state,
            )
            session.add(checkpoint)
            await session.commit()
            await session.refresh(checkpoint)
            return str(checkpoint.id)

    @activity.defn
    async def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Load workflow state from checkpoint"""
        logger.info(f"Loading checkpoint {checkpoint_id}")

        async with get_async_session() as session:
            import uuid

            checkpoint_uuid = uuid.UUID(checkpoint_id)

            stmt = select(WorkflowCheckpointModel).where(
                WorkflowCheckpointModel.id == checkpoint_uuid
            )
            result = await session.execute(stmt)
            checkpoint = result.scalar_one_or_none()

            if not checkpoint:
                raise ValueError(f"Checkpoint not found: {checkpoint_id}")

            return checkpoint.state_snapshot

    @activity.defn
    async def record_node_execution_start(
        self,
        workflow_id: str,
        node_id: str,
        input_snapshot: Dict[str, Any],
        tenant_id: str,
    ) -> str:
        """Record start of node execution"""
        logger.info(
            f"Recording execution start for node {node_id} in workflow {workflow_id}"
        )

        async with get_async_session() as session:
            import uuid
            from datetime import datetime
            from services.common.models.node_execution import (
                NodeExecution,
                NodeExecutionStatus,
            )

            execution = NodeExecution(
                tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
                workflow_instance_id=uuid.UUID(workflow_id),
                node_id=node_id,
                status=NodeExecutionStatus.RUNNING,
                started_at=datetime.utcnow(),
                input_snapshot_ref=input_snapshot,  # Storing inline for now, could be ref
                attempt=1,  # TODO: Pass attempt number from retry policy
            )
            session.add(execution)
            await session.commit()
            await session.refresh(execution)
            return str(execution.id)

    @activity.defn
    async def record_node_execution_end(
        self,
        execution_id: str,
        status: str,
        output_snapshot: Dict[str, Any] = None,
        error_details: Dict[str, Any] = None,
    ) -> None:
        """Record end of node execution"""
        logger.info(f"Recording execution end for {execution_id} with status {status}")

        async with get_async_session() as session:
            import uuid
            from datetime import datetime
            from services.common.models.node_execution import (
                NodeExecution,
                NodeExecutionStatus,
            )

            stmt = select(NodeExecution).where(
                NodeExecution.id == uuid.UUID(execution_id)
            )
            result = await session.execute(stmt)
            execution = result.scalar_one_or_none()

            if not execution:
                logger.error(f"NodeExecution {execution_id} not found")
                return

            execution.status = NodeExecutionStatus(status)
            execution.ended_at = datetime.utcnow()

            if output_snapshot:
                execution.output_snapshot_ref = output_snapshot

            if error_details:
                execution.error_details = error_details

            await session.commit()
