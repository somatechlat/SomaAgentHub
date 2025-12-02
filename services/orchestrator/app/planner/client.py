"""Client utilities for invoking the planning LLM provider via the LLM Hub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from services.common.config.base_settings import resolve_env


@dataclass
class PlannerClientConfig:
    """Configuration for the planner client."""

    model: str
    max_output_tokens: int = 2048
    temperature: float = 0.2
    top_p: float = 0.9
    request_timeout_seconds: int = 120


    class PlannerClient:
    """Thin wrapper around the centralized LLM Hub provider.

    The client is intentionally minimal: the actual orchestration of prompts, context
    assembly, and parsing belongs in ``planner_service.py``.
    """

    def __init__(self, config: PlannerClientConfig) -> None:
        self._config = config

    async def complete(
            self, prompt: str, *, metadata: dict[str, Any] | None = None
            ) -> str:
                """Execute a single‑shot completion request via the LLM Hub.

                Calls the Hub ``/v1/infer/sync`` endpoint, passing the prompt and
                configuration values from ``PlannerClientConfig``.

                Args:
                    prompt: The full prompt string that should be sent to the model.
                    metadata: Optional dictionary of tracing metadata – merged into the
                    request body under the ``metadata`` key.

                    Returns:
                        The ``completion`` field from the response – a plain string.
                        """

# Build the request payload expected by the LLM Hub.
                        request_body: dict[str, Any] = {
                        "prompt": prompt,
                        "max_tokens": self._config.max_output_tokens,
                        "temperature": self._config.temperature,
                        }
                        if metadata:
                            request_body["metadata"] = metadata

# Resolve LLM Hub base URL from environment (LLM_HUB_URL) or default service DNS.
                            import os

                            hub_base = resolve_env("LLM_HUB_URL", "http://llm-hub:10022").rstrip("/")
                            hub_url = f"{hub_base}/v1/infer/sync"

                            async with httpx.AsyncClient(
                            timeout=self._config.request_timeout_seconds
                            ) as client:
                                response = await client.post(hub_url, json=request_body)
                                response.raise_for_status()
                                payload = response.json()
# The Hub response includes a ``completion`` field.
                                return payload.get("completion", "")
