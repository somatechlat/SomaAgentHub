"""
Capsule Workflow Engine - Handles capsule creation and management workflows
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

logger = logging.getLogger(__name__)

class CapsuleWorkflowEngine:
    """Capsule workflow engine implementation"""
    
    def __init__(self):
        self.client = None
        self.worker = None
        self.active_workflows = {}
        self.workflow_queue = asyncio.Queue()
    
    async def initialize(self):
        """Initialize temporal client and worker"""
        try:
            self.client = await Client.connect("localhost:7233")
            
            # Start worker for capsule workflows
            task_queue = "capsule-workflow-queue"
            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=[CapsuleWorkflow],
                activities=[CapsuleActivities]
            )
            
            asyncio.create_task(self.worker.run())
            logger.info("Capsule workflow engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize capsule workflow engine: {e}")
            raise
    
    async def start_workflow(self, workflow_request: Dict[str, Any], tenant_context: Any) -> Dict[str, Any]:
        """Start capsule workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        try:
            # Start temporal workflow
            handle = await self.client.start_workflow(
                CapsuleWorkflow.run,
                workflow_request,
                id=workflow_id,
                task_queue="capsule-workflow-queue"
            )
            
            # Store workflow metadata
            self.active_workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_type": "capsule",
                "tenant_id": tenant_context.tenant_id,
                "status": "running",
                "started_at": datetime.utcnow(),
                "workflow_request": workflow_request,
                "handle": handle
            }
            
            return {
                "workflow_id": workflow_id,
                "estimated_duration": 300,  # 5 minutes
                "resource_allocation": {
                    "cpu": 2,
                    "memory": "4GB",
                    "storage": "10GB"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start capsule workflow: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get capsule workflow status"""
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow_meta = self.active_workflows[workflow_id]
        
        try:
            # Get workflow status from temporal
            description = await workflow_meta["handle"].describe()
            
            status = {
                "workflow_id": workflow_id,
                "workflow_type": "capsule",
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
                "workflow_type": "capsule",
                "status": "error",
                "error": str(e)
            }
    
    async def list_workflows(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List capsule workflows for tenant"""
        
        workflows = []
        
        for workflow_id, meta in self.active_workflows.items():
            if meta["tenant_id"] == tenant_id:
                workflows.append(await self.get_workflow_status(workflow_id))
        
        return workflows
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel capsule workflow"""
        
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
class CapsuleWorkflow:
    """Capsule workflow definition"""
    
    @workflow.run
    async def run(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Run capsule workflow"""
        
        logger.info(f"Starting capsule workflow: {workflow_request}")
        
        # Extract capsule parameters
        capsule_name = workflow_request.get("capsule_name")
        capsule_type = workflow_request.get("capsule_type", "general")
        capsule_config = workflow_request.get("config", {})
        
        # Execute capsule creation activities
        try:
            # Step 1: Validate capsule configuration
            validated_config = await workflow.execute_activity(
                "validate_capsule_config",
                {"capsule_name": capsule_name, "config": capsule_config},
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Step 2: Create capsule infrastructure
            infrastructure_result = await workflow.execute_activity(
                "create_capsule_infrastructure",
                {"capsule_name": capsule_name, "config": validated_config},
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Step 3: Initialize capsule services
            services_result = await workflow.execute_activity(
                "initialize_capsule_services",
                {"capsule_name": capsule_name, "infrastructure": infrastructure_result},
                start_to_close_timeout=timedelta(minutes=3)
            )
            
            # Step 4: Configure capsule
            configuration_result = await workflow.execute_activity(
                "configure_capsule",
                {"capsule_name": capsule_name, "services": services_result, "config": validated_config},
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Step 5: Deploy capsule
            deployment_result = await workflow.execute_activity(
                "deploy_capsule",
                {"capsule_name": capsule_name, "configuration": configuration_result},
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            result = {
                "workflow_id": workflow.info().workflow_id,
                "capsule_name": capsule_name,
                "capsule_type": capsule_type,
                "status": "completed",
                "deployment": deployment_result,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Capsule workflow completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Capsule workflow failed: {e}")
            raise