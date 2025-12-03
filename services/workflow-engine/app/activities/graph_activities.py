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
    async def save_checkpoint(self, workflow_id: str, node_id: str, state: Dict[str, Any]) -> str:
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
            
            stmt = select(WorkflowCheckpointModel).where(WorkflowCheckpointModel.id == checkpoint_uuid)
            result = await session.execute(stmt)
            checkpoint = result.scalar_one_or_none()
            
            if not checkpoint:
                raise ValueError(f"Checkpoint not found: {checkpoint_id}")
            
            return checkpoint.state_snapshot
