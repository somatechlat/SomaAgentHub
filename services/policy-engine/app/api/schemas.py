"""Pydantic schemas for the policy engine API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PolicyRuleModel(BaseModel):
    name: str
    pattern: str
    weight: float = Field(default=0.35, ge=0.0)
    description: Optional[str] = None
    severity: str = Field(default="medium")


class PolicyViolationModel(BaseModel):
    name: str
    pattern: str
    weight: float
    severity: str
    description: Optional[str] = None
    excerpt: str


class EvaluationMetadata(BaseModel):
    session_id: Optional[str] = None
    capsule_id: Optional[str] = None
    tool: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


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
    violations: List[PolicyViolationModel]
    reasons: Dict[str, Any] = Field(default_factory=dict)
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
    violations: List[PolicyViolationModel]


class PolicyUpdateRequest(BaseModel):
    rules: List[PolicyRuleModel]