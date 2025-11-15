"""
Workflow Engine Service - Consolidated orchestrator, mao-service, and kamachiq-service
Supports multiple workflow types: capsule, mao, kamachiq, taxi-builder
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Dict, Any, List, Optional

# Consolidated workflow engines
from .workflows.capsule_engine import CapsuleWorkflowEngine
from .workflows.mao_engine import MAOWorkflowEngine  
from .workflows.kamachiq_engine import KamachiqWorkflowEngine
from .workflows.taxi_builder_engine import TaxiBuilderWorkflowEngine
from .workflows.dynamic_engine import DynamicWorkflowEngine

# Consolidated activity handlers
from .activities.capsule_activities import CapsuleActivities
from .activities.mao_activities import MAOActivities
from .activities.kamachiq_activities import KamachiqActivities
from .activities.taxi_builder_activities import TaxiBuilderActivities
from .activities.agent_activities import AgentActivities

# Configuration
from .core.config import WorkflowEngineConfig
from .core.multi_tenant import MultiTenantManager
from .core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

class WorkflowEngineService:
    """Consolidated workflow engine service"""
    
    def __init__(self):
        self.config = WorkflowEngineConfig()
        self.tenant_manager = MultiTenantManager()
        self.resource_manager = ResourceManager()
        
        # Initialize workflow engines
        self.workflow_engines = {
            "capsule": CapsuleWorkflowEngine(),
            "mao": MAOWorkflowEngine(),
            "kamachiq": KamachiqWorkflowEngine(),
            "taxi_builder": TaxiBuilderWorkflowEngine(),
            "dynamic": DynamicWorkflowEngine()
        }
        
        # Initialize activity handlers
        self.activity_handlers = {
            "capsule": CapsuleActivities(),
            "mao": MAOActivities(),
            "kamachiq": KamachiqActivities(),
            "taxi_builder": TaxiBuilderActivities(),
            "agent": AgentActivities()
        }
    
    async def start_workflow(self, workflow_type: str, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Start workflow of specified type"""
        
        # Validate workflow type
        if workflow_type not in self.workflow_engines:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {workflow_type}")
        
        # Get workflow engine
        engine = self.workflow_engines[workflow_type]
        
        # Validate tenant access
        tenant_context = await self.tenant_manager.validate_tenant_access(workflow_request)
        
        # Check resource availability
        await self.resource_manager.check_resources(tenant_context, workflow_request)
        
        # Start workflow
        workflow_result = await engine.start_workflow(workflow_request, tenant_context)
        
        return {
            "workflow_id": workflow_result["workflow_id"],
            "workflow_type": workflow_type,
            "status": "started",
            "tenant_id": tenant_context.tenant_id,
            "estimated_duration": workflow_result["estimated_duration"],
            "resource_allocation": workflow_result["resource_allocation"]
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        
        # Find workflow type by ID
        workflow_type = await self._get_workflow_type(workflow_id)
        
        if not workflow_type:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
        
        # Get workflow engine
        engine = self.workflow_engines[workflow_type]
        
        # Get workflow status
        status = await engine.get_workflow_status(workflow_id)
        
        return status
    
    async def list_workflows(self, tenant_id: str, workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflows for tenant"""
        
        workflows = []
        
        # If workflow type specified, query specific engine
        if workflow_type:
            if workflow_type not in self.workflow_engines:
                raise HTTPException(status_code=400, detail=f"Unknown workflow type: {workflow_type}")
            
            engine = self.workflow_engines[workflow_type]
            workflows.extend(await engine.list_workflows(tenant_id))
        else:
            # Query all workflow engines
            for wt, engine in self.workflow_engines.items():
                workflows.extend(await engine.list_workflows(tenant_id))
        
        return workflows
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel workflow"""
        
        # Find workflow type by ID
        workflow_type = await self._get_workflow_type(workflow_id)
        
        if not workflow_type:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
        
        # Get workflow engine
        engine = self.workflow_engines[workflow_type]
        
        # Cancel workflow
        result = await engine.cancel_workflow(workflow_id)
        
        return result
    
    async def _get_workflow_type(self, workflow_id: str) -> Optional[str]:
        """Get workflow type by ID"""
        
        # Check all workflow engines
        for workflow_type, engine in self.workflow_engines.items():
            if await engine.has_workflow(workflow_id):
                return workflow_type
        
        return None

# FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Workflow Engine Service")
    
    # Initialize workflow engines
    workflow_service = WorkflowEngineService()
    app.state.workflow_service = workflow_service
    
    yield
    
    logger.info("Shutting down Workflow Engine Service")

app = FastAPI(
    title="SomaAgentHub Workflow Engine",
    description="Consolidated workflow orchestration service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
@app.post("/v1/workflows/{workflow_type}")
async def start_workflow(
    workflow_type: str,
    workflow_request: Dict[str, Any],
    workflow_service: WorkflowEngineService = Depends(lambda: app.state.workflow_service)
):
    """Start workflow of specified type"""
    return await workflow_service.start_workflow(workflow_type, workflow_request)

@app.get("/v1/workflows/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    workflow_service: WorkflowEngineService = Depends(lambda: app.state.workflow_service)
):
    """Get workflow status"""
    return await workflow_service.get_workflow_status(workflow_id)

@app.get("/v1/workflows")
async def list_workflows(
    tenant_id: str,
    workflow_type: Optional[str] = None,
    workflow_service: WorkflowEngineService = Depends(lambda: app.state.workflow_service)
):
    """List workflows for tenant"""
    return await workflow_service.list_workflows(tenant_id, workflow_type)

@app.delete("/v1/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    workflow_service: WorkflowEngineService = Depends(lambda: app.state.workflow_service)
):
    """Cancel workflow"""
    return await workflow_service.cancel_workflow(workflow_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "workflow-engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)