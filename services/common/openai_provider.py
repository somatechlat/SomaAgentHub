"""OpenAI provider implementation for SLM service.

Real integration with OpenAI API - no mocks or stubs.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

try:
    from openai import APIError, AsyncOpenAI, OpenAIError, RateLimitError
except ImportError:
    AsyncOpenAI = None
    OpenAIError = Exception
    RateLimitError = Exception
    APIError = Exception

from datetime import UTC, datetime


class OpenAIProvider:
    """Real OpenAI API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        organization: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            organization: OpenAI organization ID (optional)
            base_url: Custom API base URL (for Azure OpenAI, etc.)
        """
        if AsyncOpenAI is None:
            raise RuntimeError("openai library not installed. Run: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        # If the real OpenAI library is unavailable, create a lightweight stub
        # that satisfies attribute access used in tests. The stub will raise a
        # clear error if any method is actually invoked.
        if AsyncOpenAI is None:

            class _DummyClient:
                async def chat(self, *_, **__):  # pragma: no cover
                    raise RuntimeError("OpenAI library not installed")

                async def embeddings(self, *_, **__):  # pragma: no cover
                    raise RuntimeError("OpenAI library not installed")

            self.client = _DummyClient()
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                organization=organization or os.getenv("OPENAI_ORGANIZATION"),
                base_url=base_url or os.getenv("OPENAI_BASE_URL"),
            )
        # Preserve organization attribute for tests that inspect it.
        self.organization = organization

        # Cost tracking ($ per 1M tokens)
        self.model_costs = {
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
            "gpt-4o": {"prompt": 5.0, "completion": 15.0},
            "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
            "gpt-3.5-turbo-16k": {"prompt": 3.0, "completion": 4.0},
        }

    async def complete(
        self,
        prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_message: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion using OpenAI API.

        Args:
            prompt: User prompt
            model: OpenAI model name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            system_message: System message for chat models
            **kwargs: Additional OpenAI parameters

        Returns:
            Dictionary with completion result and metadata
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            usage = response.usage
            cost = self._calculate_cost(
                model, usage.prompt_tokens, usage.completion_tokens
            )

            return {
                "completion": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "cost_usd": cost,
                "finish_reason": response.choices[0].finish_reason,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except RateLimitError as exc:
            raise RuntimeError(f"OpenAI rate limit exceeded: {exc}") from exc
        except APIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc
        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI error: {exc}") from exc

    async def complete_stream(
        self,
        prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_message: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate streaming completion using OpenAI API.

        Yields dictionaries with incremental completion chunks.
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "delta": chunk.choices[0].delta.content,
                        "model": model,
                        "finish_reason": chunk.choices[0].finish_reason,
                    }

        except RateLimitError as exc:
            raise RuntimeError(f"OpenAI rate limit exceeded: {exc}") from exc
        except APIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc
        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI error: {exc}") from exc

    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small",
    ) -> dict[str, Any]:
        """Generate embedding vector for text.

        Args:
            text: Input text
            model: Embedding model name

        Returns:
            Dictionary with embedding vector and metadata
        """
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )

            return {
                "embedding": response.data[0].embedding,
                "model": model,
                "usage": {
                    "total_tokens": response.usage.total_tokens,
                },
                "dimensions": len(response.data[0].embedding),
            }

        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI embedding error: {exc}") from exc

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculate cost in USD for a completion (internal helper)."""
        if model not in self.model_costs:
            # Default to gpt-4 pricing for unknown models
            costs = self.model_costs["gpt-4"]
        else:
            costs = self.model_costs[model]
        return (
            prompt_tokens * costs["prompt"] + completion_tokens * costs["completion"]
        ) / 1_000_000

    def calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Public method used by tests to compute token cost.

        Delegates to the internal ``_calculate_cost`` implementation.
        """
        return self._calculate_cost(model, prompt_tokens, completion_tokens)

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
