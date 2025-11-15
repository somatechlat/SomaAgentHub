"""
Dynamic Workflow Engine - Handles custom and dynamic workflows
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

class DynamicWorkflowEngine:
    """Dynamic workflow engine implementation"""
    
    def __init__(self):
        self.client = None
        self.worker = None
        self.active_workflows = {}
        self.workflow_queue = asyncio.Queue()
        self.workflow_templates = {}
    
    async def initialize(self):
        """Initialize temporal client and worker"""
        try:
            self.client = await Client.connect("localhost:7233")
            
            # Start worker for dynamic workflows
            task_queue = "dynamic-workflow-queue"
            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=[DynamicWorkflow],
                activities=[AgentActivities]
            )
            
            asyncio.create_task(self.worker.run())
            logger.info("Dynamic workflow engine initialized")
            
            # Load workflow templates
            await self._load_workflow_templates()
            
        except Exception as e:
            logger.error(f"Failed to initialize dynamic workflow engine: {e}")
            raise
    
    async def start_workflow(self, workflow_request: Dict[str, Any], tenant_context: Any) -> Dict[str, Any]:
        """Start dynamic workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        try:
            # Start temporal workflow
            handle = await self.client.start_workflow(
                DynamicWorkflow.run,
                workflow_request,
                id=workflow_id,
                task_queue="dynamic-workflow-queue"
            )
            
            # Store workflow metadata
            self.active_workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_type": "dynamic",
                "tenant_id": tenant_context.tenant_id,
                "status": "running",
                "started_at": datetime.utcnow(),
                "workflow_request": workflow_request,
                "handle": handle
            }
            
            # Estimate duration based on workflow complexity
            estimated_duration = self._estimate_workflow_duration(workflow_request)
            
            return {
                "workflow_id": workflow_id,
                "estimated_duration": estimated_duration,
                "resource_allocation": self._estimate_resource_requirements(workflow_request)
            }
            
        except Exception as e:
            logger.error(f"Failed to start dynamic workflow: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get dynamic workflow status"""
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow_meta = self.active_workflows[workflow_id]
        
        try:
            # Get workflow status from temporal
            description = await workflow_meta["handle"].describe()
            
            status = {
                "workflow_id": workflow_id,
                "workflow_type": "dynamic",
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
                "workflow_type": "dynamic",
                "status": "error",
                "error": str(e)
            }
    
    async def list_workflows(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List dynamic workflows for tenant"""
        
        workflows = []
        
        for workflow_id, meta in self.active_workflows.items():
            if meta["tenant_id"] == tenant_id:
                workflows.append(await self.get_workflow_status(workflow_id))
        
        return workflows
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel dynamic workflow"""
        
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
    
    async def _load_workflow_templates(self):
        """Load workflow templates"""
        # This could be loaded from a database or configuration file
        self.workflow_templates = {
            "agent_chain": {
                "description": "Chain multiple agents together",
                "estimated_duration": 600,
                "resource_requirements": {
                    "cpu": 4,
                    "memory": "8GB",
                    "storage": "20GB"
                }
            },
            "data_pipeline": {
                "description": "Execute data processing pipeline",
                "estimated_duration": 1800,
                "resource_requirements": {
                    "cpu": 8,
                    "memory": "16GB",
                    "storage": "100GB"
                }
            },
            "custom_workflow": {
                "description": "Execute custom workflow definition",
                "estimated_duration": 1200,
                "resource_requirements": {
                    "cpu": 6,
                    "memory": "12GB",
                    "storage": "50GB"
                }
            }
        }
    
    def _estimate_workflow_duration(self, workflow_request: Dict[str, Any]) -> int:
        """Estimate workflow duration based on request"""
        workflow_type = workflow_request.get("workflow_type", "custom_workflow")
        
        if workflow_type in self.workflow_templates:
            return self.workflow_templates[workflow_type]["estimated_duration"]
        
        # Default estimation
        return 900  # 15 minutes
    
    def _estimate_resource_requirements(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate resource requirements"""
        workflow_type = workflow_request.get("workflow_type", "custom_workflow")
        
        if workflow_type in self.workflow_templates:
            return self.workflow_templates[workflow_type]["resource_requirements"]
        
        # Default requirements
        return {
            "cpu": 4,
            "memory": "8GB",
            "storage": "20GB"
        }

@workflow.defn
class DynamicWorkflow:
    """Dynamic workflow definition"""
    
    @workflow.run
    async def run(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Run dynamic workflow"""
        
        logger.info(f"Starting dynamic workflow: {workflow_request}")
        
        # Extract dynamic workflow parameters
        workflow_type = workflow_request.get("workflow_type", "custom_workflow")
        workflow_steps = workflow_request.get("workflow_steps", [])
        workflow_config = workflow_request.get("config", {})
        
        # Execute dynamic workflow activities
        try:
            # Step 1: Validate workflow definition
            validated_definition = await workflow.execute_activity(
                "validate_workflow_definition",
                {"workflow_type": workflow_type, "steps": workflow_steps},
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Step 2: Execute workflow steps dynamically
            execution_results = []
            for step in validated_definition["steps"]:
                step_result = await workflow.execute_activity(
                    "execute_workflow_step",
                    {
                        "step": step,
                        "workflow_type": workflow_type,
                        "config": workflow_config,
                        "previous_results": execution_results
                    },
                    start_to_close_timeout=timedelta(minutes=10)
                )
                execution_results.append(step_result)
                
                # Check if step failed and handle accordingly
                if step_result.get("status") == "failed":
                    logger.error(f"Workflow step failed: {step_result}")
                    raise Exception(f"Workflow step failed: {step_result['error']}")
            
            # Step 3: Aggregate results
            aggregated_result = await workflow.execute_activity(
                "aggregate_workflow_results",
                {
                    "workflow_type": workflow_type,
                    "execution_results": execution_results,
                    "config": workflow_config
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Step 4: Generate workflow report
            report = await workflow.execute_activity(
                "generate_workflow_report",
                {
                    "workflow_type": workflow_type,
                    "aggregated_result": aggregated_result,
                    "execution_results": execution_results
                },
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            result = {
                "workflow_id": workflow.info().workflow_id,
                "workflow_type": workflow_type,
                "status": "completed",
                "execution_results": execution_results,
                "aggregated_result": aggregated_result,
                "report": report,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Dynamic workflow completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Dynamic workflow failed: {e}")
            raise