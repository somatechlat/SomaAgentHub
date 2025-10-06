"""Intake manager coordinating wizard and manual flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import IntakeAnswer, IntakeRequest, IntakeResponse, ModuleState


@dataclass
class IntakeManager:
    """Stateful helper for walking through module question flows."""

    async def next_step(self, request: IntakeRequest) -> IntakeResponse:
        """Return the next question or summary for the given plan/module state."""

        raise NotImplementedError("IntakeManager.next_step requires implementation")

    async def validate_answer(self, answer: IntakeAnswer) -> List[str]:
        """Validate an answer and return a list of error messages if invalid."""

        raise NotImplementedError("IntakeManager.validate_answer requires implementation")

    async def summarize_module(self, module: ModuleState) -> str:
        """Generate a human-readable summary for review before approval."""

        raise NotImplementedError("IntakeManager.summarize_module requires implementation")
