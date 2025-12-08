"""
Multi-Agent Orchestration (MAO) API endpoints.

This module provides REST API endpoints for starting and managing MAO workflows,
including event emission for orchestration lifecycle events.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.contracts.orchestrator import OrchestrationStartedEvent
from services.common.events.outbox import OutboxEvent

from ..database import get_session
from ..repository.outbox_event_repository import OutboxEventRepository
from ..workflows.mao import (
    AgentDirective,
    MAOStartInput,
)

router = APIRouter(prefix="/v1/mao", tags=["orchestration"])


class MAOStartRequest(BaseModel):
    """Request model for starting multi-agent orchestration."""

    tenant: str = Field(..., description="Tenant identifier")
    initiator: str = Field(..., description="User ID initiating the orchestration")
    directives: list[dict[str, Any]] = Field(
        ..., description="List of agent directives"
    )
    notification_channel: str | None = Field(None, description="Notification channel")
    metadata: dict[str, Any] = Field(
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
    capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


async def emit_orchestration_started_event(
    orchestration_id: str,
    project_id: str,
    workflow_type: str,
    agent_ids: list[str],
    input_data: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Emit orchestration started event using outbox pattern."""
    event_data = OrchestrationStartedEvent(
        mao_id=orchestration_id,
        project_id=project_id,
        workflow_type=workflow_type,
        agent_ids=agent_ids,
        input_data=input_data,
        timestamp=datetime.now(UTC).isoformat(),
    )

    OutboxEvent(
        event_type="orchestration.started",
        aggregate_id=orchestration_id,
        event_data=event_data.dict(),
        created_at=datetime.now(UTC),
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
        MAOStartInput(
            orchestration_id=orchestration_id,
            tenant=request.tenant,
            initiator=request.initiator,
            directives=agent_directives,
            notification_channel=request.notification_channel,
            metadata=request.metadata,
        )

        # Start Temporal workflow
        from temporalio.client import Client

        from ..core.config import settings

        temporal_url = getattr(settings, "temporal_url", "localhost:7233")
        client = await Client.connect(temporal_url)

        await client.start_workflow(
            "multi-agent-orchestration-workflow",
            MAOStartInput(
                orchestration_id=orchestration_id,
                tenant=request.tenant,
                initiator=request.initiator,
                directives=agent_directives,
                notification_channel=request.notification_channel,
                metadata=request.metadata,
            ),
            id=orchestration_id,
            task_queue="mao-task-queue",
        )

        return MAOStartResponse(
            orchestration_id=orchestration_id,
            status="started",
            message="Orchestration started successfully",
            estimated_duration=None,
            workflow_url=f"/v1/mao/{orchestration_id}/status",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start orchestration: {str(e)}",
        )


@router.get("/{orchestration_id}/status")
async def get_orchestration_status(
    orchestration_id: str, db_session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """Get current status of an orchestration."""
    from temporalio.client import Client

    from ..core.config import settings

    try:
        temporal_url = getattr(settings, "temporal_url", "localhost:7233")
        client = await Client.connect(temporal_url)
        handle = client.get_workflow_handle(orchestration_id)
        desc = await handle.describe()

        return {
            "orchestration_id": orchestration_id,
            "status": desc.status.name,
            "start_time": desc.start_time.isoformat() if desc.start_time else None,
            "close_time": desc.close_time.isoformat() if desc.close_time else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Orchestration not found or error: {str(e)}"
        )


@router.post("/{orchestration_id}/cancel")
async def cancel_orchestration(
    orchestration_id: str, db_session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    """Cancel a running orchestration."""
    from temporalio.client import Client

    from ..core.config import settings

    try:
        temporal_url = getattr(settings, "temporal_url", "localhost:7233")
        client = await Client.connect(temporal_url)
        handle = client.get_workflow_handle(orchestration_id)
        await handle.cancel()
        return {"status": "cancelled", "orchestration_id": orchestration_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel orchestration: {str(e)}"
        )
