# Planner API endpoints for the orchestrator service.
# Provides thin HTTP wrappers around the internal PlannerService.

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel, Field
from typing import List

from ..planner.planner_service import PlannerService
from ..planner.client import PlannerClient, PlannerClientConfig
from ..planner.schemas import PlannerRequest, PlannerContext, ProjectPlan
from ..repository.plan_repository import PlanRepository
from services.common.observability import get_tracer
from opentelemetry.trace import Status, StatusCode
from ..metrics.planner import (
    planner_generate_requests,
    planner_refine_requests,
    planner_latency_seconds,
    planner_list_requests,
    planner_batch_refine_requests,
    planner_get_requests,
    planner_delete_requests,
)
from services.common.opa_client import get_opa_client

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
    # Record metric for a single generate request
    # Authorize the request via OPA – tenant is in the payload request.
    opa = get_opa_client()
    authorized = await opa.check_authorization(
        tenant_id=payload.request.tenant,
        user_id="system",  # In a real deployment this would be extracted from auth headers.
        action="create_plan",
        resource="planner",
        context={},
    )
    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized to generate plan")

    planner_generate_requests.labels(method="single").inc()
    with planner_latency_seconds.labels(endpoint="generate").time():
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
    # Increment metric for each individual generation in the batch.
    planner_generate_requests.labels(method="batch").inc(len(payload.requests))
    with planner_latency_seconds.labels(endpoint="batch_generate").time():
        with _tracer.start_as_current_span("batch_generate_plan_endpoint") as span:
            try:
                coros = [_service.generate_plan(req.request, req.context) for req in payload.requests]
                results = await asyncio.gather(*coros, return_exceptions=False)
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


class BatchRefinePayload(BaseModel):
    """Payload for batch refine requests.

    Contains a list of ``RefinePlanPayload`` objects that will be processed in
    parallel. The response preserves the order of the input list.
    """

    requests: List[RefinePlanPayload]

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

    # Record metric for refine request
    # Authorize refinement – need tenant from existing plan.
    if existing is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    # Extract tenant from stored payload.
    stored_plan = ProjectPlan.parse_obj(existing.payload)
    opa = get_opa_client()
    authorized = await opa.check_authorization(
        tenant_id=stored_plan.tenant,
        user_id="system",
        action="refine_plan",
        resource="planner",
        context={},
    )
    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized to refine plan")

    planner_refine_requests.inc()
    with planner_latency_seconds.labels(endpoint="refine").time():
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


# The ``/list`` endpoint must be defined *before* the dynamic ``/{plan_id}``
# route to avoid the latter capturing the literal ``list`` path segment.
@router.get("/list", response_model=List[ProjectPlan])
async def list_plans() -> List[ProjectPlan]:
    """Return a list of all persisted plans.

    This endpoint is useful for UI dashboards or admin tooling to view the
    current set of stored project plans.
    """
    # List operation – authorize using a generic tenant (could be admin).
    opa = get_opa_client()
    authorized = await opa.check_authorization(
        tenant_id="admin",
        user_id="system",
        action="list_plans",
        resource="planner",
        context={},
    )
    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized to list plans")

    planner_list_requests.inc()
    with planner_latency_seconds.labels(endpoint="list").time():
        records = await _repo.list_plans()
        return [ProjectPlan.parse_obj(rec.payload) for rec in records]


@router.get("/{plan_id}", response_model=ProjectPlan)
async def get_plan(plan_id: str) -> ProjectPlan:
    """Fetch a persisted plan by its identifier."""
    # Record metric for get request
    planner_get_requests.inc()
    plan = await _repo.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return ProjectPlan.parse_obj(plan.payload)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: str) -> Response:
    """Delete a plan from the database.

    Returns a ``Response`` with status 204 and an empty body to satisfy
    FastAPI's requirement that 204 responses must not include a body.
    """
    # Record metric for delete request
    planner_delete_requests.inc()
    await _repo.delete_plan(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/batch/refine", response_model=List[ProjectPlan])
async def batch_refine(payload: BatchRefinePayload) -> List[ProjectPlan]:
    """Refine multiple plans in parallel.

    Each ``RefinePlanPayload`` is processed concurrently using ``asyncio.gather``.
    The endpoint returns a list of refined ``ProjectPlan`` objects in the same
    order as the input requests.
    """
    # Increment metric for batch refine (count each item processed)
    # Authorize batch refine – using admin tenant for simplicity.
    opa = get_opa_client()
    authorized = await opa.check_authorization(
        tenant_id="admin",
        user_id="system",
        action="batch_refine",
        resource="planner",
        context={},
    )
    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized to batch refine plans")

    planner_batch_refine_requests.labels(method="batch").inc(len(payload.requests))
    with planner_latency_seconds.labels(endpoint="batch_refine").time():
        async def _process(req: RefinePlanPayload) -> ProjectPlan:
            # Fetch existing plan
            existing = await _repo.get_plan(req.plan_id)
            if existing is None:
                raise HTTPException(status_code=404, detail=f"Plan {req.plan_id} not found")
            try:
                current_plan = ProjectPlan.parse_obj(existing.payload)
            except Exception as exc:
                raise HTTPException(status_code=500, detail="Corrupted plan data") from exc
            refined = await _service.refine_plan(
                current_plan,
                req.updates,
                context=req.context,
            )
            return refined

        coros = [_process(req) for req in payload.requests]
        results = await asyncio.gather(*coros, return_exceptions=False)
        return results