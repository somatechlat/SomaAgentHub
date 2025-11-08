"""High-level orchestration for project planning using LLM outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..repository.plan_repository import PlanRepository
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

        The implementation builds a Jinja prompt using the ``request`` and ``context``
        objects, sends it to the ``PlannerClient`` (which talks to the local SLM
        service), parses the JSON response into a ``ProjectPlan`` model, and stores
        the result via ``PlanRepository``.
        """

        # 1️⃣ Build a simple prompt – in a real system this would be a Jinja2
        # template; for now we concatenate the fields.
        prompt_parts = [
            f"Tenant: {request.tenant}",
            f"Session: {request.session_id}",
            f"User prompt: {request.user_prompt}",
            f"Persona: {request.persona or 'default'}",
            "Available tools:" + ", ".join([t.name for t in context.available_tools]),
            "Memory snippets:" + " | ".join(context.memory_snippets),
        ]
        prompt = "\n".join(prompt_parts)

        # 2️⃣ Call the LLM via PlannerClient
        raw_response = await self.client.complete(prompt)

        # 3️⃣ The SLM returns a plain string – we expect it to be JSON.
        try:
            plan_dict = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner LLM returned invalid JSON: {exc}")

        # 4️⃣ Validate against the Pydantic schema
        plan = ProjectPlan.parse_obj(plan_dict)

        # 5️⃣ Persist the plan (store the full payload for auditability)
        repo = PlanRepository()
        await repo.create_plan(plan.model_dump())
        return plan

    async def refine_plan(
        self,
        plan: ProjectPlan,
        updates: dict[str, Any],
        *,
        context: PlannerContext | None = None,
    ) -> ProjectPlan:
        """Iteratively refine an existing plan.

        ``updates`` is a dict of fields the user changed (e.g., ``objective``
        or ``modules``). We re‑serialize the updated plan, send it to the LLM for
        a new suggestion, and replace the stored JSON.
        """

        # Merge updates into the existing plan dict
        merged = plan.model_dump()
        merged.update(updates)
        prompt = json.dumps(merged)
        raw_response = await self.client.complete(prompt)
        try:
            new_plan_dict = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Refine LLM returned invalid JSON: {exc}")
        new_plan = ProjectPlan.parse_obj(new_plan_dict)
        # Update persisted record
        repo = PlanRepository()
        await repo.delete_plan(plan.plan_id)  # simple replace strategy
        await repo.create_plan(new_plan.model_dump())
        return new_plan
