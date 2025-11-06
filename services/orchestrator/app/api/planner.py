# Planner API endpoints for the orchestrator service.
# Provides thin HTTP wrappers around the internal PlannerService.

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..planner.planner_service import PlannerService
from ..planner.client import PlannerClient, PlannerClientConfig
from ..planner.schemas import PlannerRequest, PlannerContext, ProjectPlan
from ..repository.plan_repository import PlanRepository
from services.common.observability import get_tracer
from opentelemetry.trace import Status, StatusCode

router = APIRouter(prefix="/v1/planner", tags=["planner"])

# Helper – create a singleton service instance. In a real deployment you would
# inject configuration from `settings`; for now we use the default SLM port.
_client = PlannerClient(PlannerClientConfig(model="10022"))
_service = PlannerService(client=_client)
_repo = PlanRepository()

# Obtain a tracer for the planner routes. The orchestrator service already
# initializes OpenTelemetry via ``setup_observability`` in ``main.py``.
_tracer = get_tracer("planner-api")

# ---------------------------------------------------------------------------
# Parallel batch generation support
# ---------------------------------------------------------------------------
# The batch endpoint accepts a list of payloads and runs the individual
# ``generate_plan`` calls concurrently using ``asyncio.gather``. This showcases
# how the service can handle parallel work without blocking the event loop.
# ---------------------------------------------------------------------------
import asyncio

class GeneratePlanPayload(BaseModel):
    """Payload for the /generate endpoint.

    `request` contains the user‑level intent, while `context` supplies the
    surrounding environment (available tools, memory snippets, etc.). Both are
    required for a meaningful plan.
    """
    request: PlannerRequest
    context: PlannerContext


class BatchGeneratePayload(BaseModel):
    """A list of generate‑plan requests for parallel processing."""

    requests: list[GeneratePlanPayload]

@router.post("/generate", response_model=ProjectPlan, status_code=status.HTTP_201_CREATED)
async def generate_plan(payload: GeneratePlanPayload) -> ProjectPlan:
    """Generate a new project plan.

    Delegates to `PlannerService.generate_plan` and returns the persisted
    `ProjectPlan`. Validation errors are returned as HTTP 400.
    """
    with _tracer.start_as_current_span("generate_plan_endpoint") as span:
        try:
            plan = await _service.generate_plan(payload.request, payload.context)
            span.set_attribute("plan.id", plan.plan_id)
            span.set_attribute("plan.tenant", plan.tenant)
            return plan
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batch/generate", response_model=list[ProjectPlan], status_code=status.HTTP_201_CREATED)
async def batch_generate(payload: BatchGeneratePayload) -> list[ProjectPlan]:
    """Generate multiple plans in parallel.

    The endpoint receives a list of ``GeneratePlanPayload`` objects and runs the
    underlying ``PlannerService.generate_plan`` concurrently using ``asyncio.gather``.
    The response is a list of ``ProjectPlan`` objects preserving the input order.
    """
    with _tracer.start_as_current_span("batch_generate_plan_endpoint") as span:
        try:
            # Build a coroutine for each request.
            coros = [_service.generate_plan(req.request, req.context) for req in payload.requests]
            results = await asyncio.gather(*coros, return_exceptions=False)
            # Attach some batch metrics to the span.
            span.set_attribute("batch.size", len(payload.requests))
            return results
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise HTTPException(status_code=400, detail=str(exc)) from exc

class RefinePlanPayload(BaseModel):
    """Payload for the /refine endpoint.

    `plan_id` identifies the plan to refine, `updates` contains the fields
    the user changed, and an optional `context` can be supplied for additional
    information.
    """
    plan_id: str = Field(..., description="Identifier of the plan to refine")
    updates: dict = Field(..., description="Partial fields to merge into the plan")
    context: PlannerContext | None = None

@router.post("/refine", response_model=ProjectPlan)
async def refine_plan(payload: RefinePlanPayload) -> ProjectPlan:
    """Refine an existing plan with user‑provided updates.

    The existing plan is fetched, merged with ``updates`` and sent through the
    LLM for a new suggestion. The refreshed plan replaces the previous record.
    """
    existing = await _repo.get_plan(payload.plan_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        current_plan = ProjectPlan.parse_obj(existing.payload)
    except Exception as exc:
        # Stored JSON is malformed – treat as server error.
        raise HTTPException(status_code=500, detail="Corrupted plan data") from exc

    with _tracer.start_as_current_span("refine_plan_endpoint") as span:
        try:
            refined = await _service.refine_plan(
                current_plan,
                payload.updates,
                context=payload.context,
            )
            span.set_attribute("plan.id", refined.plan_id)
            span.set_attribute("plan.tenant", refined.tenant)
            return refined
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{plan_id}", response_model=ProjectPlan)
async def get_plan(plan_id: str) -> ProjectPlan:
    """Fetch a persisted plan by its identifier."""
    plan = await _repo.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return ProjectPlan.parse_obj(plan.payload)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: str) -> None:
    """Delete a plan from the database."""
    await _repo.delete_plan(plan_id)
    # FastAPI automatically returns 204 No Content.