"""
HITL Activities - Handles Human-in-the-Loop interactions
"""

import logging
import uuid
from typing import Dict, Any, Optional
from temporalio import activity
from sqlmodel import select

from services.orchestrator.app.database import get_async_session
from services.orchestrator.app.models.schema import HumanReviewSessionModel

logger = logging.getLogger(__name__)

class HITLActivities:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory

    @activity.defn
    async def create_human_review_session(self, workflow_id: str, node_id: str, payload: Dict[str, Any]) -> str:
        """Create a human review session record in DB"""
        logger.info(f"Creating human review session for workflow {workflow_id} at node {node_id}")
        
        async with get_async_session() as session:
            import uuid
            instance_uuid = uuid.UUID(workflow_id)
            
            review_session = HumanReviewSessionModel(
                instance_id=instance_uuid,
                node_id=node_id,
                payload=payload,
                status="PENDING"
            )
            session.add(review_session)
            await session.commit()
            await session.refresh(review_session)
            return str(review_session.id)

    @activity.defn
    async def get_human_review_status(self, session_id: str) -> Dict[str, Any]:
        """Check status of a human review session"""
        async with get_async_session() as session:
            import uuid
            session_uuid = uuid.UUID(session_id)
            
            stmt = select(HumanReviewSessionModel).where(HumanReviewSessionModel.id == session_uuid)
            result = await session.execute(stmt)
            review_session = result.scalar_one_or_none()
            
            if not review_session:
                raise ValueError(f"Review session not found: {session_id}")
            
            return {
                "status": review_session.status,
                "resolved_at": str(review_session.resolved_at) if review_session.resolved_at else None
            }
