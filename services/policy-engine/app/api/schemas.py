"""Pydantic schemas for the policy engine API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class PolicyRuleModel(BaseModel):
    name: str
    pattern: str
    weight: float = Field(default=0.35, ge=0.0)
    description: str | None = None
    severity: str = Field(default="medium")


class PolicyViolationModel(BaseModel):
    name: str
    pattern: str
    weight: float
    severity: str
    description: str | None = None
    excerpt: str


class EvaluationMetadata(BaseModel):
    session_id: str | None = None
    capsule_id: str | None = None
    tool: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    session_id: str
    tenant: str
    user: str
    role: str
    prompt: str
    metadata: EvaluationMetadata = Field(default_factory=EvaluationMetadata)


class EvaluationResponse(BaseModel):
    allowed: bool
    score: float
    violations: list[PolicyViolationModel]
    reasons: dict[str, Any] = Field(default_factory=dict)
    constitution_hash: str
    evaluated_at: datetime


class ScoreRequest(BaseModel):
    tenant: str
    prompt: str
    metadata: EvaluationMetadata = Field(default_factory=EvaluationMetadata)


class ScoreResponse(BaseModel):
    score: float
    violation_count: int
    severity: str
    constitution_hash: str
    violations: list[PolicyViolationModel]


class PolicyUpdateRequest(BaseModel):
    rules: list[PolicyRuleModel]
