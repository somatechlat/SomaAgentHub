"""Temporal workflow scaffolding for persona rentals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass
class PersonaRentalRequest:
    rental_id: str
    tenant: str
    persona_id: str
    model_box_id: str
    renter: str
    duration_minutes: int = 10
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonaRentalResult:
    rental_id: str
    tenant: str
    persona_id: str
    status: str
    started_at: str
    ended_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Activities (placeholders for future integrations)
# ---------------------------------------------------------------------------


@activity.defn(name="persona-rental.begin")
async def begin_rental(request: PersonaRentalRequest) -> Dict[str, Any]:
    """Reserve entitlements, create session scaffolding, and emit audit events."""

    activity.logger.info(
        "Beginning persona rental",
        extra={
            "rental_id": request.rental_id,
            "tenant": request.tenant,
            "persona_id": request.persona_id,
            "model_box_id": request.model_box_id,
            "renter": request.renter,
        },
    )
    # Placeholder payload mirrors what future marketplace events will emit.
    return {
        "rental_id": request.rental_id,
        "status": "started",
    }


@activity.defn(name="persona-rental.cleanup")
async def cleanup_rental(request: PersonaRentalRequest) -> Dict[str, Any]:
    """Release entitlements, emit completion events, and persist billing usage."""

    activity.logger.info(
        "Cleaning up persona rental",
        extra={
            "rental_id": request.rental_id,
            "tenant": request.tenant,
            "persona_id": request.persona_id,
            "model_box_id": request.model_box_id,
        },
    )
    return {
        "rental_id": request.rental_id,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------


@workflow.defn(name="persona-rental-workflow")
class PersonaRentalWorkflow:
    """Coordinates timed persona rentals via Temporal timers."""

    @workflow.run
    async def run(self, request: PersonaRentalRequest) -> PersonaRentalResult:
        logger = workflow.logger
        logger.info("Starting persona rental", rental_id=request.rental_id)

        start_payload = await workflow.execute_activity(
            begin_rental,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )

        await workflow.sleep(timedelta(minutes=request.duration_minutes))

        end_payload = await workflow.execute_activity(
            cleanup_rental,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info("Completed persona rental", rental_id=request.rental_id)
        return PersonaRentalResult(
            rental_id=request.rental_id,
            tenant=request.tenant,
            persona_id=request.persona_id,
            status=end_payload.get("status", "completed"),
            started_at=str(workflow.now()),
            ended_at=str(workflow.now()),
            metadata={
                "begin": start_payload,
                "end": end_payload,
                "duration_minutes": request.duration_minutes,
            },
        )
