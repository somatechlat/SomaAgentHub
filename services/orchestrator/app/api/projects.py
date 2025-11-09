"""Project planning API endpoints (planner + wizard lifecycle)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/projects", tags=["projects"])


class AnalyzeProjectRequest(BaseModel):
    tenant: str
    session_id: str
    prompt: str
    persona: str | None = None
    metadata: dict = Field(default_factory=dict)


class AnalyzeProjectResponse(BaseModel):
    plan_id: str
    capsule: str | None = None
    objective: str | None = None
    summary: str | None = None
    next_action: dict | None = None


@router.post("/analyze", response_model=AnalyzeProjectResponse)
async def analyze_project(payload: AnalyzeProjectRequest) -> AnalyzeProjectResponse:
    """Kick off the planning flow (LLM analysis + initial wizard question).

    Implementation will glue together the PlannerService, PlanRepository, and IntakeManager.
    """

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Planner integration not yet available",
    )


class IntakeRequestModel(BaseModel):
    plan_id: str
    module_id: str | None = None
    question_id: str | None = None
    answer: dict | None = None
    mode: str = "wizard"


class IntakeResponseModel(BaseModel):
    plan_id: str
    status: str
    prompt: str | None = None
    question: dict | None = None
    summary: str | None = None
    finished: bool = False


@router.post("/{plan_id}/intake", response_model=IntakeResponseModel)
async def progress_intake(plan_id: str, payload: IntakeRequestModel) -> IntakeResponseModel:
    """Advance the wizard/manual intake flow for a plan."""

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Intake engine not yet available",
    )


class ApprovalRequestModel(BaseModel):
    plan_id: str
    approver: str
    notes: str | None = None


class ApprovalResponseModel(BaseModel):
    plan_id: str
    status: str
    workflow_id: str | None = None
    run_id: str | None = None


@router.post("/{plan_id}/approve", response_model=ApprovalResponseModel)
async def approve_plan(plan_id: str, payload: ApprovalRequestModel) -> ApprovalResponseModel:
    """Approve the plan and trigger the Temporal execution workflow."""

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Plan approval workflow not yet available",
    )
