"""Async HTTP client for SomaBrain endpoints."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import httpx

from .models import RagRequest, RecallPayload, RememberPayload


class SomaBrainError(RuntimeError):
    """Raised when SomaBrain returns a non-success response."""


class SomaBrainClient:
    """Thin wrapper around SomaBrain's HTTP API."""

    def __init__(
        self,
        base_url: str,
        *,
        tenant_header: str = "X-Tenant-ID",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._tenant_header = tenant_header
        self._timeout = timeout_seconds

    async def _post(
        self,
        path: str,
        tenant_id: str,
        payload: Mapping[str, Any],
    ) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}{path}",
                headers={self._tenant_header: tenant_id},
                json=payload,
            )
        if response.status_code >= 400:
            raise SomaBrainError(
                f"SomaBrain POST {path} failed: {response.status_code} {response.text}"
            )
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    async def remember(self, tenant_id: str, payload: RememberPayload | Mapping[str, Any]) -> Any:
        """Store text/facts via `/remember`."""

        data = payload.model_dump(mode="json") if isinstance(payload, RememberPayload) else dict(payload)
        return await self._post("/remember", tenant_id, data)

    async def recall(self, tenant_id: str, payload: RecallPayload | Mapping[str, Any]) -> Any:
        """Retrieve memories via `/recall`."""

        data = payload.model_dump(mode="json") if isinstance(payload, RecallPayload) else dict(payload)
        return await self._post("/recall", tenant_id, data)

    async def rag_retrieve(self, tenant_id: str, payload: RagRequest | Mapping[str, Any]) -> Any:
        """Invoke SomaBrain's RAG pipeline."""

        data = payload.model_dump(mode="json") if isinstance(payload, RagRequest) else dict(payload)
        return await self._post("/rag/retrieve", tenant_id, data)

    async def link(self, tenant_id: str, payload: Mapping[str, Any]) -> Any:
        """Create typed relations via `/link`."""

        return await self._post("/link", tenant_id, payload)

    async def load_constitution(self, payload: Mapping[str, Any]) -> Any:
        """Upload constitution JSON (requires trusted access)."""

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/constitution/load", json=payload)
        if response.status_code >= 400:
            raise SomaBrainError(
                f"SomaBrain POST /constitution/load failed: {response.status_code} {response.text}"
            )
        return response.json()

    async def get_constitution_version(self) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/constitution/version")
        if response.status_code >= 400:
            raise SomaBrainError(
                f"SomaBrain GET /constitution/version failed: {response.status_code} {response.text}"
            )
        return response.json()

    async def checksum_constitution(self, payload: Mapping[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/constitution/checksum", json=payload)
        if response.status_code >= 400:
            raise SomaBrainError(
                f"SomaBrain POST /constitution/checksum failed: {response.status_code} {response.text}"
            )
        return response.json()

    async def validate_constitution(self, payload: Mapping[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/constitution/validate", json=payload)
        if response.status_code >= 400:
            raise SomaBrainError(
                f"SomaBrain POST /constitution/validate failed: {response.status_code} {response.text}"
            )
        return response.json()
