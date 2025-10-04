"""Temporal workflow definitions for multi-agent orchestration (MAO)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from temporalio import activity, workflow

from ..core.config import settings
from .session import (
    IdentityTokenRequest,
    PolicyEvaluationContext,
    SlmRequest,
    emit_audit_event,
    evaluate_policy,
    issue_identity_token,
    run_slm_completion,
)


@dataclass
class AgentDirective:
    agent_id: str
    goal: str
    prompt: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MAOStartInput:
    orchestration_id: str
    tenant: str
    initiator: str
    directives: List[AgentDirective]
    notification_channel: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecutionResult:
    agent_id: str
    goal: str
    status: str
    slm_response: Dict[str, Any]
    token: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: datetime


@dataclass
class MAOResult:
    orchestration_id: str
    tenant: str
    initiator: str
    status: str
    agent_results: List[AgentExecutionResult]
    audit_event_id: str
    notifications_sent: List[Dict[str, Any]]
    completed_at: datetime
    policy: Dict[str, Any]


@dataclass
class NotificationEnvelope:
    tenant_id: str
    channel: str
    message: str
    severity: str = "info"
    metadata: Dict[str, str] = field(default_factory=dict)


@activity.defn(name="dispatch-notification")
async def dispatch_notification(envelope: NotificationEnvelope) -> Dict[str, Any]:
    """Send a notification via the notification service if configured."""

    if not settings.notification_service_url:
        activity.logger.warning("Notification service URL not configured; skipping dispatch")
        return {"status": "skipped", "reason": "notification service disabled"}

    payload = {
        "tenant_id": envelope.tenant_id,
        "channel": envelope.channel,
        "message": envelope.message,
        "severity": envelope.severity,
        "metadata": {k: str(v) for k, v in envelope.metadata.items()},
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(str(settings.notification_service_url), json=payload)
        response.raise_for_status()
        return response.json()


@workflow.defn(name="multi-agent-orchestration-workflow")
class MultiAgentWorkflow:
    """Coordinate multiple agent directives within a single Temporal workflow."""

    @workflow.run
    async def run(self, payload: MAOStartInput) -> MAOResult:
        logger = workflow.logger
        logger.info("Starting MAO workflow", payload=asdict(payload))

        policy_ctx = PolicyEvaluationContext(
            session_id=payload.orchestration_id,
            tenant=payload.tenant,
            user=payload.initiator,
            payload={**payload.metadata, "directives": [asdict(d) for d in payload.directives]},
        )

        policy = await workflow.execute_activity(
            evaluate_policy,
            policy_ctx,
            start_to_close_timeout=timedelta(seconds=30),
        )

        notifications: List[Dict[str, Any]] = []
        agent_results: List[AgentExecutionResult] = []

        if not policy.get("allowed", True):
            audit_event_id = await workflow.execute_activity(
                emit_audit_event,
                {
                    "orchestration_id": payload.orchestration_id,
                    "tenant": payload.tenant,
                    "initiator": payload.initiator,
                    "status": "rejected",
                    "policy": policy,
                    "metadata": payload.metadata,
                },
                start_to_close_timeout=timedelta(seconds=10),
            )

            if payload.notification_channel:
                notification = await workflow.execute_activity(
                    dispatch_notification,
                    NotificationEnvelope(
                        tenant_id=payload.tenant,
                        channel=payload.notification_channel,
                        severity="warning",
                        message=f"MAO {payload.orchestration_id} rejected by policy",
                        metadata={"initiator": payload.initiator},
                    ),
                    start_to_close_timeout=timedelta(seconds=15),
                )
                notifications.append(notification)

            result = MAOResult(
                orchestration_id=payload.orchestration_id,
                tenant=payload.tenant,
                initiator=payload.initiator,
                status="rejected",
                agent_results=agent_results,
                audit_event_id=audit_event_id,
                notifications_sent=notifications,
                completed_at=workflow.now(),
                policy=policy,
            )
            logger.info("MAO workflow rejected", result=asdict(result))
            return result

        for directive in payload.directives:
            started_at = workflow.now()

            token_req = IdentityTokenRequest(
                user_id=payload.initiator,
                tenant_id=payload.tenant,
                capabilities=directive.capabilities or [f"agent:{directive.agent_id}"],
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
                    session_id=f"{payload.orchestration_id}:{directive.agent_id}",
                    prompt=directive.prompt,
                    model=directive.metadata.get("model", "somagent-demo"),
                    tenant=payload.tenant,
                    user=payload.initiator,
                ),
                start_to_close_timeout=timedelta(seconds=90),
            )

            completed_at = workflow.now()
            execution_result = AgentExecutionResult(
                agent_id=directive.agent_id,
                goal=directive.goal,
                status="completed",
                slm_response=slm_response,
                token=token,
                started_at=started_at,
                completed_at=completed_at,
            )
            agent_results.append(execution_result)

            if payload.notification_channel:
                notification = await workflow.execute_activity(
                    dispatch_notification,
                    NotificationEnvelope(
                        tenant_id=payload.tenant,
                        channel=payload.notification_channel,
                        severity="info",
                        message=f"MAO {payload.orchestration_id} completed directive {directive.agent_id}",
                        metadata={
                            "goal": directive.goal,
                            "status": execution_result.status,
                            "completed_at": completed_at.isoformat(),
                        },
                    ),
                    start_to_close_timeout=timedelta(seconds=15),
                )
                notifications.append(notification)

        audit_event_id = await workflow.execute_activity(
            emit_audit_event,
            {
                "orchestration_id": payload.orchestration_id,
                "tenant": payload.tenant,
                "initiator": payload.initiator,
                "status": "completed",
                "policy": policy,
                "directives": [asdict(d) for d in payload.directives],
                "agent_results": [asdict(r) for r in agent_results],
            },
            start_to_close_timeout=timedelta(seconds=15),
        )

        result = MAOResult(
            orchestration_id=payload.orchestration_id,
            tenant=payload.tenant,
            initiator=payload.initiator,
            status="completed",
            agent_results=agent_results,
            audit_event_id=audit_event_id,
            notifications_sent=notifications,
            completed_at=workflow.now(),
            policy=policy,
        )
        logger.info("MAO workflow completed", result=asdict(result))
        return result
