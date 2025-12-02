"""
MAO Engine Main Entry Point.

Unified orchestration engine main application.
Provides HTTP API and CLI interface for the MAO engine.

TRUTH: Single entry point eliminates multiple service endpoints.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.mao_engine.core import mao_engine
from services.mao_engine.workflows.marketing_campaign import (
MarketingCampaignParams,
MarketingCampaignResult,
)
from services.common.config.base_settings import resolve_env


# Configure logging
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ExecuteSagaRequest(BaseModel):
    """Request model for saga execution."""

    workflow_id: str
    workflow_name: str
    input_data: dict
    timeout_seconds: Optional[int] = None


    class ExecuteSagaResponse(BaseModel):
    """Response model for saga execution."""

    workflow_id: str
    workflow_name: str
    status: str
    result: Optional[dict] = None
    error_message: Optional[str] = None


    class ExecuteActivityRequest(BaseModel):
        """Request model for activity execution."""

        activity_id: str
        activity_name: str
        input_data: dict
        workflow_id: Optional[str] = None
        timeout_seconds: Optional[int] = None


        class ExecuteActivityResponse(BaseModel):
            """Response model for activity execution."""

            activity_id: str
            activity_name: str
            status: str
            result: Optional[dict] = None
            error_message: Optional[str] = None


            class CircuitBreakerStatusRequest(BaseModel):
                """Request model for circuit breaker status."""

                service_name: str


                class CircuitBreakerStatusResponse(BaseModel):
                    """Response model for circuit breaker status."""

                    service_name: str
                    status: dict


                    @asynccontextmanager
    async def lifespan(app: FastAPI):
                            """Application lifespan manager."""
                            logger.info("Starting MAO Engine...")
                            try:
# Start the MAO engine
                                await mao_engine.start()
                                logger.info("MAO Engine started successfully")
                                yield
                                finally:
# Stop the MAO engine
                                    logger.info("Stopping MAO Engine...")
                                    await mao_engine.stop()
                                    logger.info("MAO Engine stopped")


# Create FastAPI app
                                    app = FastAPI(
                                    title="MAO Engine API",
                                    description="Unified Multi-Agent Orchestrator Engine API",
                                    version="1.0.0",
                                    lifespan=lifespan,
                                    )


                                    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "MAO Engine - Unified Orchestrator"}


        @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        stats = mao_engine.get_engine_statistics()
        return {
        "status": "healthy",
        "engine_running": stats["is_running"],
        "workers_running": stats["workers_running"],
        "temporal_connected": stats["temporal_client_connected"],
        }


        @app.post("/saga/execute", response_model=ExecuteSagaResponse)
    async def execute_saga(request: ExecuteSagaRequest):
                                            """
                                            Execute a saga workflow.

                                            TRUTH: Single endpoint for all workflow execution.
                                            """
                                            try:
                                                result = await mao_engine.execute_saga(
                                                workflow_id=request.workflow_id,
                                                workflow_name=request.workflow_name,
                                                input_data=request.input_data,
                                                timeout_seconds=request.timeout_seconds,
                                                )

                                                return ExecuteSagaResponse(
                                                workflow_id=request.workflow_id,
                                                workflow_name=request.workflow_name,
                                                status="completed",
                                                result=result,
                                                )

                                                except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute saga {request.workflow_id}: {e}")
        return ExecuteSagaResponse(
        workflow_id=request.workflow_id,
        workflow_name=request.workflow_name,
        status="failed",
        error_message=str(e),
        )


        @app.post("/activity/execute", response_model=ExecuteActivityResponse)
    async def execute_activity(request: ExecuteActivityRequest):
    """
    Execute an activity.

    TRUTH: Single endpoint for all activity execution.
    """
    try:
        result = await mao_engine.execute_activity(
        activity_id=request.activity_id,
        activity_name=request.activity_name,
        input_data=request.input_data,
        workflow_id=request.workflow_id,
        timeout_seconds=request.timeout_seconds,
        )

        return ExecuteActivityResponse(
        activity_id=request.activity_id,
        activity_name=request.activity_name,
        status="completed",
        result=result,
        )

        except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute activity {request.activity_id}: {e}")
        return ExecuteActivityResponse(
        activity_id=request.activity_id,
        activity_name=request.activity_name,
        status="failed",
        error_message=str(e),
        )


        @app.get("/workflow/{workflow_id}")
    async def get_workflow_status(workflow_id: str):
    """Get workflow status."""
    instance = mao_engine.get_workflow_status(workflow_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow not found")

        return {
        "workflow_id": instance.workflow_id,
        "workflow_name": instance.workflow_name,
        "status": instance.status.value,
        "input_data": instance.input_data,
        "output_data": instance.output_data,
        "error_message": instance.error_message,
        "start_time": instance.start_time,
        "end_time": instance.end_time,
        }


        @app.get("/workflows")
    async def list_workflows(workflow_name: Optional[str] = None, status: Optional[str] = None):
    """List workflows."""
    from services.mao_engine.core import WorkflowStatus

    workflow_status = WorkflowStatus(status) if status else None
    instances = mao_engine.list_workflows(
    workflow_name=workflow_name,
    status=workflow_status,
    )

    return {
    "workflows": [
    {
        "workflow_id": instance.workflow_id,
        "workflow_name": instance.workflow_name,
        "status": instance.status.value,
        "input_data": instance.input_data,
        "output_data": instance.output_data,
        "error_message": instance.error_message,
        "start_time": instance.start_time,
        "end_time": instance.end_time,
    }
    for instance in instances
    ]
    }


    @app.get("/activity/{activity_id}")
    async def get_activity_status(activity_id: str):
    """Get activity status."""
    instance = mao_engine.get_activity_status(activity_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Activity not found")

        return {
        "activity_id": instance.activity_id,
        "activity_name": instance.activity_name,
        "status": instance.status.value,
        "input_data": instance.input_data,
        "output_data": instance.output_data,
        "error_message": instance.error_message,
        "start_time": instance.start_time,
        "end_time": instance.end_time,
        "retry_count": instance.retry_count,
        }


        @app.get("/activities")
    async def list_activities(
    activity_name: Optional[str] = None,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    ):
    """List activities."""
    from services.mao_engine.core import ActivityStatus

    activity_status = ActivityStatus(status) if status else None
    instances = mao_engine.list_activities(
    activity_name=activity_name,
    status=activity_status,
    workflow_id=workflow_id,
    )

    return {
    "activities": [
    {
        "activity_id": instance.activity_id,
        "activity_name": instance.activity_name,
        "status": instance.status.value,
        "input_data": instance.input_data,
        "output_data": instance.output_data,
        "error_message": instance.error_message,
        "start_time": instance.start_time,
        "end_time": instance.end_time,
        "retry_count": instance.retry_count,
    }
    for instance in instances
    ]
    }


    @app.post("/circuit-breaker/status", response_model=CircuitBreakerStatusResponse)
    async def get_circuit_breaker_status(request: CircuitBreakerStatusRequest):
    """Get circuit breaker status."""
    try:
        status = mao_engine.get_circuit_breaker_status(request.service_name)
        return CircuitBreakerStatusResponse(
    service_name=request.service_name,
    status=status,
    )
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status for {request.service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


        @app.get("/stats")
    async def get_engine_statistics():
        """Get engine statistics."""
        stats = mao_engine.get_engine_statistics()
        return stats


        @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        )


    async def main():
                """Main entry point."""
# Configuration
                host = resolve_env("MAO_ENGINE_HOST", "0.0.0.0")
                port = int(resolve_env("MAO_ENGINE_PORT", "8000"))
                debug = resolve_env("MAO_ENGINE_DEBUG", "false").lower() == "true"

# Run the server
                logger.info(f"Starting MAO Engine API server on {host}:{port}")
                await uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info" if not debug else "debug",
                )


                if __name__ == "__main__":
                    asyncio.run(main())