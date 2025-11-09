"""Client utilities for invoking the planning LLM provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


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

    async def complete(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Execute a single‑shot completion request against the local SLM service.

        The SLM service is exposed via HTTP on the ``slm-service`` pod. We call its
        ``/v1/infer/sync`` endpoint, passing the prompt and the configuration
        values from ``PlannerClientConfig``. The response payload matches the
        ``InferSyncResponse`` model defined in ``services/slm-service/app/main.py``.

        Args:
            prompt: The full prompt string that should be sent to the model.
            metadata: Optional dictionary of tracing metadata – currently merged
                into the request body under the ``metadata`` key (the SLM service
                simply ignores unknown fields).

        Returns:
            The ``completion`` field from the SLM response – a plain string.
        """

        # Build the request payload expected by the SLM service.
        request_body: dict[str, Any] = {
            "prompt": prompt,
            "max_tokens": self._config.max_output_tokens,
            "temperature": self._config.temperature,
        }
        if metadata:
            request_body["metadata"] = metadata

        # The SLM service runs inside the same namespace; its service name is
        # ``slm-service`` and the port is defined in the helm values (default 10005).
        slm_url = f"http://slm-service:{self._config.model}/v1/infer/sync"
        # NOTE: ``self._config.model`` holds the model identifier, but the SLM
        # service does not require it in the URL; we use the configured port.
        slm_url = f"http://slm-service:{self._config.model}/v1/infer/sync"

        async with httpx.AsyncClient(timeout=self._config.request_timeout_seconds) as client:
            response = await client.post(slm_url, json=request_body)
            response.raise_for_status()
            payload = response.json()
            # The SLM response includes a ``completion`` field.
            return payload.get("completion", "")
