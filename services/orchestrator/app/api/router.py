"""HTTP routes for the orchestrator service.

Temporal has been fully removed. Former workflow endpoints now execute
as in‑process async tasks with immediate responses or lightweight status
tracking. All legacy Temporal constructs (clients, handles, task queues)
have been eliminated.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from prometheus_client import Counter
from pydantic import BaseModel, Field

from services.common.contracts.orchestrator import (
    AgentDirective as ContractAgentDirective,
)
from services.common.contracts.orchestrator import (
    MultiAgentStartRequest as ContractMultiAgentStartRequest,
)
from services.common.contracts.orchestrator import (
    MultiAgentStartResponse as ContractMultiAgentStartResponse,
)
from services.common.contracts.orchestrator import (
    SessionStartRequest as ContractSessionStartRequest,
)
from services.common.contracts.orchestrator import (
    SessionStartResponse as ContractSessionStartResponse,
)

from ..capsule_executor import CapsuleRunInput as ExecCapsuleRunInput
from ..capsule_executor import execute_capsule
from ..core.config import settings
from ..database import get_session

# Import conversation and training endpoints
from .conversation import router as conversation_router
from .projects import router as projects_router
from .registry import router as registry_router
from .routes.tenants import router as tenants_router
from .training import router as training_router

router = APIRouter(prefix="/v1", tags=["orchestrator"])
router.include_router(conversation_router)
router.include_router(projects_router)
router.include_router(training_router)

router.include_router(registry_router)

# Include Tenant Router
router.include_router(tenants_router)

# Metrics
POLICY_FALLBACK_EVENTS = Counter(
    "policy_fallback_events_total",
    "Total policy fallback events",
    ["route", "reason"],
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

    url = (
        settings.pricing_service_url.rstrip("/")
        + "/v1/pricing/evaluate-budget/with-policy"
    )
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(url, params=params)
        if r.status_code != 200:
            raise HTTPException(
                status_code=502, detail=f"Pricing precheck failed: {r.text}"
            )
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

from .planner import router as planner_router  # noqa: E402

router.include_router(planner_router)


SessionStartRequest = ContractSessionStartRequest
SessionStartResponse = ContractSessionStartResponse


class SessionStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    history_length: int | None = None
    result: dict[str, Any] | None = None


AgentDirectiveModel = ContractAgentDirective


MultiAgentStartRequest = ContractMultiAgentStartRequest
MultiAgentStartResponse = ContractMultiAgentStartResponse


class CapsuleRunRequest(BaseModel):
    tenant: str
    user: str
    capsule_id: str = Field(..., description="Capsule identifier, e.g. org/name")
    version: str = Field(default="latest", description="Capsule version/tag")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters for the capsule run"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for audit/tracing"
    )


class CapsuleRunResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    task_queue: str
    capsule_id: str
    version: str


class InProcessTaskStatus(BaseModel):
    id: str
    created_at: str
    type: str
    status: str
    result: dict[str, Any] | None = None


_INPROCESS_TASKS: dict[str, InProcessTaskStatus] = {}


def _normalize_result(result_obj: Any) -> dict[str, Any] | None:
    if result_obj is None:
        return None
    if is_dataclass(result_obj):
        return asdict(result_obj)
    if isinstance(result_obj, dict):
        return result_obj
    if isinstance(result_obj, list):
        return {"items": result_obj}
    return {"value": result_obj}


async def _call_policy_engine(payload: dict[str, Any]) -> dict[str, Any]:
    endpoint = str(settings.policy_engine_url).rstrip("/") + "/v1/evaluate"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(endpoint, json=payload)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {"raw": data}


async def _issue_identity_token(
    user_id: str, tenant_id: str, capabilities: list[str], mfa_code: str | None
) -> dict[str, Any]:
    endpoint = str(settings.identity_service_url).rstrip("/") + "/v1/tokens/issue"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            endpoint,
            json={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "capabilities": capabilities,
                "mfa_code": mfa_code,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {"raw": data}


async def _llm_chat_completion(
    prompt: str, model: str, tenant: str, user: str
) -> dict[str, Any]:
    base = (str(settings.llm_hub_url) or "").rstrip("/")
    if not base:
        raise RuntimeError("LLM_HUB_URL not configured")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/v1/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        # Normalize
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {
            "model": data.get("model", model),
            "completion": content,
            "usage": data.get("usage", {}),
        }


async def _run_session_task(workflow_id: str, payload: SessionStartRequest) -> None:
    logger = logging.getLogger("orchestrator.session")
    try:
        policy = await _call_policy_engine(
            {
                **(payload.metadata or {}),
                "tenant": payload.tenant,
                "user": payload.user,
                "session_id": workflow_id,
                "prompt": payload.prompt,
            }
        )
        if not policy.get("allowed", True):
            _INPROCESS_TASKS[workflow_id].status = "rejected"
            _INPROCESS_TASKS[workflow_id].result = {"policy": policy}
            return

        token = await _issue_identity_token(
            user_id=payload.user,
            tenant_id=payload.tenant,
            capabilities=["session:start"],
            mfa_code=(payload.metadata or {}).get("mfa_code"),
        )

        llm = await _llm_chat_completion(
            prompt=payload.prompt,
            model=payload.model or "somagent-demo",
            tenant=payload.tenant,
            user=payload.user,
        )

        _INPROCESS_TASKS[workflow_id].status = "completed"
        _INPROCESS_TASKS[workflow_id].result = {
            "policy": policy,
            "token": {k: v for k, v in token.items() if k != "access_token"},
            "llm": llm,
        }
    except Exception as exc:  # pragma: no cover - runtime protection
        logger.exception("session task failed: %s", exc)
        _INPROCESS_TASKS[workflow_id].status = "failed"
        _INPROCESS_TASKS[workflow_id].result = {"error": str(exc)}


async def _run_capsule_task(workflow_id: str, req: CapsuleRunRequest) -> None:
    logger = logging.getLogger("orchestrator.capsule")
    try:
        payload = ExecCapsuleRunInput(
            run_id=workflow_id,
            capsule_id=req.capsule_id,
            version=req.version,
            tenant=req.tenant,
            user=req.user,
            params=req.params or {},
            metadata=req.metadata or {},
        )
        result = await execute_capsule(payload)
        _INPROCESS_TASKS[workflow_id].status = "completed"
        _INPROCESS_TASKS[workflow_id].result = (
            result if isinstance(result, dict) else {"value": result}
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("capsule task failed: %s", exc)
        _INPROCESS_TASKS[workflow_id].status = "failed"
        _INPROCESS_TASKS[workflow_id].result = {"error": str(exc)}


async def _run_mao_task(workflow_id: str, payload: MultiAgentStartRequest) -> None:
    logger = logging.getLogger("orchestrator.mao")
    try:
        results: list[dict[str, Any]] = []
        for directive in payload.directives:
            token = await _issue_identity_token(
                user_id=payload.initiator,
                tenant_id=payload.tenant,
                capabilities=directive.capabilities or [f"agent:{directive.agent_id}"],
                mfa_code=(payload.metadata or {}).get("mfa_code"),
            )
            llm = await _llm_chat_completion(
                prompt=directive.prompt,
                model=directive.metadata.get("model", "central"),
                tenant=payload.tenant,
                user=payload.initiator,
            )
            results.append(
                {
                    "agent_id": directive.agent_id,
                    "goal": directive.goal,
                    "status": "completed",
                    "token_claims": {
                        k: v for k, v in token.items() if k != "access_token"
                    },
                    "llm": llm,
                }
            )
        _INPROCESS_TASKS[workflow_id].status = "completed"
        _INPROCESS_TASKS[workflow_id].result = {"agents": results}
    except Exception as exc:  # pragma: no cover
        logger.exception("mao task failed: %s", exc)
        _INPROCESS_TASKS[workflow_id].status = "failed"
        _INPROCESS_TASKS[workflow_id].result = {"error": str(exc)}


@router.post(
    "/sessions/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_session(request: Request) -> SessionStartResponse:
    """Start a session (in‑process async task).

    Previously launched a Temporal workflow. Now we create a deterministic
    task identifier and store a placeholder status. Downstream processing
    would be performed by an internal async worker (future enhancement).
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

    _INPROCESS_TASKS[workflow_id] = InProcessTaskStatus(
        id=workflow_id,
        created_at=datetime.now(UTC).isoformat(),
        type="session",
        status="started",
        result=None,
    )
    return SessionStartResponse(
        workflow_id=workflow_id,
        run_id="",
        session_id=session_id,
        task_queue="inprocess",
    )


@router.get("/sessions/{workflow_id}", response_model=SessionStatusResponse)
async def get_session_status(workflow_id: str) -> SessionStatusResponse:
    task = _INPROCESS_TASKS.get(workflow_id)
    if not task:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStatusResponse(
        workflow_id=workflow_id,
        run_id="",
        status=task.status,
        history_length=None,
        result=task.result,
    )


@router.post(
    "/mao/start",
    response_model=MultiAgentStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_multi_agent(
    payload: MultiAgentStartRequest,
    session=Depends(get_session),
) -> MultiAgentStartResponse:
    orchestration_id = payload.metadata.get("orchestration_id") or f"mao-{uuid4()}"
    workflow_id = f"mao-{orchestration_id}"

    _INPROCESS_TASKS[workflow_id] = InProcessTaskStatus(
        id=workflow_id,
        created_at=datetime.now(UTC).isoformat(),
        type="multi-agent",
        status="started",
        result={"directives": [d.model_dump() for d in payload.directives]},
    )

    # Real event emission using outbox + publisher
    logger = logging.getLogger("orchestrator.events")
    from services.common.events.publisher import get_publisher

    from ..services.event_service import OrchestratorEventService

    publisher = get_publisher("orchestrator")
    event_service = OrchestratorEventService(session=session, event_publisher=publisher)
    try:
        await event_service.emit_orchestration_started(
            workflow_id=workflow_id,
            tenant=payload.tenant,
            initiator=payload.initiator,
            directives=[d.model_dump() for d in payload.directives],
            metadata=payload.metadata,
        )
    except Exception as exc:
        logger.error("Failed emitting orchestration.started event: %s", exc)

    run_id = ""

    return MultiAgentStartResponse(
        workflow_id=workflow_id,
        run_id=run_id,
        orchestration_id=orchestration_id,
        task_queue="inprocess",
    )


@router.get("/mao/{workflow_id}", response_model=SessionStatusResponse)
async def get_multi_agent_status(workflow_id: str) -> SessionStatusResponse:
    return await get_session_status(workflow_id)


@router.post(
    "/capsule/run",
    response_model=CapsuleRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_capsule_run(
    payload: CapsuleRunRequest,
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
            raise HTTPException(
                status_code=403, detail="Not allowed to execute capsule"
            )
        # Treat None/unknown as deny unless explicitly allowed by config
        if allowed is None and not settings.allow_on_opa_error:
            raise HTTPException(status_code=503, detail="Policy evaluation unavailable")
        if allowed is None and settings.allow_on_opa_error:
            POLICY_FALLBACK_EVENTS.labels(route="capsule.run", reason="opa_none").inc()
    except Exception as exc:
        if settings.allow_on_opa_error:
            POLICY_FALLBACK_EVENTS.labels(
                route="capsule.run", reason="opa_exception"
            ).inc()
        else:
            raise HTTPException(
                status_code=503, detail="Policy engine unavailable"
            ) from exc

    _INPROCESS_TASKS[workflow_id] = InProcessTaskStatus(
        id=workflow_id,
        created_at=datetime.now(UTC).isoformat(),
        type="capsule",
        status="started",
        result={
            "capsule_id": payload.capsule_id,
            "version": payload.version,
            "params": payload.params,
        },
    )
    rid = ""

    return CapsuleRunResponse(
        workflow_id=workflow_id,
        run_id=rid,
        task_queue="inprocess",
        capsule_id=payload.capsule_id,
        version=payload.version,
    )


@router.get("/capsule/{workflow_id}", response_model=SessionStatusResponse)
async def get_capsule_status(workflow_id: str) -> SessionStatusResponse:
    return await get_session_status(workflow_id)
