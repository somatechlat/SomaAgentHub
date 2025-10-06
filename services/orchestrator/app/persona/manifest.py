"""Persona manifest schema and helpers for SomaBrain experience capsules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError, validator


SCHEMA_VERSION = "0.2.0"


class ManifestValidationError(ValueError):
    """Raised when a persona manifest fails validation."""


class PersonaOwner(BaseModel):
    """Represents a human or organization responsible for the persona."""

    name: str
    contact: Optional[str] = Field(
        default=None, description="Email or URL for the persona maintainer"
    )
    organization: Optional[str] = Field(default=None, description="Owning organization")


class ModelCapability(BaseModel):
    """Capability toggle exposed by a model box."""

    feature: str
    enabled: bool = True
    notes: Optional[str] = None


class ModelBoxReference(BaseModel):
    """Reference to the model box powering the persona."""

    model_box_id: str = Field(..., description="Unique identifier in the SLM catalog")
    version: str = Field(..., description="Semantic version of the model box")
    provider: str = Field(..., description="Provider or serving stack (e.g., openai, groq, vllm)")
    default_mode: str = Field(
        "production",
        description="Preferred deployment mode for this persona (production, staging, etc.)",
    )
    capabilities: List[ModelCapability] = Field(
        default_factory=list,
        description="Feature flags exposed by the model box",
    )
    temperature: float = Field(
        0.2,
        ge=0.0,
        le=2.0,
        description="Default creative setting expected by downstream planners",
    )

    class Config:
        extra = "forbid"


class MemorySnapshotReference(BaseModel):
    """Pointer to the persisted SomaBrain memory bundle."""

    snapshot_id: str
    storage_uri: str = Field(
        ..., description="URI to the memory snapshot artifact (s3://, gs://, file://)"
    )
    embedding_model: str = Field(
        ..., description="Embedding model used when producing the snapshot"
    )
    item_count: int = Field(..., ge=0, description="Total number of memory items")
    checksum: str = Field(
        ..., description="SHA256 checksum for integrity validation"
    )


class ToolAccessDescriptor(BaseModel):
    """Represents a tool capability required by the persona."""

    tool: str = Field(..., description="Tool adapter name (e.g., github, notion)")
    required: bool = Field(
        True, description="Whether the persona needs this tool to operate correctly"
    )
    access_scope: str = Field(
        "read",
        description="Scope expected (read, write, admin, custom policy identifier)",
    )
    notes: Optional[str] = None


class EvaluationScore(BaseModel):
    """Captures evaluation signal for the persona."""

    benchmark: str
    score: float = Field(..., description="Normalized score between 0 and 1")
    dataset: Optional[str] = None
    captured_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the evaluation was recorded",
    )
    reference_link: Optional[HttpUrl] = None
    notes: Optional[str] = None

    @validator("score")
    def _check_score(cls, value: float) -> float:  # noqa: D401
        """Ensure score is clamped between 0 and 1."""

        if not 0.0 <= value <= 1.0:
            raise ValueError("Evaluation scores must be between 0 and 1 inclusive")
        return value


class GovernanceMetadata(BaseModel):
    """Governance and policy context for the persona export."""

    constitution_sha: str = Field(
        ..., description="SHA3-512 hash of the constitution governing the persona"
    )
    training_snapshot_id: str = Field(
        ..., description="Identifier of the training mode session used for export"
    )
    approvals: List[str] = Field(
        default_factory=list,
        description="List of user IDs or capability grants that approved publication",
    )
    kill_switch_enabled: bool = Field(
        True,
        description="Whether the persona honors the kill switch channel from SomaAgentHub",
    )


class PricingModel(BaseModel):
    """Describes how the persona can be monetized in the marketplace."""

    model: str = Field(
        "rental",
        description="Pricing archetype (purchase, subscription, rental)",
    )
    amount_usd: float = Field(
        0.0,
        ge=0.0,
        description="Reference price in USD for the selected pricing model",
    )
    billing_period_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Applies to rental/subscription models: duration in minutes",
    )
    notes: Optional[str] = None


class PersonaMetadata(BaseModel):
    """Top-level persona metadata shared with the marketplace."""

    persona_id: str = Field(..., description="Stable identifier for the persona")
    version: str = Field(..., description="Semantic version of this persona snapshot")
    display_name: str = Field(..., description="Human-readable name")
    summary: str = Field(..., description="Short marketing/description blurb")
    domains: List[str] = Field(
        default_factory=list,
        description="Domain tags (e.g., project-management, finance, chemistry)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owners: List[PersonaOwner] = Field(
        default_factory=list, description="Maintainers responsible for the persona"
    )


class ArtifactBundle(BaseModel):
    """Supporting artifacts emitted during export."""

    prompts_uri: Optional[str] = Field(
        default=None,
        description="Location of prompt templates bundled with the persona",
    )
    evaluation_report_uri: Optional[str] = Field(
        default=None,
        description="Location of evaluation results (JSON, PDF, etc.)",
    )
    release_notes_uri: Optional[str] = Field(
        default=None,
        description="Location of release notes or changelog for this persona version",
    )


class ManifestSignature(BaseModel):
    """Cryptographic signature binding the manifest to the constitution service."""

    algorithm: str = Field(..., description="Signing algorithm identifier (e.g., ed25519)")
    signature: str = Field(..., description="Base64-encoded detached signature")
    public_key: str = Field(..., description="Base64-encoded public key used for verification")
    digest: str = Field(..., description="SHA3-256 digest of the canonical manifest payload")
    signed_at: datetime = Field(..., description="Timestamp when the manifest was signed")


class PersonaManifest(BaseModel):
    """Canonical manifest describing a SomaBrain persona capsule."""

    schema_version: str = Field(SCHEMA_VERSION, description="Manifest schema version")
    metadata: PersonaMetadata
    model_box: ModelBoxReference
    memory: MemorySnapshotReference
    tools: List[ToolAccessDescriptor] = Field(
        default_factory=list,
        description="Tool adapters and scopes required by the persona",
    )
    evaluations: List[EvaluationScore] = Field(
        default_factory=list, description="Evaluation signals backing the persona"
    )
    governance: GovernanceMetadata
    pricing: PricingModel = Field(
        default_factory=PricingModel,
        description="Marketplace pricing metadata",
    )
    artifacts: ArtifactBundle = Field(
        default_factory=ArtifactBundle,
        description="Supporting artifacts published alongside the persona",
    )
    signature: Optional[ManifestSignature] = Field(
        default=None,
        description="Cryptographic signature issued by the constitution service",
    )

    class Config:
        extra = "forbid"


@dataclass(slots=True)
class ManifestIO:
    """Structured response from manifest utility helpers."""

    manifest: PersonaManifest
    raw: Dict[str, Any]
    source_path: Optional[Path] = None


def _load_data_from_source(source: Union[str, Path, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    """Normalise different manifest sources into a dictionary."""

    if isinstance(source, dict):
        return source
    if isinstance(source, bytes):
        return _load_data_from_bytes(source)
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise ManifestValidationError(f"Manifest path does not exist: {path}")
        data = path.read_bytes()
        payload = _load_data_from_bytes(data)
        payload.setdefault("_source_path", str(path))
        return payload
    raise ManifestValidationError("Unsupported manifest source type")


def _load_data_from_bytes(data: bytes) -> Dict[str, Any]:
    """Decode YAML or JSON payload into a dictionary."""

    try:
        return yaml.safe_load(data) or {}
    except yaml.YAMLError:
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ManifestValidationError("Manifest payload is not valid YAML or JSON") from exc


def validate_persona_manifest(
    payload: Union[str, Path, bytes, Dict[str, Any]]
) -> PersonaManifest:
    """Validate a manifest payload and return the parsed PersonaManifest."""

    data = _load_data_from_source(payload)
    try:
        manifest = PersonaManifest.model_validate(data)
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc
    return manifest


def load_persona_manifest(source: Union[str, Path, bytes]) -> ManifestIO:
    """Load a persona manifest from disk or bytes, returning the model + raw payload."""

    data = _load_data_from_source(source)
    source_path: Optional[Path] = None
    if "_source_path" in data:
        source_path = Path(data.pop("_source_path"))
    manifest = validate_persona_manifest(data)
    return ManifestIO(manifest=manifest, raw=data, source_path=source_path)


def dump_persona_manifest(manifest: PersonaManifest, destination: Union[str, Path]) -> Path:
    """Serialise a persona manifest to YAML at the given destination path."""

    path = Path(destination)
    payload = manifest.model_dump(mode="json", exclude_none=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path