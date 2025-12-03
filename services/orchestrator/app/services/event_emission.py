"""
Centralized event emission service for orchestrator events.

Provides real integration with the outbox pattern for reliable event delivery.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..planner.schemas import ProjectPlan
from ..repository.outbox_event_repository import OutboxEventRepository


class EventEmissionService:
    """Service for emitting domain events using the outbox pattern."""

    def __init__(self, session: AsyncSession):
        self.outbox_repo = OutboxEventRepository(session)

    async def emit_plan_created_event(
        self,
        plan: ProjectPlan,
        session_id: str | None = None,
        initiator: str | None = None,
    ) -> None:
        """Emit plan created event with real data.

        Args:
            plan: The created project plan
            session_id: Original wizard session ID
            initiator: User who initiated the plan creation
        """
        event_data = {
            "plan_id": plan.plan_id,
            "tenant": plan.tenant,
            "session_id": session_id,
            "initiator": initiator or "system",
            "objective": plan.objective,
            "modules": [
                {
                    "module_id": m.module_id,
                    "agent_id": m.agent_id,
                    "goal": m.goal,
                    "dependencies": m.dependencies,
                }
                for m in plan.modules
            ],
            "modules_count": len(plan.modules),
            "created_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.plan_created",
            topic="orchestrator.events",
            key=str(plan.plan_id),
            payload=event_data,
        )

    async def emit_plan_refined_event(
        self,
        plan_id: str,
        tenant: str,
        changes: dict[str, Any],
        initiator: str | None = None,
    ) -> None:
        """Emit plan refinement event.

        Args:
            plan_id: The plan ID being refined
            tenant: Tenant identifier
            changes: Dictionary of changes made
            initiator: User who made the changes
        """
        event_data = {
            "plan_id": plan_id,
            "tenant": tenant,
            "initiator": initiator or "system",
            "changes": changes,
            "refined_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.plan_refined",
            topic="orchestrator.events",
            key=str(plan_id),
            payload=event_data,
        )

    async def emit_build_run_started_event(
        self,
        build_run_id: str,
        tenant: str,
        project_id: str,
        workflow_type: str,
        agent_ids: list[str],
    ) -> None:
        """Emit build run started event.

        Args:
            build_run_id: The build run identifier
            tenant: Tenant identifier
            project_id: Associated project ID
            workflow_type: Type of workflow being executed
            agent_ids: List of agent IDs involved
        """
        event_data = {
            "build_run_id": build_run_id,
            "tenant": tenant,
            "project_id": project_id,
            "workflow_type": workflow_type,
            "agent_ids": agent_ids,
            "started_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.build_run_started",
            topic="orchestrator.events",
            key=str(build_run_id),
            payload=event_data,
        )

    async def emit_build_run_completed_event(
        self,
        build_run_id: str,
        tenant: str,
        status: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Emit build run completed event.

        Args:
            build_run_id: The build run identifier
            tenant: Tenant identifier
            status: Final status (completed/failed)
            duration_seconds: Duration of the build run
            success: Whether the build completed successfully
        """
        event_data = {
            "build_run_id": build_run_id,
            "tenant": tenant,
            "status": status,
            "duration_seconds": duration_seconds,
            "success": success,
            "completed_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.build_run_completed",
            topic="orchestrator.events",
            key=str(build_run_id),
            payload=event_data,
        )

    async def emit_agent_status_changed_event(
        self,
        agent_id: str,
        plan_id: str,
        old_status: str,
        new_status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit agent status change event.

        Args:
            agent_id: The agent identifier
            plan_id: Associated plan ID
            old_status: Previous status
            new_status: New status
            metadata: Additional metadata
        """
        event_data = {
            "agent_id": agent_id,
            "plan_id": plan_id,
            "old_status": old_status,
            "new_status": new_status,
            "metadata": metadata or {},
            "changed_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.agent_status_changed",
            topic="orchestrator.events",
            key=str(agent_id),
            payload=event_data,
        )

    async def emit_budget_evaluation_event(
        self,
        build_run_id: str,
        tenant: str,
        budget_cap: float,
        estimated_cost: float,
        evaluation_result: str,
    ) -> None:
        """Emit budget evaluation event.

        Args:
            build_run_id: The build run identifier
            tenant: Tenant identifier
            budget_cap: Budget limit
            estimated_cost: Estimated cost
            evaluation_result: Evaluation result (approved/rejected)
        """
        event_data = {
            "build_run_id": build_run_id,
            "tenant": tenant,
            "budget_cap": budget_cap,
            "estimated_cost": estimated_cost,
            "evaluation_result": evaluation_result,
            "evaluated_at": datetime.now(UTC).isoformat(),
        }

        await self.outbox_repo.create_event(
            event_type="orchestration.budget_evaluation",
            topic="orchestrator.events",
            key=str(build_run_id),
            payload=event_data,
        )
