"""Client utilities for invoking the planning LLM provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PlannerClientConfig:
    """Configuration for the planner client."""

    model: str
    max_output_tokens: int = 2048
    temperature: float = 0.2
    top_p: float = 0.9
    request_timeout_seconds: int = 120


class PlannerClient:
    """Thin wrapper around the SLM Service or external LLM provider.

    The client is intentionally minimal: the actual orchestration of prompts, context
    assembly, and parsing belongs in ``planner_service.py``.
    """

    def __init__(self, config: PlannerClientConfig) -> None:
        self._config = config

    async def complete(self, prompt: str, *, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Execute a single-shot completion request.

        Args:
            prompt: The serialized prompt payload (usually JSON/YAML).
            metadata: Optional tracing metadata to forward to the LLM backend.

        Returns:
            The raw text completion produced by the model.

        Note:
            The implementation will be added when the SLM client integration lands.
        """

        raise NotImplementedError("PlannerClient.complete is pending integration with the SLM service")
