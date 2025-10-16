"""
⚠️ WE DO NOT MOCK - Real Multi-Agent Orchestrator (MAO) service implementation.

This service manages the lifecycle of multi-agent projects using Temporal workflows.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid

from temporalio.client import Client as TemporalClient, WorkflowHandle
from temporalio.common import RetryPolicy

from workflows.project_workflow import (
    ProjectWorkflow,
    ProjectConfig,
    TaskDefinition,
    ExecutionMode,
)


# Pydantic models for API

class TaskRequest(BaseModel):
    """Request model for task definition."""
    task_id: Optional[str] = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    capsule_id: str = Field(..., description="ID of the capsule to execute")
    persona_id: str = Field(..., description="ID of the persona to use")
    description: str = Field(..., description="Task description")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    timeout_seconds: int = Field(default=3600, description="Task timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ProjectRequest(BaseModel):
    """Request model for project creation."""
    project_name: str = Field(..., description="Name of the project")
    tasks: List[TaskRequest] = Field(..., description="List of tasks to execute")
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.DAG,
        description="Execution mode: sequential, parallel, or dag"
    )
    workspace_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="VSCode workspace configuration"
    )
    git_repo_url: Optional[str] = Field(
        default=None,
        description="Git repository URL to clone"
    )
    artifact_storage: str = Field(
        default="s3://somagent-artifacts",
        description="Storage location for artifacts"
    )
    notify_webhooks: Optional[List[str]] = Field(
        default=None,
        description="Webhook URLs for notifications"
    )
    max_parallel_tasks: int = Field(
        default=5,
        description="Maximum parallel tasks in DAG mode"
    )


class ProjectResponse(BaseModel):
    """Response model for project."""
    project_id: str
    project_name: str
    workflow_id: str
    run_id: str
    status: str
    created_at: datetime


class ProjectStatusResponse(BaseModel):
    """Response model for project status."""
    project_id: str
    workflow_id: str
    current_status: str
    workspace_id: Optional[str]
    completed_tasks: int
    total_tasks: int
    task_results: Dict[str, Any]


# FastAPI app

app = FastAPI(
    title="Multi-Agent Orchestrator (MAO) Service",
    description="Orchestrates multi-agent projects using Temporal workflows",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Temporal client
temporal_client: Optional[TemporalClient] = None


@app.on_event("startup")
async def startup_event():
    """Initialize Temporal client on startup."""
    global temporal_client
    
    temporal_client = await TemporalClient.connect(
        "localhost:7233",  # Temporal server address
        namespace="default",
    )
    
    print("✅ Connected to Temporal server")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if temporal_client:
        await temporal_client.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Temporal connection
        await temporal_client.list_workflows()
        return {
            "status": "healthy",
            "temporal": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/v1/projects", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """
    Create and start a new multi-agent project.
    
    This endpoint:
    1. Validates the project configuration
    2. Starts a Temporal workflow
    3. Returns project ID and workflow information
    """
    try:
        # Generate unique project ID
        project_id = f"project-{uuid.uuid4().hex[:12]}"
        workflow_id = f"workflow-{project_id}"
        
        # Convert request to workflow config
        config = ProjectConfig(
            project_id=project_id,
            project_name=request.project_name,
            tasks=[
                TaskDefinition(
                    task_id=task.task_id,
                    capsule_id=task.capsule_id,
                    persona_id=task.persona_id,
                    description=task.description,
                    dependencies=task.dependencies,
                    timeout_seconds=task.timeout_seconds,
                    retry_attempts=task.retry_attempts,
                    metadata=task.metadata,
                )
                for task in request.tasks
            ],
            execution_mode=request.execution_mode,
            workspace_config=request.workspace_config,
            git_repo_url=request.git_repo_url,
            artifact_storage=request.artifact_storage,
            notify_webhooks=request.notify_webhooks,
            max_parallel_tasks=request.max_parallel_tasks,
        )
        
        # Start Temporal workflow
        handle = await temporal_client.start_workflow(
            ProjectWorkflow.run,
            config,
            id=workflow_id,
            task_queue="mao-task-queue",
            retry_policy=RetryPolicy(
                maximum_attempts=1,  # Don't retry entire workflow
            ),
        )
        
        return ProjectResponse(
            project_id=project_id,
            project_name=request.project_name,
            workflow_id=workflow_id,
            run_id=handle.first_execution_run_id,
            status="running",
            created_at=datetime.utcnow(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )


@app.get("/v1/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """
    Get the current status of a project.
    
    Queries the Temporal workflow for real-time status.
    """
    try:
        workflow_id = f"workflow-{project_id}"
        
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Query workflow status
        status = await handle.query(ProjectWorkflow.get_status)
        
        return ProjectStatusResponse(
            project_id=project_id,
            workflow_id=workflow_id,
            current_status=status["current_status"],
            workspace_id=status.get("workspace_id"),
            completed_tasks=status.get("completed_tasks", 0),
            total_tasks=len(status.get("task_results", {})),
            task_results=status.get("task_results", {}),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {str(e)}"
        )


@app.post("/v1/projects/{project_id}/cancel")
async def cancel_project(project_id: str):
    """
    Cancel a running project.
    
    Sends cancellation signal to the Temporal workflow.
    """
    try:
        workflow_id = f"workflow-{project_id}"
        
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Send cancellation signal
        await handle.signal(ProjectWorkflow.cancel_workflow)
        
        return {
            "project_id": project_id,
            "status": "cancellation_requested",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel project: {str(e)}"
        )


@app.get("/v1/projects/{project_id}/result")
async def get_project_result(project_id: str):
    """
    Get the final result of a completed project.
    
    Waits for workflow completion and returns the result.
    """
    try:
        workflow_id = f"workflow-{project_id}"
        
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Wait for result (with timeout)
        result = await asyncio.wait_for(
            handle.result(),
            timeout=60.0  # 1 minute timeout
        )
        
        return {
            "project_id": project_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Timeout waiting for project result"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project result: {str(e)}"
        )


@app.get("/v1/projects")
async def list_projects(
    limit: int = 10,
    status: Optional[str] = None
):
    """
    List recent projects.
    
    Queries Temporal for workflow executions.
    """
    try:
        # List workflows
        workflows = []
        async for workflow in temporal_client.list_workflows(
            f'WorkflowType="ProjectWorkflow"'
        ):
            workflows.append({
                "workflow_id": workflow.id,
                "project_id": workflow.id.replace("workflow-", ""),
                "status": workflow.status.name,
                "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                "close_time": workflow.close_time.isoformat() if workflow.close_time else None,
            })
            
            if len(workflows) >= limit:
                break
        
        return {
            "projects": workflows,
            "count": len(workflows),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )


# WebSocket endpoint for real-time updates

active_connections: Dict[str, List[WebSocket]] = {}


@app.websocket("/v1/projects/{project_id}/stream")
async def project_stream(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time project updates.
    
    Streams workflow status changes to connected clients.
    """
    await websocket.accept()
    
    # Register connection
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)
    
    try:
        workflow_id = f"workflow-{project_id}"
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Stream updates
        while True:
            try:
                # Query status
                status = await handle.query(ProjectWorkflow.get_status)
                
                # Send to client
                await websocket.send_json({
                    "type": "status_update",
                    "project_id": project_id,
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
                # Check if workflow is complete
                if status["current_status"] in ["completed", "failed", "cancelled"]:
                    break
                
                # Wait before next update
                await asyncio.sleep(2)
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                break
        
    except WebSocketDisconnect:
        pass
    finally:
        # Unregister connection
        if project_id in active_connections:
            active_connections[project_id].remove(websocket)
            if not active_connections[project_id]:
                del active_connections[project_id]


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "10007")) # Default to 10007 if not set
    uvicorn.run(app, host="0.0.0.0", port=port)
