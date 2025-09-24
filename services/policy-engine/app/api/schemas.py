"""Schemas for policy evaluation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PolicyEvaluationRequest(BaseModel):
    action_id: str
    capability: str
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    budget_required: float = Field(ge=0.0)
    budget_remaining: Optional[float] = None
    requires_human: bool = False
    deployment_mode: str = "developer-light"


class PolicyEvaluationResponse(BaseModel):
    score: float
    allow: bool
    threshold: float
    reasons: list[str]
