"""Intake manager coordinating wizard and manual flows."""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import IntakeAnswer, IntakeRequest, IntakeResponse, ModuleState


@dataclass
class IntakeManager:
    """Stateful helper for walking through module question flows."""

    async def next_step(self, request: IntakeRequest) -> IntakeResponse:
        """Return the next question or summary for the given plan/module state."""
        # Minimal deterministic wizard flow (two questions then summary)
        module_id = request.module_id or "core"
        metadata = request.metadata or {}
        answered = metadata.get("answered", [])

        # First question
        if "q1" not in answered:
            return IntakeResponse(
                plan_id=request.plan_id,
                module_id=module_id,
                status="in_progress",
                prompt="Provide the high-level project objective.",
                question={
                    "id": "q1",
                    "text": "What is the primary objective?",
                    "type": "text",
                },
                finished=False,
            )

        # Second question
        if "q2" not in answered:
            return IntakeResponse(
                plan_id=request.plan_id,
                module_id=module_id,
                status="in_progress",
                prompt="Detail success criteria to measure completion.",
                question={
                    "id": "q2",
                    "text": "List measurable success criteria.",
                    "type": "list",
                },
                finished=False,
            )

        # Summary when finished
        return IntakeResponse(
            plan_id=request.plan_id,
            module_id=module_id,
            status="completed",
            summary="Objective and success criteria captured.",
            finished=True,
        )

    async def validate_answer(self, answer: IntakeAnswer) -> list[str]:
        """Validate an answer and return a list of error messages if invalid."""
        errors: list[str] = []
        if answer.question_id == "q1":
            if not isinstance(answer.value, str) or not answer.value.strip():
                errors.append("Objective must be a non-empty string.")
            if len(str(answer.value).strip()) < 10:
                errors.append("Provide a more descriptive objective (>=10 chars).")
        elif answer.question_id == "q2":
            if not isinstance(answer.value, (list, tuple)) or len(answer.value) == 0:
                errors.append("Provide at least one success criterion.")
        return errors

    async def summarize_module(self, module: ModuleState) -> str:
        """Generate a human-readable summary for review before approval."""
        objective = module.answers.get("q1", "<missing objective>")
        criteria = module.answers.get("q2", [])
        criteria_list = ", ".join(criteria) if isinstance(criteria, list) else str(criteria)
        return f"Objective: {objective} | Success Criteria: {criteria_list}"
