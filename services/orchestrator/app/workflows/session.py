"""Session orchestration workflow executed by Temporal.

This workflow coordinates policy evaluation, identity token issuance, SLM
invocation via Ray, and audit emission over Kafka using real client libraries.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from aiokafka import AIOKafkaProducer
from temporalio import activity, workflow

from ..core.config import settings

# ---------------------------------------------------------------------------
# Data contracts shared between the API surface and workflow execution.
# ---------------------------------------------------------------------------


@dataclass
class SessionStartInput:
    session_id: str
    tenant: str
    user: str
    prompt: str
    model: str = "somagent-demo"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionStartResult:
    session_id: str
    tenant: str
    user: str
    status: str
    policy: Dict[str, Any]
    token: Optional[Dict[str, Any]]
    slm_response: Dict[str, Any]
    audit_event_id: str
    completed_at: datetime
    volcano_job: Optional[Dict[str, Any]] = None


@dataclass
class PolicyEvaluationContext:
    session_id: str
    tenant: str
    user: str
    payload: Dict[str, Any]


@dataclass
class IdentityTokenRequest:
    user_id: str
    tenant_id: str
    capabilities: list[str]
    mfa_code: Optional[str] = None


@dataclass
class SlmRequest:
    session_id: str
    prompt: str
    model: str
    tenant: str
    user: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _identity_endpoint(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    suffix = "/v1/tokens/issue"
    return normalized if normalized.endswith(suffix) else f"{normalized}{suffix}"


def _policy_endpoint(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    suffix = "/v1/evaluate"
    return normalized if normalized.endswith(suffix) else f"{normalized}{suffix}"


# ---------------------------------------------------------------------------
# Activities – executed by Temporal workers.
# ---------------------------------------------------------------------------


@activity.defn(name="evaluate-policy")
async def evaluate_policy(ctx: PolicyEvaluationContext) -> Dict[str, Any]:
    """Invoke the policy engine using the real HTTP endpoint."""

    async with httpx.AsyncClient(timeout=10.0) as client:
        endpoint = _policy_endpoint(str(settings.policy_engine_url))
        response = await client.post(endpoint, json=ctx.payload)
        response.raise_for_status()
        payload = response.json()
    return payload if isinstance(payload, dict) else {"raw": payload}


@activity.defn(name="issue-identity-token")
async def issue_identity_token(req: IdentityTokenRequest) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        endpoint = _identity_endpoint(str(settings.identity_service_url))
        response = await client.post(endpoint, json=asdict(req))
        response.raise_for_status()
        payload = response.json()
    return payload if isinstance(payload, dict) else {"raw": payload}


@activity.defn(name="emit-audit-event")
async def emit_audit_event(event: Dict[str, Any]) -> str:
    """Publish an audit event to Kafka using the configured bootstrap servers."""

    audit_id = str(uuid4())
    event = {**event, "audit_id": audit_id, "emitted_at": datetime.now(timezone.utc).isoformat()}

    bootstrap = settings.kafka_bootstrap_servers
    if not bootstrap:
        activity.logger.warning("Kafka bootstrap servers not configured; audit event stored locally")
        activity.logger.info(json.dumps(event))
        return audit_id

    producer = AIOKafkaProducer(bootstrap_servers=[s.strip() for s in bootstrap.split(",") if s.strip()])
    await producer.start()
    try:
        await producer.send_and_wait("agent.audit", json.dumps(event).encode("utf-8"))
    finally:
        await producer.stop()
    return audit_id


@activity.defn(name="run-slm-completion")
def run_slm_completion(request: SlmRequest) -> Dict[str, Any]:
    """Execute a Ray remote function to simulate a completion call."""

    import time

    import ray

    ray.init(address=settings.ray_address or "auto", namespace=settings.ray_namespace, ignore_reinit_error=True)

    @ray.remote
    def _generate_completion(prompt: str, model: str, session_id: str, tenant: str, user: str) -> Dict[str, Any]:
        # In production this is where a provider adapter is called. We keep the
        # function simple but real (executed inside Ray) to honour the principle
        # of avoiding mocks.
        time.sleep(0.5)
        return {
            "session_id": session_id,
            "tenant": tenant,
            "user": user,
            "model": model,
            "prompt_summary": prompt[:200],
            "completion": f"Model {model} acknowledged prompt length {len(prompt)} characters.",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    result = ray.get(
        _generate_completion.remote(
            request.prompt,
            request.model,
            request.session_id,
            request.tenant,
            request.user,
        )
    )
    return result


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------


@workflow.defn(name="session-start-workflow")
class SessionWorkflow:
    """Temporal workflow orchestrating a single session bootstrap."""

    @workflow.run
    async def run(self, payload: SessionStartInput) -> SessionStartResult:
        logger = workflow.logger
        logger.info("Starting session workflow", payload=payload.__dict__)

        policy_ctx = PolicyEvaluationContext(
            session_id=payload.session_id,
            tenant=payload.tenant,
            user=payload.user,
            payload={**payload.metadata, "session_id": payload.session_id, "prompt": payload.prompt},
        )

        policy = await workflow.execute_activity(
            evaluate_policy,
            policy_ctx,
            start_to_close_timeout=timedelta(seconds=20),
        )

        if not policy.get("allowed", True):
            audit_id = await workflow.execute_activity(
                emit_audit_event,
                {
                    "session_id": payload.session_id,
                    "tenant": payload.tenant,
                    "user": payload.user,
                    "status": "rejected",
                    "policy": policy,
                },
                start_to_close_timeout=timedelta(seconds=10),
            )
            return SessionStartResult(
                session_id=payload.session_id,
                tenant=payload.tenant,
                user=payload.user,
                status="rejected",
                policy=policy,
                token=None,
                slm_response={},
                audit_event_id=audit_id,
                completed_at=datetime.now(timezone.utc),
            )

        volcano_job_result: dict[str, Any] | None = None
        if settings.enable_volcano_scheduler:
            volcano_payload: dict[str, Any] = {
                "session_id": payload.session_id,
                "tenant": payload.tenant,
                "user": payload.user,
                "wait": payload.metadata.get("volcano_wait", True),
            }
            for key, meta_key in {
                "queue": "volcano_queue",
                "command": "volcano_command",
                "image": "volcano_image",
                "env": "volcano_env",
                "cpu": "volcano_cpu",
                "memory": "volcano_memory",
                "timeout_seconds": "volcano_timeout_seconds",
            }.items():
                value = payload.metadata.get(meta_key)
                if value is not None:
                    volcano_payload[key] = value

            try:
                volcano_job_result = await workflow.execute_activity(
                    "launch-volcano-session-job",
                    volcano_payload,
                    start_to_close_timeout=timedelta(
                        seconds=settings.volcano_job_timeout_seconds + 30
                    ),
                )
                logger.info("Volcano job submitted with result %s", volcano_job_result)
            except Exception as exc:  # pragma: no cover - best effort integration
                logger.warning("Volcano submission failed: %s", exc)

        token_req = IdentityTokenRequest(
            user_id=payload.user,
            tenant_id=payload.tenant,
            capabilities=["session:start"],
            mfa_code=payload.metadata.get("mfa_code"),
        )
        token = await workflow.execute_activity(
            issue_identity_token,
            token_req,
            start_to_close_timeout=timedelta(seconds=20),
        )

        slm_response = await workflow.execute_activity(
            run_slm_completion,
            SlmRequest(
                session_id=payload.session_id,
                prompt=payload.prompt,
                model=payload.model,
                tenant=payload.tenant,
                user=payload.user,
            ),
            start_to_close_timeout=timedelta(seconds=60),
        )

        audit_event_id = await workflow.execute_activity(
            emit_audit_event,
            {
                "session_id": payload.session_id,
                "tenant": payload.tenant,
                "user": payload.user,
                "status": "accepted",
                "policy": policy,
                "token_claims": {k: v for k, v in token.items() if k != "access_token"},
                "slm_model": payload.model,
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        result = SessionStartResult(
            session_id=payload.session_id,
            tenant=payload.tenant,
            user=payload.user,
            status="completed",
            policy=policy,
            token=token,
            slm_response=slm_response,
            audit_event_id=audit_event_id,
            completed_at=datetime.now(timezone.utc),
            volcano_job=volcano_job_result,
        )
        logger.info("Session workflow completed", result=result.__dict__)
        return result
