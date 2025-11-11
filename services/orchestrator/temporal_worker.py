"""
Temporal worker for KAMACHIQ workflows.
Sprint-5: Executes autonomous project orchestration workflows.
"""

import asyncio
import logging
import os
from contextlib import suppress

from temporalio.client import Client
from temporalio.worker import Worker
from workflows import (
    AgentTaskWorkflow,
    KAMACHIQProjectWorkflow,
    aggregate_results,
    copy_templates,
    create_task_plan,
    decompose_project,
    execute_task,
    review_output,
    spawn_agent,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker(
    temporal_host: str = "localhost:10009",
    task_queue: str = "kamachiq-tasks",
    namespace: str = "default",
):
    """
    Run Temporal worker that executes KAMACHIQ workflows.

    Args:
        temporal_host: Temporal server address
        task_queue: Task queue name
        namespace: Temporal namespace
    """
    logger.info(f"Connecting to Temporal server at {temporal_host}")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_host,
        namespace=namespace,
    )

    logger.info(f"Connected to Temporal namespace: {namespace}")
    logger.info(f"Listening on task queue: {task_queue}")

    # Create worker with workflows and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            KAMACHIQProjectWorkflow,
            AgentTaskWorkflow,
        ],
        activities=[
            decompose_project,
            create_task_plan,
            spawn_agent,
            execute_task,
            review_output,
            aggregate_results,
            copy_templates,
        ],
    )

    logger.info("✅ Temporal worker started")
    logger.info("   - KAMACHIQProjectWorkflow: Autonomous project execution")
    logger.info("   - AgentTaskWorkflow: Individual agent task execution")
    logger.info("   - 7 activities registered")

    # Run worker execution loop
    # ---------------------------------------------------------------------
    # Background task: report Temporal queue length to Prometheus
    # ---------------------------------------------------------------------
    from .metrics.queue import set_queue_length

    async def _report_queue_length() -> None:
        """Periodically query Temporal for pending workflows and update gauge."""
        while True:
            try:
                # Count open workflows on the configured task queue.
                pending = 0
                async for _ in client.list_workflows(
                    query=f"TaskQueue = '{task_queue}' AND CloseTime = missing",
                    page_size=100,
                ):
                    pending += 1
                set_queue_length(task_queue, pending)
            except Exception as exc:
                logger.error(f"Failed to report queue length: {exc}")
            await asyncio.sleep(15.0)

    queue_reporter = asyncio.create_task(_report_queue_length())

    try:
        await worker.run()
    finally:
        # Cancel background metric task on shutdown
        queue_reporter.cancel()
        with suppress(asyncio.CancelledError):
            await queue_reporter


async def start_workflow_example(
    client: Client,
    project_description: str,
    user_id: str = "demo_user",
):
    """
    Example: Start a KAMACHIQ workflow.

    Demonstrates workflow execution.
    """
    workflow_id = f"kamachiq-project-{user_id}-{int(asyncio.get_event_loop().time())}"

    logger.info(f"Starting workflow: {workflow_id}")

    # Start workflow
    handle = await client.start_workflow(
        KAMACHIQProjectWorkflow.run,
        args=[project_description, user_id, workflow_id],
        id=workflow_id,
        task_queue="kamachiq-tasks",
    )

    logger.info(f"Workflow started: {handle.id}")
    logger.info("Waiting for completion...")

    # Wait for result
    result = await handle.result()

    logger.info("✅ Workflow completed successfully!")
    logger.info(f"   Project ID: {result['project_id']}")
    logger.info(f"   Tasks: {result['task_count']}")
    logger.info(f"   Quality Score: {result['quality_score']}%")
    logger.info(f"   Status: {result['status']}")

    return result


async def main():
    """
    Main entry point for Temporal worker.

    Environment variables:
    - TEMPORAL_HOST: Temporal server address (default: localhost:10009)
    - TEMPORAL_NAMESPACE: Namespace (default: default)
    - TEMPORAL_TASK_QUEUE: Task queue (default: kamachiq-tasks)
    - RUN_EXAMPLE: If "true", run example workflow (default: false)
    """
    from services.common.config.base_settings import resolve_env

    temporal_host = resolve_env("TEMPORAL_HOST", "localhost:10009")
    namespace = resolve_env("TEMPORAL_NAMESPACE", "default")
    task_queue = resolve_env("TEMPORAL_TASK_QUEUE", "kamachiq-tasks")
    run_example = str(resolve_env("RUN_EXAMPLE", "false")).lower() == "true"

    if run_example:
        # Run example workflow then start worker
        logger.info("Running example workflow first...")

        client = await Client.connect(temporal_host, namespace=namespace)

        await start_workflow_example(
            client,
            project_description="Create a simple Python CLI calculator that supports basic math operations",
            user_id="demo_user",
        )

        logger.info("Example complete. Starting worker...")

    # Run worker (blocks until shutdown)
    await run_worker(
        temporal_host=temporal_host,
        task_queue=task_queue,
        namespace=namespace,
    )


if __name__ == "__main__":
    """
    Run Temporal worker.

    Usage:
        # Start worker (connects to local Temporal server)
        python temporal_worker.py

        # Start worker with example
        RUN_EXAMPLE=true python temporal_worker.py

        # Connect to remote Temporal
        TEMPORAL_HOST=temporal.observability:10009 python temporal_worker.py
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        raise
