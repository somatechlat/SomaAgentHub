"""Pydantic models used by the intake engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    """Represents a request to fetch the next wizard/manual step."""

    plan_id: str
    module_id: Optional[str] = None
    mode: str = Field(default="wizard", description="wizard or manual")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntakeAnswer(BaseModel):
    """User-provided answer to a wizard question."""

    plan_id: str
    module_id: str
    question_id: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModuleState(BaseModel):
    """State tracker for a module inside the intake process."""

    plan_id: str
    module_id: str
    status: str
    answers: Dict[str, Any] = Field(default_factory=dict)
    pending_questions: List[str] = Field(default_factory=list)


class IntakeResponse(BaseModel):
    """Response containing the next prompt or summary for the user."""

    plan_id: str
    module_id: Optional[str] = None
    status: str = "pending"
    prompt: Optional[str] = None
    question: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    finished: bool = False
