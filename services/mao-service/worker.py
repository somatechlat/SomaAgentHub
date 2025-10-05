"""
⚠️ WE DO NOT MOCK - Real Temporal worker implementation.

This worker processes activities for the MAO service.
"""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from workflows.project_workflow import ProjectWorkflow
from workflows.activities import (
    create_workspace,
    provision_git_repo,
    execute_capsule,
    bundle_artifacts,
    notify_completion,
    cleanup_workspace,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    Start the Temporal worker.
    
    This worker:
    1. Connects to Temporal server
    2. Registers workflows and activities
    3. Processes tasks from the queue
    """
    
    # Connect to Temporal
    client = await Client.connect("localhost:7233", namespace="default")
    
    logger.info("✅ Connected to Temporal server")
    
    # Create worker
    worker = Worker(
        client,
        task_queue="mao-task-queue",
        workflows=[ProjectWorkflow],
        activities=[
            create_workspace,
            provision_git_repo,
            execute_capsule,
            bundle_artifacts,
            notify_completion,
            cleanup_workspace,
        ],
        max_concurrent_activities=10,
        max_concurrent_workflow_tasks=10,
    )
    
    logger.info("🚀 MAO worker started, listening on task queue: mao-task-queue")
    logger.info("   Workflows: ProjectWorkflow")
    logger.info("   Activities: 6 registered")
    
    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
