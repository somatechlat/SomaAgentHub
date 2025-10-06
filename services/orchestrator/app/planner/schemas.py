"""Shared data models for planner inputs and outputs."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlanStatus(str, Enum):
    """High-level lifecycle for project plans."""

    DRAFT = "draft"
    INTAKE = "intake"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlannerRequest(BaseModel):
    """User intent and metadata delivered to the planner."""

    tenant: str
    session_id: str
    user_prompt: str
    persona: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolDescriptor(BaseModel):
    """Represents a tool that is available or recommended."""

    name: str
    category: str
    status: str  # e.g., available, missing_credentials, unsupported
    details: Dict[str, Any] = Field(default_factory=dict)


class PlannerContext(BaseModel):
    """Aggregated environment context for the planner."""

    capsule_candidates: List[Dict[str, Any]]
    available_tools: List[ToolDescriptor]
    memory_snippets: List[str] = Field(default_factory=list)
    tenant_defaults: Dict[str, Any] = Field(default_factory=dict)


class WizardQuestion(BaseModel):
    """Metadata for a wizard question supplied by capsules."""

    module_id: str
    question_id: str
    prompt: str
    type: str
    options: Optional[List[Any]] = None
    default: Optional[Any] = None
    depends_on: List[str] = Field(default_factory=list)


class ModuleSpec(BaseModel):
    """Single module within a project plan."""

    module_id: str
    title: str
    summary: Optional[str] = None
    status: PlanStatus = PlanStatus.DRAFT
    dependencies: List[str] = Field(default_factory=list)
    provisioning_capsule: Optional[str] = None
    wizard_questions: List[WizardQuestion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolSuggestion(BaseModel):
    """Suggested tool bindings for a capability area."""

    capability: str
    preferred_tool: str
    alternatives: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RiskRecord(BaseModel):
    """Captures risks or blockers identified by the LLM planner."""

    description: str
    severity: str = "medium"
    mitigation: Optional[str] = None


class ProjectPlan(BaseModel):
    """Top-level structure returned by the planner."""

    plan_id: str
    tenant: str
    capsule: str
    objective: str
    status: PlanStatus = PlanStatus.DRAFT
    modules: List[ModuleSpec] = Field(default_factory=list)
    tool_suggestions: List[ToolSuggestion] = Field(default_factory=list)
    risks: List[RiskRecord] = Field(default_factory=list)
    wizard_queue: List[WizardQuestion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
