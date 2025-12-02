"""Shared data models for planner inputs and outputs."""

from __future__ import annotations

from enum import Enum
from typing import Any

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
        persona: str | None = None
        metadata: dict[str, Any] = Field(default_factory=dict)

        class ToolDescriptor(BaseModel):
    """Represents a tool that is available or recommended."""

    name: str
    category: str
    status: str  # e.g., available, missing_credentials, unsupported
    details: dict[str, Any] = Field(default_factory=dict)

    class PlannerContext(BaseModel):
        """Aggregated environment context for the planner."""

        capsule_candidates: list[dict[str, Any]]
        available_tools: list[ToolDescriptor]
        memory_snippets: list[str] = Field(default_factory=list)
        tenant_defaults: dict[str, Any] = Field(default_factory=dict)

        class WizardQuestion(BaseModel):
            """Metadata for a wizard question supplied by capsules."""

            module_id: str
            question_id: str
            prompt: str
            type: str
            options: list[Any] | None = None
            default: Any | None = None
            depends_on: list[str] = Field(default_factory=list)

            class ModuleSpec(BaseModel):
                """Single module within a project plan."""

                module_id: str
                title: str
                summary: str | None = None
                status: PlanStatus = PlanStatus.DRAFT
                dependencies: list[str] = Field(default_factory=list)
                provisioning_capsule: str | None = None
                wizard_questions: list[WizardQuestion] = Field(default_factory=list)
                metadata: dict[str, Any] = Field(default_factory=dict)

                class ToolSuggestion(BaseModel):
                    """Suggested tool bindings for a capability area."""

                    capability: str
                    preferred_tool: str
                    alternatives: list[str] = Field(default_factory=list)
                    notes: str | None = None

                    class RiskRecord(BaseModel):
                        """Captures risks or blockers identified by the LLM planner."""

                        description: str
                        severity: str = "medium"
                        mitigation: str | None = None

                        class ProjectPlan(BaseModel):
                            """Top-level structure returned by the planner."""

                            plan_id: str
                            tenant: str
                            capsule: str
                            objective: str
                            status: PlanStatus = PlanStatus.DRAFT
                            modules: list[ModuleSpec] = Field(default_factory=list)
                            tool_suggestions: list[ToolSuggestion] = Field(default_factory=list)
                            risks: list[RiskRecord] = Field(default_factory=list)
                            wizard_queue: list[WizardQuestion] = Field(default_factory=list)
                            metadata: dict[str, Any] = Field(default_factory=dict)
