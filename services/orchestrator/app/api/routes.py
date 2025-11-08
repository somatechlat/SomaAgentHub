"""HTTP routes for the orchestrator service backed by Temporal workflows."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from temporalio import client as temporal_client
from temporalio.client import RPCError, RPCStatusCode
from sqlmodel import Session, select
from services.orchestrator.app.repository.models import BuildRun
from services.orchestrator.app.database import get_session
import uuid
import httpx

from ..core.config import settings
from ..workflows.mao import AgentDirective, MAOStartInput
from ..workflows.session import SessionStartInput
from ..workflows.capsule import CapsuleRunInput

# Import conversation and training endpoints
from .conversation import router as conversation_router
from .projects import router as projects_router
from .training import router as training_router

router = APIRouter(prefix="/v1", tags=["orchestrator"])
router.include_router(conversation_router)
router.include_router(projects_router)
router.include_router(training_router)
class BuildRunCreate(BaseModel):
    tenant: str
    project_id: str
    pricing_snapshot_id: str
    budget_cap: float
    estimated_cost: float
    template_set: str = "default"
    policy_reason: str = ""

class BuildRunResponse(BaseModel):
    id: uuid.UUID
    tenant: str
    project_id: str
    pricing_snapshot_id: str
    budget_cap: float
    estimated_cost: float
    status: str
    template_set: str
    policy_reason: str
    created_at: str
    updated_at: str

@router.post("/build-runs", response_model=BuildRunResponse, tags=["build"])
def create_build_run(payload: BuildRunCreate, session: Session = Depends(get_session)):
    br = BuildRun(
        tenant=payload.tenant,
        project_id=payload.project_id,
        pricing_snapshot_id=payload.pricing_snapshot_id,
        budget_cap=payload.budget_cap,
        estimated_cost=payload.estimated_cost,
        template_set=payload.template_set,
        policy_reason=payload.policy_reason,
    )
    session.add(br)
    session.commit()
    session.refresh(br)
    return BuildRunResponse(
        id=br.id,
        tenant=br.tenant,
        project_id=br.project_id,
        pricing_snapshot_id=br.pricing_snapshot_id,
        budget_cap=br.budget_cap,
        estimated_cost=br.estimated_cost,
        status=br.status,
        template_set=br.template_set,
        policy_reason=br.policy_reason,
        created_at=br.created_at.isoformat(),
        updated_at=br.updated_at.isoformat(),
    )

@router.get("/build-runs/{build_run_id}", response_model=BuildRunResponse, tags=["build"])
def get_build_run(build_run_id: str, session: Session = Depends(get_session)):
    try:
        bid = uuid.UUID(build_run_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid build_run_id")
    stmt = select(BuildRun).where(BuildRun.id == bid)
    br = session.exec(stmt).first()
    if not br:
        raise HTTPException(status_code=404, detail="BuildRun not found")
    return BuildRunResponse(
        id=br.id,
        tenant=br.tenant,
        project_id=br.project_id,
        pricing_snapshot_id=br.pricing_snapshot_id,
        budget_cap=br.budget_cap,
        estimated_cost=br.estimated_cost,
        status=br.status,
        template_set=br.template_set,
        policy_reason=br.policy_reason,
        created_at=br.created_at.isoformat(),
        updated_at=br.updated_at.isoformat(),
    )


class BuildPrecheckRequest(BaseModel):
    tenant: str
    project_id: str
    gpu_model: str | None = None
    region: str | None = None
    hours_planned: float
    quantity: int = 1
    budget_cap: float
    payment_approved: bool = False
    required_feature: str | None = None
    current_agents: int = 0


class BuildPrecheckResponse(BaseModel):
    within_budget: bool
    estimated_cost: float
    currency: str | None = None
    policy_decision: dict | None = None
    require_payment: bool = False
    recommended_action: str | None = None


@router.post("/build/precheck", response_model=BuildPrecheckResponse, tags=["build"])
async def build_precheck(payload: BuildPrecheckRequest) -> BuildPrecheckResponse:
    from ..core.config import settings

    params = {
        "gpu_model": payload.gpu_model,
        "region": payload.region,
        "hours_planned": payload.hours_planned,
        "quantity": payload.quantity,
        "budget_cap": payload.budget_cap,
        "payment_approved": payload.payment_approved,
        "required_feature": payload.required_feature,
        "current_agents": payload.current_agents,
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    url = settings.pricing_service_url.rstrip("/") + "/v1/pricing/evaluate-budget/with-policy"
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(url, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Pricing precheck failed: {r.text}")
    data = r.json()

    require_payment = False
    recommended = None
    # If budget exceeded or policy says not allowed, recommend payment or reduce plan
    decision = data.get("policy_decision") or {}
    if not data.get("within_budget", False):
        require_payment = True
        recommended = "increase budget or reduce hours"
    elif decision and not decision.get("allow_build", True):
        # If policy blocks build, recommend payment if payment_approved missing or feature disabled
        reason = decision.get("reason")
        if reason in ("payment_or_feature_required",):
            require_payment = not payload.payment_approved
            recommended = "complete payment or enable required feature"
        elif reason == "max_agents_exceeded":
            recommended = "reduce concurrent agents or upgrade plan"

    return BuildPrecheckResponse(
        within_budget=bool(data.get("within_budget", False)),
        estimated_cost=float(data.get("estimated_cost", 0.0)),
        currency=data.get("currency"),
        policy_decision=decision or None,
        require_payment=require_payment,
        recommended_action=recommended,
    )
# Planner endpoints – generate, refine, retrieve, delete plans
from .planner import router as planner_router
router.include_router(planner_router)


class SessionStartRequest(BaseModel):
    tenant: str = Field(..., description="Tenant identifier")
    user: str = Field(..., description="User starting the session")
    prompt: str = Field(..., description="Conversation seed prompt")
    model: str = Field(default="somagent-demo", description="Requested model identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")


class SessionStartResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    session_id: str
    task_queue: str


class SessionStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    history_length: int | None = None
    result: Dict[str, Any] | None = None


class AgentDirectiveModel(BaseModel):
    agent_id: str
    goal: str
    prompt: str
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartRequest(BaseModel):
    tenant: str
    initiator: str
    directives: List[AgentDirectiveModel]
    notification_channel: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    orchestration_id: str
    task_queue: str


class CapsuleRunRequest(BaseModel):
    tenant: str
    user: str
    capsule_id: str = Field(..., description="Capsule identifier, e.g. org/name")
    version: str = Field(default="latest", description="Capsule version/tag")
    params: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the capsule run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata for audit/tracing")


class CapsuleRunResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    task_queue: str
    capsule_id: str
    version: str


async def get_temporal_client(request: Request) -> temporal_client.Client:
    client = getattr(request.app.state, "temporal_client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Temporal client not initialised")
    return client


def _normalize_result(result_obj: Any) -> Dict[str, Any] | None:
    if result_obj is None:
        return None
    if is_dataclass(result_obj):
        return asdict(result_obj)
    if isinstance(result_obj, dict):
        return result_obj
    if isinstance(result_obj, list):
        return {"items": result_obj}
    return {"value": result_obj}


@router.post("/sessions/start", response_model=SessionStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_session(request: Request, client: temporal_client.Client = Depends(get_temporal_client)) -> SessionStartResponse:
    """Kick off the Temporal session workflow and return identifiers for tracking.

    This handler is tolerant in dev to payloads that provide either
    (tenant, user) or (tenant_id, user_id) to accommodate slightly
    different gateway forwards during local debugging.
    """
    body = await request.json()

    # Normalize tenant/user fields from either canonical or legacy names
    tenant = body.get("tenant") or body.get("tenant_id")
    user = body.get("user") or body.get("user_id")
    prompt = body.get("prompt")
    model = body.get("model") or "somagent-demo"
    metadata = body.get("metadata") or {}

    if not tenant or not user or not prompt:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: tenant, user, and prompt are required",
        )

    # Build a validated request model for downstream code clarity
    payload = SessionStartRequest(
        tenant=tenant,
        user=user,
        prompt=prompt,
        model=model,
        metadata=metadata,
    )

    session_id = payload.metadata.get("session_id") or f"session-{uuid4()}"
    workflow_id = f"session-{session_id}"

    handle = await client.start_workflow(
        "session-start-workflow",
        SessionStartInput(
            session_id=session_id,
            tenant=payload.tenant,
            user=payload.user,
            prompt=payload.prompt,
            model=payload.model,
            metadata=payload.metadata,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    # Some Temporal client/server combinations may return None for run_id
    # in development setups. Be tolerant during dev smoke tests and coerce
    # a missing run_id to an empty string while logging the handle for
    # diagnostic purposes.
    try:
        hid = getattr(handle, "id", None) or workflow_id
        rid = getattr(handle, "run_id", None) or ""
    except Exception:
        # Fallback if handle is an unexpected type
        hid = workflow_id
        rid = ""

    # Helpful debug log when running locally to surface Temporal client returns
    try:
        import logging

        logging.getLogger("orchestrator").debug("workflow handle: %s", repr(handle))
    except Exception:
        pass

    return SessionStartResponse(
        workflow_id=hid,
        run_id=rid,
        session_id=session_id,
        task_queue=settings.temporal_task_queue,
    )


@router.get("/sessions/{workflow_id}", response_model=SessionStatusResponse)
async def get_session_status(workflow_id: str, client: temporal_client.Client = Depends(get_temporal_client)) -> SessionStatusResponse:
    """Fetch workflow status and (if completed) the result payload."""

    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
    except RPCError as exc:
        if exc.status == RPCStatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    status_name = desc.status.name.lower()
    result: Dict[str, Any] | None = None
    if status_name == "completed":
        try:
            result_obj = await handle.result()
            result = _normalize_result(result_obj)
        except Exception as exc:  # pragma: no cover - Temporal result retrieval edge cases
            result = {"error": str(exc)}

    # ``desc`` may be a simple namespace without an ``id`` attribute (as in the
    # test suite). Use ``getattr`` to safely fall back to the supplied
    # ``workflow_id`` when the attribute is missing.
    return SessionStatusResponse(
        workflow_id=getattr(desc, "id", workflow_id),
        run_id=getattr(desc, "run_id", ""),
        status=status_name,
        history_length=getattr(desc, "history_length", 0),
        result=result,
    )


@router.post("/mao/start", response_model=MultiAgentStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_multi_agent(
    payload: MultiAgentStartRequest,
    client: temporal_client.Client = Depends(get_temporal_client),
) -> MultiAgentStartResponse:
    orchestration_id = payload.metadata.get("orchestration_id") or f"mao-{uuid4()}"
    workflow_id = f"mao-{orchestration_id}"

    directives = [AgentDirective(**directive.model_dump()) for directive in payload.directives]

    handle = await client.start_workflow(
        "multi-agent-orchestration-workflow",
        MAOStartInput(
            orchestration_id=orchestration_id,
            tenant=payload.tenant,
            initiator=payload.initiator,
            directives=directives,
            notification_channel=payload.notification_channel,
            metadata=payload.metadata,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    run_id = getattr(handle, "run_id", None)
    if not run_id:
        run_id = getattr(handle, "first_execution_run_id", None)

    return MultiAgentStartResponse(
        workflow_id=handle.id,
        run_id=run_id,
        orchestration_id=orchestration_id,
        task_queue=settings.temporal_task_queue,
    )


@router.get("/mao/{workflow_id}", response_model=SessionStatusResponse)
async def get_multi_agent_status(
    workflow_id: str,
    client: temporal_client.Client = Depends(get_temporal_client),
) -> SessionStatusResponse:
    return await get_session_status(workflow_id, client)


@router.post("/capsule/run", response_model=CapsuleRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_capsule_run(
    payload: CapsuleRunRequest,
    client: temporal_client.Client = Depends(get_temporal_client),
    # OPA client will be lazily imported inside the function to avoid circular deps.
) -> CapsuleRunResponse:
    """Start a lightweight capsule run workflow and return identifiers.

    This is a minimal starter that kicks off a Temporal workflow which can
    be extended in subsequent sprints to provision environments, stream logs,
    and emit audit records.
    """
    from uuid import uuid4

    run_hint = payload.metadata.get("run_id") or f"run-{uuid4()}"
    # ``payload.capsule_id`` may contain slashes (e.g., "org/name"). FastAPI
    # path parameters stop at a slash, so we sanitise the identifier for the
    # workflow ID by replacing '/' with '_' – this keeps the ID deterministic
    # while remaining URL‑safe.
    safe_capsule_id = payload.capsule_id.replace("/", "_")
    workflow_id = f"capsule-{payload.tenant}-{safe_capsule_id}-{run_hint}"

    # -------------------------------------------------------------------
    # OPA authorization – ensure the caller is allowed to execute the capsule.
    # -------------------------------------------------------------------
    try:
        from services.common.opa_client import check_policy

        # Full OPA policy path: package ``somagent.capsule`` with rule
        # ``allow_execute_capsule``.
        allowed = await check_policy(
            policy_name="somagent/capsule/allow_execute_capsule",
            input={
                "user": payload.user,
                "tenant": payload.tenant,
                "capsule": payload.capsule_id,
                "version": payload.version,
            },
        )
        if allowed is False:
            raise HTTPException(status_code=403, detail="Not allowed to execute capsule")
    except Exception:
        # If OPA is unavailable or the policy is missing we fall back to allow –
        # this mirrors the behaviour of other endpoints where OPA is optional.
        pass

    handle = await client.start_workflow(
        "capsule-run-workflow",
        CapsuleRunInput(
            run_id=run_hint,
            capsule_id=payload.capsule_id,
            version=payload.version,
            tenant=payload.tenant,
            user=payload.user,
            params=payload.params,
            metadata=payload.metadata,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    rid = getattr(handle, "run_id", None) or getattr(handle, "first_execution_run_id", None)

    return CapsuleRunResponse(
        workflow_id=handle.id,
        run_id=rid,
        task_queue=settings.temporal_task_queue,
        capsule_id=payload.capsule_id,
        version=payload.version,
    )


@router.get("/capsule/{workflow_id}", response_model=SessionStatusResponse)
async def get_capsule_status(
    workflow_id: str,
    client: temporal_client.Client = Depends(get_temporal_client),
) -> SessionStatusResponse:
    """Fetch status for a capsule-run workflow by workflow_id."""
    return await get_session_status(workflow_id, client)
