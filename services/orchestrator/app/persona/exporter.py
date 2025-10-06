"""Persona export pipeline scaffolding for the SomaBrain Experience Marketplace."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .manifest import (
    ArtifactBundle,
    GovernanceMetadata,
    MemorySnapshotReference,
    ModelBoxReference,
    PersonaManifest,
    PersonaMetadata,
    PricingModel,
    ToolAccessDescriptor,
    dump_persona_manifest,
)
from .signing import (
    ManifestSigningClient,
    ManifestSigningFailure,
    build_signing_client,
)


logger = logging.getLogger(__name__)


class PersonaExportRequest(BaseModel):
    """Input payload describing what should be exported."""

    tenant: str
    initiated_by: str = Field(..., description="User or system triggering the export")
    destination_path: Path = Field(
        ..., description="Local filesystem path for the manifest artifact"
    )
    metadata: PersonaMetadata
    model_box: ModelBoxReference
    memory: MemorySnapshotReference
    tools: List[ToolAccessDescriptor] = Field(default_factory=list)
    evaluations: List[Any] = Field(
        default_factory=list,
        description="Evaluation records, validated upstream before export",
    )
    governance: GovernanceMetadata
    pricing: PricingModel = Field(default_factory=PricingModel)
    artifacts: ArtifactBundle = Field(default_factory=ArtifactBundle)
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Loose metadata to persist alongside the manifest",
    )


class PersonaExportResult(BaseModel):
    """Outcome of an export operation."""

    tenant: str
    manifest: PersonaManifest
    manifest_path: Path
    created_at: datetime
    completed_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class PersonaExporterDependencies:
    """Thin dependency container allowing future injection of services."""

    storage_client: Optional[Any] = None
    memory_gateway: Optional[Any] = None
    tool_registry: Optional[Any] = None
    event_emitter: Optional[Any] = None
    signing_client: Optional[ManifestSigningClient] = None


class PersonaExporter:
    """Coordinates persona capsule exports and manifest generation."""

    def __init__(self, dependencies: Optional[PersonaExporterDependencies] = None) -> None:
        self._deps = dependencies or PersonaExporterDependencies()
        if self._deps.signing_client is None:
            self._deps.signing_client = build_signing_client()

    async def export_persona(self, request: PersonaExportRequest) -> PersonaExportResult:
        """Primary entrypoint to export a persona manifest and supporting artifacts."""

        started_at = datetime.utcnow()
        manifest = self._build_manifest(request)
        manifest = await self._maybe_sign_manifest(manifest)
        manifest_path = self._persist_manifest(manifest, request.destination_path)

        await self._dispatch_async_tasks(request, manifest_path)

        completed_at = datetime.utcnow()
        result = PersonaExportResult(
            tenant=request.tenant,
            manifest=manifest,
            manifest_path=manifest_path,
            created_at=started_at,
            completed_at=completed_at,
            metadata=request.additional_metadata,
        )

        await self._emit_event(result)
        return result

    def _build_manifest(self, request: PersonaExportRequest) -> PersonaManifest:
        """Construct a PersonaManifest from the export request."""

        manifest = PersonaManifest(
            metadata=request.metadata,
            model_box=request.model_box,
            memory=request.memory,
            tools=request.tools,
            evaluations=list(request.evaluations),
            governance=request.governance,
            pricing=request.pricing,
            artifacts=request.artifacts,
        )
        return manifest

    def _persist_manifest(self, manifest: PersonaManifest, destination: Path) -> Path:
        """Persist the manifest to the requested destination."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        return dump_persona_manifest(manifest, destination)

    async def _maybe_sign_manifest(self, manifest: PersonaManifest) -> PersonaManifest:
        """Attach a cryptographic signature when a signing client is configured."""

        client = self._deps.signing_client
        if client is None:
            return manifest

        try:
            signature = await client.sign_manifest(manifest)
        except ManifestSigningFailure as exc:
            logger.error("Persona manifest signing failed: %s", exc)
            raise
        manifest.signature = signature
        return manifest

    async def _dispatch_async_tasks(
        self, request: PersonaExportRequest, manifest_path: Path
    ) -> None:
        """Hook for future async tasks (artifact uploads, memory exports, etc.)."""

        tasks: List[asyncio.Task[Any]] = []
        # Placeholder: attach background uploads once dependencies exist.
        if tasks:
            await asyncio.gather(*tasks)

    async def _emit_event(self, result: PersonaExportResult) -> None:
        """Emit an audit/marketplace event capturing the export."""

        if self._deps.event_emitter is None:
            return
        payload = {
            "tenant": result.tenant,
            "persona_id": result.manifest.metadata.persona_id,
            "version": result.manifest.metadata.version,
            "manifest_path": str(result.manifest_path),
            "created_at": result.created_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
        }
        await self._deps.event_emitter.emit("persona.export.completed", payload)


async def export_persona(request: PersonaExportRequest) -> PersonaExportResult:
    """Convenience coroutine using default dependencies."""

    exporter = PersonaExporter()
    return await exporter.export_persona(request)
