"""API surface for the Multi-Agent Orchestrator."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_session
from .schemas import WorkflowRequest, WorkflowResponse, WorkflowStepStatus
from ..core.db import workflows, workflow_steps

router = APIRouter(prefix="/v1", tags=["mao"])


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowRequest, session: AsyncSession = Depends(get_session)) -> WorkflowResponse:
    if not payload.steps:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one step required")

    wf_result = await session.execute(
        workflows.insert().returning(workflows.c.id).values(
            name=payload.name,
            tenant_id=payload.tenant_id,
            capsule_id=payload.capsule_id,
            status="pending",
        )
    )
    wf_id = wf_result.scalar_one()

    await session.execute(
        workflow_steps.insert(),
        [
            {
                "workflow_id": wf_id,
                "step_index": step.step_index,
                "persona": step.persona,
                "instruction": step.instruction,
                "status": "pending",
            }
            for step in sorted(payload.steps, key=lambda s: s.step_index)
        ],
    )
    await session.commit()
    return await _serialize_workflow(session, wf_id)


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(session: AsyncSession = Depends(get_session)) -> List[WorkflowResponse]:
    result = await session.execute(select(workflows.c.id))
    ids = [row.id for row in result]
    return [await _serialize_workflow(session, wf_id) for wf_id in ids]


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: int, session: AsyncSession = Depends(get_session)) -> WorkflowResponse:
    return await _serialize_workflow(session, workflow_id)


async def _serialize_workflow(session: AsyncSession, workflow_id: int) -> WorkflowResponse:
    wf_row = await session.execute(select(workflows).where(workflows.c.id == workflow_id))
    wf = wf_row.fetchone()
    if wf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    steps_result = await session.execute(
        select(workflow_steps)
        .where(workflow_steps.c.workflow_id == workflow_id)
        .order_by(workflow_steps.c.step_index)
    )
    steps = [
        WorkflowStepStatus(
            step_index=row.step_index,
            persona=row.persona,
            instruction=row.instruction,
            status=row.status,
            result=row.result,
        )
        for row in steps_result
    ]

    return WorkflowResponse(
        workflow_id=wf.id,
        name=wf.name,
        tenant_id=wf.tenant_id,
        capsule_id=wf.capsule_id,
        status=wf.status,
        steps=steps,
    )
