"""
MAO Workflow Engine - Handles Marketing Automation Orchestrator workflows
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

logger = logging.getLogger(__name__)

class MAOWorkflowEngine:
    """MAO workflow engine implementation"""
    
    def __init__(self):
        self.client = None
        self.worker = None
        self.active_workflows = {}
        self.workflow_queue = asyncio.Queue()
    
    async def initialize(self):
        """Initialize temporal client and worker"""
        try:
            self.client = await Client.connect("localhost:7233")
            
            # Start worker for MAO workflows
            task_queue = "mao-workflow-queue"
            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=[MAOWorkflow],
                activities=[MAOActivities]
            )
            
            asyncio.create_task(self.worker.run())
            logger.info("MAO workflow engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MAO workflow engine: {e}")
            raise
    
    async def start_workflow(self, workflow_request: Dict[str, Any], tenant_context: Any) -> Dict[str, Any]:
        """Start MAO workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        try:
            # Start temporal workflow
            handle = await self.client.start_workflow(
                MAOWorkflow.run,
                workflow_request,
                id=workflow_id,
                task_queue="mao-workflow-queue"
            )
            
            # Store workflow metadata
            self.active_workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_type": "mao",
                "tenant_id": tenant_context.tenant_id,
                "status": "running",
                "started_at": datetime.utcnow(),
                "workflow_request": workflow_request,
                "handle": handle
            }
            
            return {
                "workflow_id": workflow_id,
                "estimated_duration": 600,  # 10 minutes
                "resource_allocation": {
                    "cpu": 4,
                    "memory": "8GB",
                    "storage": "20GB"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start MAO workflow: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get MAO workflow status"""
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow_meta = self.active_workflows[workflow_id]
        
        try:
            # Get workflow status from temporal
            description = await workflow_meta["handle"].describe()
            
            status = {
                "workflow_id": workflow_id,
                "workflow_type": "mao",
                "status": description.status.name,
                "started_at": workflow_meta["started_at"],
                "tenant_id": workflow_meta["tenant_id"],
                "workflow_request": workflow_meta["workflow_request"]
            }
            
            if description.result:
                status["result"] = description.result
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "workflow_id": workflow_id,
                "workflow_type": "mao",
                "status": "error",
                "error": str(e)
            }
    
    async def list_workflows(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List MAO workflows for tenant"""
        
        workflows = []
        
        for workflow_id, meta in self.active_workflows.items():
            if meta["tenant_id"] == tenant_id:
                workflows.append(await self.get_workflow_status(workflow_id))
        
        return workflows
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel MAO workflow"""
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        try:
            # Cancel temporal workflow
            await self.active_workflows[workflow_id]["handle"].cancel()
            
            # Update metadata
            self.active_workflows[workflow_id]["status"] = "cancelled"
            
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "cancelled_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise
    
    async def has_workflow(self, workflow_id: str) -> bool:
        """Check if workflow exists"""
        return workflow_id in self.active_workflows

@workflow.defn
class MAOWorkflow:
    """MAO workflow definition"""
    
    @workflow.run
    async def run(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Run MAO workflow"""
        
        logger.info(f"Starting MAO workflow: {workflow_request}")
        
        # Extract MAO parameters
        campaign_name = workflow_request.get("campaign_name")
        campaign_type = workflow_request.get("campaign_type", "email")
        target_audience = workflow_request.get("target_audience", {})
        campaign_config = workflow_request.get("config", {})
        
        # Execute MAO campaign activities
        try:
            # Step 1: Validate campaign configuration
            validated_config = await workflow.execute_activity(
                "validate_campaign_config",
                {"campaign_name": campaign_name, "config": campaign_config},
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Step 2: Analyze target audience
            audience_analysis = await workflow.execute_activity(
                "analyze_target_audience",
                {"campaign_name": campaign_name, "audience": target_audience},
                start_to_close_timeout=timedelta(minutes=3)
            )
            
            # Step 3: Create campaign content
            content_result = await workflow.execute_activity(
                "create_campaign_content",
                {
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "audience_analysis": audience_analysis,
                    "config": validated_config
                },
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Step 4: Setup campaign infrastructure
            infrastructure_result = await workflow.execute_activity(
                "setup_campaign_infrastructure",
                {"campaign_name": campaign_name, "content": content_result},
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Step 5: Execute campaign
            execution_result = await workflow.execute_activity(
                "execute_campaign",
                {
                    "campaign_name": campaign_name,
                    "infrastructure": infrastructure_result,
                    "audience": target_audience
                },
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            # Step 6: Monitor campaign performance
            monitoring_result = await workflow.execute_activity(
                "monitor_campaign_performance",
                {"campaign_name": campaign_name, "execution": execution_result},
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            result = {
                "workflow_id": workflow.info().workflow_id,
                "campaign_name": campaign_name,
                "campaign_type": campaign_type,
                "status": "completed",
                "execution": execution_result,
                "monitoring": monitoring_result,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"MAO workflow completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"MAO workflow failed: {e}")
            raise