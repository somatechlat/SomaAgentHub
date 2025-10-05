"""OpenAI provider implementation for SLM service.

Real integration with OpenAI API - no mocks or stubs.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator, Any, Dict, Optional

try:
    from openai import AsyncOpenAI
    from openai import OpenAIError, RateLimitError, APIError
except ImportError:
    AsyncOpenAI = None
    OpenAIError = Exception
    RateLimitError = Exception
    APIError = Exception

from datetime import datetime, timezone


class OpenAIProvider:
    """Real OpenAI API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
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
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=organization or os.getenv("OPENAI_ORGANIZATION"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        
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
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
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
                **kwargs
            )
            
            usage = response.usage
            cost = self._calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)
            
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
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
                **kwargs
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
    ) -> Dict[str, Any]:
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

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD for a completion."""
        if model not in self.model_costs:
            # Default to gpt-4 pricing for unknown models
            costs = self.model_costs["gpt-4"]
        else:
            costs = self.model_costs[model]
        
        prompt_cost = (prompt_tokens / 1_000_000) * costs["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * costs["completion"]
        
        return round(prompt_cost + completion_cost, 6)

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
