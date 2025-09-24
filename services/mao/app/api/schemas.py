"""Pydantic schemas for MAO workflows."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    step_index: int
    persona: Optional[str] = None
    instruction: str


class WorkflowRequest(BaseModel):
    name: str
    tenant_id: str
    capsule_id: Optional[str] = None
    steps: List[WorkflowStep]


class WorkflowStepStatus(BaseModel):
    step_index: int
    persona: Optional[str] = None
    instruction: str
    status: str
    result: Optional[str] = None


class WorkflowResponse(BaseModel):
    workflow_id: int
    name: str
    tenant_id: str
    capsule_id: Optional[str] = None
    status: str
    steps: List[WorkflowStepStatus]
