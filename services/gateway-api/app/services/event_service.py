"""Event emission service for gateway endpoints."""

import logging
from typing import Any, Dict
from uuid import UUID

from services.common.events.publisher import EventPublisher
from services.orchestrator.app.repository.outbox import OutboxEventRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GatewayEventService:
    """Service for emitting domain events from gateway operations."""

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher):
        self.session = session
        self.event_publisher = event_publisher
        self.outbox_repo = OutboxEventRepository(session)

    async def emit_wizard_approved(
        self,
        session_id: str,
        user_id: str,
        workflow_id: str,
        campaign_name: str,
        estimated_cost: float = 0.0,
    ) -> None:
        """Emit wizard approval event.

        Args:
            session_id: The wizard session ID
            user_id: The user who approved the wizard
            workflow_id: The orchestrator workflow ID
            campaign_name: The campaign name from wizard
            estimated_cost: Estimated execution cost
        """
        event_data = {
            "session_id": session_id,
            "user_id": user_id,
            "workflow_id": workflow_id,
            "campaign_name": campaign_name,
            "estimated_cost": estimated_cost,
            "approved_at": None,  # Will be set by outbox
            "metadata": {"source": "gateway", "event_version": "v1"},
        }

        try:
            # Save to outbox for durability
            await self.outbox_repo.save_event(event_type="gateway.wizard_approved.v1", event_data=event_data)

            logger.info(f"Emitted wizard approved event: {session_id} -> {workflow_id}")

        except Exception as e:
            logger.exception(f"Failed to emit wizard approved event: {e}")
            raise

    async def emit_wizard_rejected(self, session_id: str, user_id: str, reason: str, campaign_name: str) -> None:
        """Emit wizard rejection event.

        Args:
            session_id: The wizard session ID
            user_id: The user who rejected the wizard
            reason: Rejection reason
            campaign_name: The campaign name
        """
        event_data = {
            "session_id": session_id,
            "user_id": user_id,
            "reason": reason,
            "campaign_name": campaign_name,
            "rejected_at": None,  # Will be set by outbox
            "metadata": {"source": "gateway", "event_version": "v1"},
        }

        try:
            # Save to outbox for durability
            await self.outbox_repo.save_event(event_type="gateway.wizard_rejected.v1", event_data=event_data)

            logger.info(f"Emitted wizard rejected event: {session_id}")

        except Exception as e:
            logger.exception(f"Failed to emit wizard rejected event: {e}")
            raise

    async def emit_budget_exceeded(
        self,
        session_id: str,
        user_id: str,
        budget_cap: float,
        estimated_cost: float,
        campaign_name: str,
    ) -> None:
        """Emit budget exceeded event.

        Args:
            session_id: The wizard session ID
            user_id: The user whose budget was exceeded
            budget_cap: The budget limit
            estimated_cost: The exceeded cost
            campaign_name: The campaign name
        """
        event_data = {
            "session_id": session_id,
            "user_id": user_id,
            "budget_cap": budget_cap,
            "estimated_cost": estimated_cost,
            "campaign_name": campaign_name,
            "exceeded_at": None,  # Will be set by outbox
            "metadata": {"source": "gateway", "event_version": "v1"},
        }

        try:
            # Save to outbox for durability
            await self.outbox_repo.save_event(event_type="gateway.budget_exceeded.v1", event_data=event_data)

            logger.info(f"Emitted budget exceeded event: {session_id}")

        except Exception as e:
            logger.exception(f"Failed to emit budget exceeded event: {e}")
            raise
