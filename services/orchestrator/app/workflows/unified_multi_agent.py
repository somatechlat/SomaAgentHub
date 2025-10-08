"""Unified multi-agent workflow orchestrating across multiple frameworks."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow

from ..core.framework_router import FrameworkRouter, MultiAgentPattern
from ..integrations import run_autogen_group_chat, run_crewai_delegation, run_langgraph_routing
from ..workflows.session import PolicyEvaluationContext, evaluate_policy, emit_audit_event


@workflow.defn(name="unified-multi-agent-workflow")
class UnifiedMultiAgentWorkflow:
    """Temporal workflow that selects the optimal framework per request."""

    def __init__(self) -> None:
        self.router = FrameworkRouter()

    @workflow.run
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        logger = workflow.logger
        workflow_id = workflow.info().workflow_id

        policy_ctx = PolicyEvaluationContext(
            session_id=request.get("session_id", workflow_id),
            tenant=request.get("tenant", "default"),
            user=request.get("user", "anonymous"),
            payload=request,
        )

        policy = await workflow.execute_activity(
            evaluate_policy,
            policy_ctx,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not policy.get("allowed", True):
            return {"status": "rejected", "reason": "policy_denied", "policy": policy}

        pattern = self.router.detect_pattern(request)
        activity_name = self.router.select_framework(pattern)

        logger.info(
            "Dispatching multi-agent request",
            pattern=pattern.value,
            activity=activity_name,
            workflow_id=workflow_id,
        )

        result: Dict[str, Any]
        if pattern is MultiAgentPattern.GROUP_CHAT:
            result = await workflow.execute_activity(
                run_autogen_group_chat,
                request,
                start_to_close_timeout=timedelta(minutes=10),
            )
        elif pattern is MultiAgentPattern.TASK_DELEGATION:
            result = await workflow.execute_activity(
                run_crewai_delegation,
                request,
                start_to_close_timeout=timedelta(minutes=15),
            )
        else:
            result = await workflow.execute_activity(
                run_langgraph_routing,
                request,
                start_to_close_timeout=timedelta(minutes=5),
            )

        await workflow.execute_activity(
            emit_audit_event,
            {
                "workflow_id": workflow_id,
                "pattern": pattern.value,
                "activity": activity_name,
                "status": "completed",
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "status": "completed",
            "pattern": pattern.value,
            "activity": activity_name,
            "policy": policy,
            "result": result,
        }
