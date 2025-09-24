"""Provider registry and stub implementations for SLM service."""

from __future__ import annotations

import asyncio
import math
from typing import Any, Dict, Protocol


class SyncProvider(Protocol):
    async def infer_sync(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def embedding(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class StubProvider:
    """No-op provider useful for local development."""

    async def infer_sync(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt") or payload.get("input") or ""
        await asyncio.sleep(0.05)  # simulate small latency
        return {
            "model": payload.get("model", "stub"),
            "output": f"[stub-response] {prompt}",
            "tokens_used": len(prompt.split()),
        }

    async def embedding(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text") or payload.get("input") or ""
        await asyncio.sleep(0.02)
        vector = [math.sin(i + len(text)) for i in range(8)]
        return {
            "model": payload.get("model", "stub-embedding"),
            "embedding": vector,
            "dim": len(vector),
        }


PROVIDERS: Dict[str, SyncProvider] = {
    "stub": StubProvider(),
}


def get_provider(name: str) -> SyncProvider:
    try:
        return PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown SLM provider '{name}'") from exc
