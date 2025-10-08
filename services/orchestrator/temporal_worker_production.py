"""
Temporal worker for SomaAgentHub orchestration.

Registers all production workflows and activities:
- MarketingCampaignWorkflow
- KAMACHIQ workflows
- Multi-Agent Orchestration workflows
"""

import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

# Import from app package
from app.workflows.marketing_campaign import MarketingCampaignWorkflow
from app.workflows.marketing_activities import (
    # Activities
    research_phase_activity,
    content_creation_activity,
    design_assets_activity,
    review_approval_activity,
    distribute_campaign_activity,
    analytics_setup_activity,
    # Compensation activities
    delete_content_drafts_activity,
    delete_design_assets_activity,
    rollback_distribution_activity,
    cleanup_analytics_activity,
)

# Import existing workflows
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

# Import MAO workflow
from app.workflows.mao import MultiAgentWorkflow, dispatch_notification
from app.workflows.session import (
    SessionWorkflow,
    evaluate_policy,
    issue_identity_token,
    run_slm_completion,
    emit_audit_event,
)

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


async def run_worker(
    temporal_host: str = "localhost:7233",
    task_queue: str = "somagent-tasks",
    namespace: str = "default",
):
    """
    Run Temporal worker that executes all SomaAgentHub workflows.
    
    Args:
        temporal_host: Temporal server address
        task_queue: Task queue name
        namespace: Temporal namespace
    """
    logger.info(f"🔌 Connecting to Temporal server at {temporal_host}")
    
    # Connect to Temporal server
    client = await Client.connect(
        temporal_host,
        namespace=namespace,
    )
    
    logger.info(f"✅ Connected to Temporal namespace: {namespace}")
    logger.info(f"📋 Listening on task queue: {task_queue}")
    
    # Create worker with ALL workflows and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            # NEW: Marketing Campaign Workflow (Production)
            MarketingCampaignWorkflow,
            
            # Existing: KAMACHIQ Workflows
            KAMACHIQProjectWorkflow,
            AgentTaskWorkflow,
            
            # Existing: MAO Workflow
            MultiAgentWorkflow,
            
            # Existing: Session Workflow
            SessionWorkflow,
        ],
        activities=[
            # NEW: Marketing Campaign Activities (11 total)
            research_phase_activity,
            content_creation_activity,
            design_assets_activity,
            review_approval_activity,
            distribute_campaign_activity,
            analytics_setup_activity,
            delete_content_drafts_activity,
            delete_design_assets_activity,
            rollback_distribution_activity,
            cleanup_analytics_activity,
            
            # Existing: KAMACHIQ Activities
            decompose_project,
            create_task_plan,
            spawn_agent,
            execute_task,
            review_output,
            aggregate_results,
            
            # Existing: MAO Activities
            dispatch_notification,
            
            # Existing: Session Activities
            evaluate_policy,
            issue_identity_token,
            run_slm_completion,
            emit_audit_event,
        ],
    )
    
    logger.info("🚀 Temporal worker started successfully!")
    logger.info("")
    logger.info("📊 Registered Workflows (5):")
    logger.info("   ✅ MarketingCampaignWorkflow - End-to-end campaign automation")
    logger.info("   ✅ KAMACHIQProjectWorkflow - Autonomous project execution")
    logger.info("   ✅ AgentTaskWorkflow - Individual agent tasks")
    logger.info("   ✅ MultiAgentWorkflow - Multi-agent orchestration")
    logger.info("   ✅ SessionWorkflow - User session management")
    logger.info("")
    logger.info("🔧 Registered Activities (21):")
    logger.info("   Marketing Campaign: 10 activities")
    logger.info("   KAMACHIQ: 6 activities")
    logger.info("   MAO: 1 activity")
    logger.info("   Session: 4 activities")
    logger.info("")
    logger.info(f"⏳ Worker polling on queue: {task_queue}")
    
    # Run worker execution loop (blocks until shutdown)
    await worker.run()


async def main():
    """
    Main entry point for Temporal worker.
    
    Environment variables:
    - TEMPORAL_HOST: Temporal server address (default: localhost:7233)
    - TEMPORAL_NAMESPACE: Namespace (default: default)
    - TEMPORAL_TASK_QUEUE: Task queue (default: somagent-tasks)
    """
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "somagent-tasks")
    
    try:
        await run_worker(
            temporal_host=temporal_host,
            task_queue=task_queue,
            namespace=namespace,
        )
    except KeyboardInterrupt:
        logger.info("👋 Worker shutdown requested")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    """
    Run Temporal worker.
    
    Usage:
        # Start worker (connects to local Temporal server)
        python temporal_worker.py
        
        # Connect to remote Temporal
        TEMPORAL_HOST=temporal.observability:7233 python temporal_worker.py
        
        # Use different task queue
        TEMPORAL_TASK_QUEUE=custom-queue python temporal_worker.py
    """
    asyncio.run(main())
