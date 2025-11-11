"""
Multi-Agent Orchestration (MAO) API endpoints.

This module provides REST API endpoints for starting and managing MAO workflows,
including event emission for orchestration lifecycle events.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.contracts.orchestrator import OrchestrationStartedEvent
from ..repository.outbox import OutboxEvent
from ..workflows.mao import (
    MAOStartInput,
    AgentDirective,
    MultiAgentWorkflow,
)
from ..repository.outbox_event_repository import OutboxEventRepository
from ..database import get_session
from services.common.config.base_settings import resolve_env

router = APIRouter(prefix="/v1/mao", tags=["orchestration"])


class MAOStartRequest(BaseModel):
    """Request model for starting multi-agent orchestration."""

    tenant: str = Field(..., description="Tenant identifier")
    initiator: str = Field(..., description="User ID initiating the orchestration")
    directives: List[Dict[str, Any]] = Field(
        ..., description="List of agent directives"
    )
    notification_channel: str | None = Field(None, description="Notification channel")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    project_id: str = Field(
        ..., description="Project ID associated with this orchestration"
    )


class MAOStartResponse(BaseModel):
    """Response model for MAO start request."""

    orchestration_id: str
    status: str
    message: str
    estimated_duration: int | None = None
    workflow_url: str | None = None


class AgentDirectiveModel(BaseModel):
    """Pydantic model for agent directive."""

    agent_id: str
    goal: str
    prompt: str
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def emit_orchestration_started_event(
    orchestration_id: str,
    project_id: str,
    workflow_type: str,
    agent_ids: List[str],
    input_data: Dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Emit orchestration started event using outbox pattern."""
    event_data = OrchestrationStartedEvent(
        mao_id=orchestration_id,
        project_id=project_id,
        workflow_type=workflow_type,
        agent_ids=agent_ids,
        input_data=input_data,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    outbox_event = OutboxEvent(
        event_type="orchestration.started",
        aggregate_id=orchestration_id,
        event_data=event_data.dict(),
        created_at=datetime.now(timezone.utc),
    )

    outbox_repo = OutboxEventRepository(session=db_session)
    await outbox_repo.create_event(
        event_type="orchestration.started",
        topic="orchestration.events",
        key=orchestration_id,
        payload=event_data.dict(),
    )


@router.post("/start", response_model=MAOStartResponse)
async def start_orchestration(
    request: MAOStartRequest, db_session: AsyncSession = Depends(get_session)
) -> MAOStartResponse:
    """
    Start a new multi-agent orchestration workflow.

    This endpoint:
    1. Validates the request
    2. Creates a new orchestration instance
    3. Emits orchestration.started event
    4. Starts the Temporal workflow
    """
    try:
        # Generate unique orchestration ID
        orchestration_id = str(uuid.uuid4())

        # Convert directives to AgentDirective objects
        agent_directives = []
        agent_ids = []

        for directive_data in request.directives:
            directive = AgentDirective(
                agent_id=directive_data["agent_id"],
                goal=directive_data["goal"],
                prompt=directive_data["prompt"],
                capabilities=directive_data.get("capabilities", []),
                metadata=directive_data.get("metadata", {}),
            )
            agent_directives.append(directive)
            agent_ids.append(directive.agent_id)

        # Prepare input data for event
        input_data = {
            "tenant": request.tenant,
            "initiator": request.initiator,
            "directives": request.directives,
            "metadata": request.metadata,
            "project_id": request.project_id,
        }

        # Emit orchestration started event
        await emit_orchestration_started_event(
            orchestration_id=orchestration_id,
            project_id=request.project_id,
            workflow_type="multi_agent_orchestration",
            agent_ids=agent_ids,
            input_data=input_data,
            db_session=db_session,
        )

        # Create MAO input
        mao_input = MAOStartInput(
            orchestration_id=orchestration_id,
            tenant=request.tenant,
            initiator=request.initiator,
            directives=agent_directives,
            notification_channel=request.notification_channel,
            metadata=request.metadata,
        )

        # Start Temporal workflow (simplified - would use Temporal client in real implementation)
        # For now, we'll simulate workflow start
        workflow_id = f"mao-{orchestration_id}"

        return MAOStartResponse(
            orchestration_id=orchestration_id,
            status="started",
            message="Multi-agent orchestration started successfully",
            estimated_duration=3600,  # 1 hour in seconds
            workflow_url=f"/v1/workflows/{workflow_id}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start orchestration: {str(e)}",
        )


@router.get("/{orchestration_id}/status")
async def get_orchestration_status(
    orchestration_id: str, db_session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get current status of an orchestration."""
    # This would integrate with Temporal workflow queries
    # For now, return mock data
    return {
        "orchestration_id": orchestration_id,
        "status": "running",
        "progress": {"completed_agents": 2, "total_agents": 5, "percentage": 40},
        "agents": [
            {"agent_id": "agent-1", "status": "completed"},
            {"agent_id": "agent-2", "status": "completed"},
            {"agent_id": "agent-3", "status": "running"},
            {"agent_id": "agent-4", "status": "pending"},
            {"agent_id": "agent-5", "status": "pending"},
        ],
    }


@router.post("/{orchestration_id}/cancel")
async def cancel_orchestration(
    orchestration_id: str, db_session: AsyncSession = Depends(get_session)
) -> Dict[str, str]:
    """Cancel a running orchestration."""
    # This would integrate with Temporal workflow cancellation
    return {
        "orchestration_id": orchestration_id,
        "status": "cancelled",
        "message": "Orchestration cancelled successfully",
    }
