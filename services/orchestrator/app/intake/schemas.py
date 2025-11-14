"""Pydantic models used by the intake engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class IntakeRequest(BaseModel):
"""Represents a request to fetch the next wizard/manual step."""

plan_id: str
module_id: str | None = None
mode: str = Field(default="wizard", description="wizard or manual")
metadata: dict[str, Any] = Field(default_factory=dict)


class IntakeAnswer(BaseModel):
"""User-provided answer to a wizard question."""

plan_id: str
module_id: str
question_id: str
value: Any
metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleState(BaseModel):
"""State tracker for a module inside the intake process."""

plan_id: str
module_id: str
status: str
answers: dict[str, Any] = Field(default_factory=dict)
pending_questions: list[str] = Field(default_factory=list)


class IntakeResponse(BaseModel):
"""Response containing the next prompt or summary for the user."""

plan_id: str
module_id: str | None = None
status: str = "pending"
prompt: str | None = None
question: dict[str, Any] | None = None
summary: str | None = None
finished: bool = False
