"""Temporal worker bootstrap for the orchestrator service."""

from __future__ import annotations

import asyncio
import logging

from temporalio import client as temporal_client
from temporalio import worker as temporal_worker

from .core.config import settings
from .workflows.mao import MultiAgentWorkflow, dispatch_notification
from .workflows.session import (
    SessionWorkflow,
    emit_audit_event,
    evaluate_policy,
    issue_identity_token,
    run_slm_completion,
)


logger = logging.getLogger("orchestrator.worker")


async def _run_worker() -> None:
    logger.info(
        "Connecting Temporal client",
        extra={
            "target_host": settings.temporal_target_host,
            "namespace": settings.temporal_namespace,
            "task_queue": settings.temporal_task_queue,
        },
    )
    client = await temporal_client.Client.connect(
        settings.temporal_target_host,
        namespace=settings.temporal_namespace,
    )

    worker = temporal_worker.Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[SessionWorkflow, MultiAgentWorkflow],
        activities=[
            evaluate_policy,
            issue_identity_token,
            emit_audit_event,
            run_slm_completion,
            dispatch_notification,
        ],
    )

    await worker.run()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
