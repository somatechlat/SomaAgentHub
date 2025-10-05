"""
Real Temporal worker for KAMACHIQ workflows.
Sprint-5: Connects to real Temporal server, executes real workflows.
"""

import asyncio
import logging
import os
from typing import Optional

from temporalio.client import Client
from temporalio.worker import Worker

from workflows import (
    KAMACHIQProjectWorkflow,
    AgentTaskWorkflow,
    decompose_project,
    create_task_plan,
    spawn_agent,
    execute_task,
    review_output,
    aggregate_results,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker(
    temporal_host: str = "localhost:7233",
    task_queue: str = "kamachiq-tasks",
    namespace: str = "default",
):
    """
    Run real Temporal worker that executes KAMACHIQ workflows.
    
    This is NOT a mock - it connects to a real Temporal server
    and executes real workflows with real activities.
    
    Args:
        temporal_host: Real Temporal server address
        task_queue: Real task queue name
        namespace: Real Temporal namespace
    """
    logger.info(f"Connecting to REAL Temporal server at {temporal_host}")
    
    # Connect to REAL Temporal server
    client = await Client.connect(
        temporal_host,
        namespace=namespace,
    )
    
    logger.info(f"Connected to Temporal namespace: {namespace}")
    logger.info(f"Listening on task queue: {task_queue}")
    
    # Create REAL worker with real workflows and activities
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
        ],
    )
    
    logger.info("✅ Temporal worker started with REAL workflows")
    logger.info("   - KAMACHIQProjectWorkflow: Autonomous project execution")
    logger.info("   - AgentTaskWorkflow: Individual agent task execution")
    logger.info("   - 6 real activities registered")
    
    # Run worker (REAL execution loop)
    await worker.run()


async def start_workflow_example(
    client: Client,
    project_description: str,
    user_id: str = "demo_user",
):
    """
    Example: Start a real KAMACHIQ workflow.
    
    This demonstrates how to trigger a real workflow execution.
    """
    workflow_id = f"kamachiq-project-{user_id}-{int(asyncio.get_event_loop().time())}"
    
    logger.info(f"Starting REAL workflow: {workflow_id}")
    
    # Start REAL workflow
    handle = await client.start_workflow(
        KAMACHIQProjectWorkflow.run,
        args=[project_description, user_id, workflow_id],
        id=workflow_id,
        task_queue="kamachiq-tasks",
    )
    
    logger.info(f"Workflow started: {handle.id}")
    logger.info("Waiting for completion...")
    
    # Wait for REAL result
    result = await handle.result()
    
    logger.info(f"✅ Workflow completed successfully!")
    logger.info(f"   Project ID: {result['project_id']}")
    logger.info(f"   Tasks: {result['task_count']}")
    logger.info(f"   Quality Score: {result['quality_score']}%")
    logger.info(f"   Status: {result['status']}")
    
    return result


async def main():
    """
    Main entry point for Temporal worker.
    
    Environment variables:
    - TEMPORAL_HOST: Temporal server address (default: localhost:7233)
    - TEMPORAL_NAMESPACE: Namespace (default: default)
    - TEMPORAL_TASK_QUEUE: Task queue (default: kamachiq-tasks)
    - RUN_EXAMPLE: If "true", run example workflow (default: false)
    """
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "kamachiq-tasks")
    run_example = os.getenv("RUN_EXAMPLE", "false").lower() == "true"
    
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
    Run the real Temporal worker.
    
    Usage:
        # Start worker (connects to local Temporal server)
        python temporal_worker.py
        
        # Start worker with example
        RUN_EXAMPLE=true python temporal_worker.py
        
        # Connect to remote Temporal
        TEMPORAL_HOST=temporal.observability:7233 python temporal_worker.py
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        raise
