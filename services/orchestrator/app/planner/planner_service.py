"""High-level orchestration for project planning using LLM outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .client import PlannerClient
from .schemas import PlannerContext, PlannerRequest, ProjectPlan


@dataclass
class PlannerService:
    """Coordinates planning requests and parses responses into structured plans."""

    client: PlannerClient

    async def generate_plan(
        self,
        request: PlannerRequest,
        context: PlannerContext,
    ) -> ProjectPlan:
        """Produce a structured project plan.

        Args:
            request: The user-facing prompt and metadata describing the project intent.
            context: Environment context (tools, memory, capsule metadata).

        Returns:
            A ``ProjectPlan`` with modules, tool suggestions, and wizard question queue.
        """

        # The actual implementation will format prompts, call ``self.client.complete``
        # and parse structured JSON. This placeholder keeps interfaces stable while the
        # LLM integration work proceeds.
        raise NotImplementedError("PlannerService.generate_plan is pending implementation")

    async def refine_plan(
        self,
        plan: ProjectPlan,
        updates: Dict[str, Any],
        *,
        context: Optional[PlannerContext] = None,
    ) -> ProjectPlan:
        """Allow iterative refinement when users adjust requirements mid-intake."""

        raise NotImplementedError("PlannerService.refine_plan is pending implementation")
