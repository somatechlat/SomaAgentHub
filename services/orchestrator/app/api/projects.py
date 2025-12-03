"""Project planning API endpoints (planner + wizard lifecycle)."""

from __future__ import annotations

from uuid import uuid4

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
async def analyze_project(
    payload: AnalyzeProjectRequest,
) -> AnalyzeProjectResponse:
    """Kick off the planning flow (LLM analysis + initial wizard question).

    Implementation will glue together the PlannerService, PlanRepository, and IntakeManager.
    """
    # Minimal implementation removing placeholder: synthesise initial plan snapshot
    plan_id = f"plan-{uuid4()}"
    summary = f"Plan {plan_id} created for tenant {payload.tenant}. Objective pending intake."
    return AnalyzeProjectResponse(
        plan_id=plan_id,
        capsule=None,
        objective=None,
        summary=summary,
        next_action={
            "type": "intake_question",
            "question": {
                "id": "q1",
                "text": "What is the primary objective?",
                "type": "text",
            },
        },
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
    from ..intake.manager import IntakeManager
    from ..intake.schemas import (
        IntakeAnswer,
        IntakeRequest,
        ModuleState,
    )

    manager = IntakeManager()

    # Build transient module state from payload metadata (no persistence yet)
    answered = payload.answer.get("answered", []) if payload.answer else []
    answers_map = {}
    if payload.question_id and payload.answer and "value" in payload.answer:
        answers_map[payload.question_id] = payload.answer["value"]
        if payload.question_id not in answered:
            answered.append(payload.question_id)

    request_model = IntakeRequest(
        plan_id=plan_id,
        module_id=payload.module_id,
        mode=payload.mode,
        metadata={"answered": answered},
    )

    # Provide validation when an answer is supplied
    if payload.question_id and payload.answer and "value" in payload.answer:
        validation_errors = await manager.validate_answer(
            IntakeAnswer(
                plan_id=plan_id,
                module_id=payload.module_id or "core",
                question_id=payload.question_id,
                value=payload.answer["value"],
            )
        )
        if validation_errors:
            return IntakeResponseModel(
                plan_id=plan_id,
                status="validation_failed",
                prompt="; ".join(validation_errors),
                finished=False,
            )

    next_step = await manager.next_step(request_model)
    if next_step.finished:
        summary = await manager.summarize_module(
            ModuleState(
                plan_id=plan_id,
                module_id=next_step.module_id or "core",
                status="completed",
                answers=answers_map,
                pending_questions=[],
            )
        )
        return IntakeResponseModel(
            plan_id=plan_id,
            status="completed",
            summary=summary,
            finished=True,
        )

    return IntakeResponseModel(
        plan_id=plan_id,
        status=next_step.status,
        prompt=next_step.prompt,
        question=next_step.question,
        finished=False,
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


@router.post(
    "/{plan_id}/approve",
    response_model=ApprovalResponseModel,
)
async def approve_plan(
    plan_id: str,
    payload: ApprovalRequestModel,
) -> ApprovalResponseModel:
    """Approve the plan and trigger the Temporal execution workflow."""

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Plan approval workflow not yet available",
    )
