"""Event emission service for orchestrator operations."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..repository.outbox_event_repository import OutboxEventRepository
from services.common.events.publisher import EventPublisher
from sqlalchemy.ext.asyncio import AsyncSession
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class OrchestratorEventService:
    """Service for emitting domain events from orchestrator operations.

    ``event_publisher`` is optional – many internal activities only need to
    persist the event to the outbox.  When a real ``EventPublisher`` is
    provided the event will also be sent to Kafka.
    """

    def __init__(self, session: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.session = session
        self.event_publisher = event_publisher
        self.outbox_repo = OutboxEventRepository(session)

    async def emit_orchestration_started(
  self,
  workflow_id: str,
  tenant: str,
  initiator: str,
  directives: List[Dict[str, Any]],
  metadata: Dict[str, Any],
  ) -> None:
      """Emit orchestration started event.

      Args:
          workflow_id: The orchestrator workflow ID
          tenant: The tenant identifier
          initiator: The user who initiated the workflow
          directives: List of orchestration directives
          metadata: Additional workflow metadata
          """
          event_data = {
          "workflow_id": workflow_id,
          "tenant": tenant,
          "initiator": initiator,
          "directives": directives,
          "metadata": {
          **metadata,
          "source": "orchestrator",
          "event_version": "v1",
          "directives_count": len(directives),
          "agent_count": len(set(d["agent_id"] for d in directives)),
          },
          }

          try:
# Save to outbox for durability
              await self.outbox_repo.save_event(
              event_type="orchestration.started.v1", event_data=event_data
              )

              logger.info(f"Emitted orchestration started event: {workflow_id}")

              except Exception as e:
                  logger.exception(f"Failed to emit orchestration started event: {e}")
                  raise

    async def emit_orchestration_completed(
                  self,
                  workflow_id: str,
                  tenant: str,
                  initiator: str,
                  status: str,
                  results: Dict[str, Any],
                  duration_seconds: float,
                  metadata: Dict[str, Any],
                  ) -> None:
                      """Emit orchestration completed event.

                      Args:
                          workflow_id: The orchestrator workflow ID
                          tenant: The tenant identifier
                          initiator: The user who initiated the workflow
                          status: Final status (success, failed, cancelled)
                          results: Workflow execution results
                          duration_seconds: Total execution duration
                          metadata: Additional workflow metadata
                          """
                          event_data = {
                          "workflow_id": workflow_id,
                          "tenant": tenant,
                          "initiator": initiator,
                          "status": status,
                          "results": results,
                          "duration_seconds": duration_seconds,
                          "metadata": {
                          **metadata,
                          "source": "orchestrator",
                          "event_version": "v1",
                          "completed_at": None,  # Will be set by outbox
                          },
                          }

                          try:
# Save to outbox for durability
                              await self.outbox_repo.save_event(
                              event_type="orchestration.completed.v1", event_data=event_data
                              )

                              logger.info(
                              f"Emitted orchestration completed event: {workflow_id} ({status})"
                              )

                              except Exception as e:
                                  logger.exception(f"Failed to emit orchestration completed event: {e}")
                                  raise

    async def emit_orchestration_failed(
                                  self,
                                  workflow_id: str,
                                  tenant: str,
                                  initiator: str,
                                  error: str,
                                  failed_step: str,
                                  metadata: Dict[str, Any],
                                  ) -> None:
                                      """Emit orchestration failed event.

                                      Args:
                                          workflow_id: The orchestrator workflow ID
                                          tenant: The tenant identifier
                                          initiator: The user who initiated the workflow
                                          error: Error message
                                          failed_step: Which step/agent failed
                                          metadata: Additional workflow metadata
                                          """
                                          event_data = {
                                          "workflow_id": workflow_id,
                                          "tenant": tenant,
                                          "initiator": initiator,
                                          "error": error,
                                          "failed_step": failed_step,
                                          "metadata": {
                                          **metadata,
                                          "source": "orchestrator",
                                          "event_version": "v1",
                                          "failed_at": None,  # Will be set by outbox
                                          },
                                          }

                                          try:
# Save to outbox for durability
                                              await self.outbox_repo.save_event(
                                              event_type="orchestration.failed.v1", event_data=event_data
                                              )

                                              logger.error(f"Emitted orchestration failed event: {workflow_id} - {error}")

                                              except Exception as e:
                                                  logger.exception(f"Failed to emit orchestration failed event: {e}")
                                                  raise

    async def emit_agent_completed(
 self,
 workflow_id: str,
 agent_id: str,
 task_id: str,
 status: str,
 result: Dict[str, Any],
 duration_seconds: float,
 metadata: Dict[str, Any],
 ) -> None:
 """Emit individual agent completion event.

 Args:
 workflow_id: The orchestrator workflow ID
 agent_id: The agent that completed the task
 task_id: The specific task identifier
 status: Task completion status
 result: Task execution result
 duration_seconds: Task execution duration
 metadata: Additional task metadata
 """
 event_data = {
  "workflow_id": workflow_id,
  "agent_id": agent_id,
  "task_id": task_id,
  "status": status,
  "result": result,
  "duration_seconds": duration_seconds,
  "metadata": {**metadata, "source": "orchestrator", "event_version": "v1"},
 }

 try:
  # Save to outbox for durability
  await self.outbox_repo.save_event(
   event_type="orchestrator.agent_completed.v1", event_data=event_data
  )

  logger.info(f"Emitted agent completed event: {workflow_id}/{agent_id}")

 except Exception as e:
  logger.exception(f"Failed to emit agent completed event: {e}")
  raise

# ---------------------------------------------------------------------
# VC step emission (governed by allow_rl_training_data flag)
# ---------------------------------------------------------------------
    async def emit_vc_step(
 self,
 episode_id: str,
 step_index: int,
 role: str,
 reward: float,
 metadata: Optional[Dict[str, Any]] = None,
 ) -> None:
 """Emit a ``vc.step.v1`` outbox event for a V‑C step.

 The orchestrator settings contain ``allow_rl_training_data`` – if it is
 False the event is not persisted, ensuring compliance with tenant policy.
 """
 from ..core.config import settings

 if not settings.allow_rl_training_data:
  logger.info(
   "RL training data emission disabled – skipping VC_STEP event",
   episode_id=episode_id,
   step_index=step_index,
  )
  return

 event_data: Dict[str, Any] = {
  "episode_id": episode_id,
  "step_index": step_index,
  "role": role,
  "reward": reward,
  **(metadata or {}),
 }

 await self.outbox_repo.save_event(event_type="vc.step.v1", event_data=event_data)
 logger.info(
  "Emitted VC_STEP event",
  episode_id=episode_id,
  step_index=step_index,
  role=role,
 )
