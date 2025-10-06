"""Client helpers for constitution-service manifest signing."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..core.config import settings
from .manifest import ManifestSignature, PersonaManifest


class ManifestSigningFailure(RuntimeError):
    """Raised when the manifest signing request fails."""


@dataclass(slots=True)
class ManifestSigningConfig:
    """Runtime configuration for manifest signing."""

    endpoint: str
    timeout_seconds: float


class ManifestSigningClient:
    """Thin async client for constitution-service manifest signing."""

    def __init__(self, config: ManifestSigningConfig) -> None:
        self._config = config

    async def sign_manifest(self, manifest: PersonaManifest) -> ManifestSignature:
        payload = {"manifest": manifest.model_dump(mode="json", exclude_none=True)}
        try:
            async with httpx.AsyncClient(timeout=self._config.timeout_seconds) as client:
                response = await client.post(self._config.endpoint, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - httpx specifics
            raise ManifestSigningFailure(f"Manifest signing failed: {exc.response.text}") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network errors vary
            raise ManifestSigningFailure(f"Failed to contact manifest signing endpoint: {exc}") from exc

        data = response.json()
        return ManifestSignature.model_validate(data)


def build_signing_client() -> ManifestSigningClient | None:
    """Factory returning a signing client when enabled."""

    if not settings.manifest_signing_enabled:
        return None
    endpoint = settings.constitution_service_url.rstrip("/") + "/sign/persona-manifest"
    config = ManifestSigningConfig(
        endpoint=endpoint,
        timeout_seconds=settings.manifest_signing_timeout_seconds,
    )
    return ManifestSigningClient(config)
