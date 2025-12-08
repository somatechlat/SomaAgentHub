"""SQLModel definition for the capsule registry used by the Orchestrator.

Sprint 1 introduces a PostgreSQL‑backed capsule table.  The model mirrors the
structure of the existing ``task‑capsule‑repo`` service but is defined with
``SQLModel`` so it integrates with the Orchestrator's ``init_db`` routine.
Only fields required by the current test suite are included – additional
columns can be added later without breaking compatibility.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class CapsuleType(str, enum.Enum):
    WORKFLOW = "workflow"
    STATIC = "static"
    DYNAMIC = "dynamic"
    TOOL = "tool"


class CapsuleKind(str, enum.Enum):
    WORKFLOW = "workflow"
    STATIC = "static"
    EXTERNAL_SERVICE = "external_service"
    ANALYTIC = "analytic"


class ExecutionMode(str, enum.Enum):
    SYNC = "sync"
    ASYNC = "async"


class Capsule(SQLModel, table=True):
    """Persisted capsule metadata.

    The fields are deliberately simple and JSON‑serialisable so they can be
    stored in PostgreSQL ``jsonb`` columns.
    """

    __tablename__ = "capsules"

    # Primary key
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Business identifiers
    capsule_id: str = Field(index=True, description="Human readable capsule identifier")
    version: str = Field(default="latest", description="Capsule version/tag")

    # Classification fields
    type: CapsuleType | None = Field(default=None, description="Logical capsule type")
    kind: CapsuleKind | None = Field(default=None, description="Execution kind")
    execution_mode: ExecutionMode | None = Field(
        default=None, description="Sync/async mode"
    )

    # Optional JSON blobs
    required_roles: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    requires_payment: str = Field(default="false")
    http_config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    manifest_yaml: str | None = Field(default=None)
    metadata_json: dict[str, Any] = Field(
        default_factory=dict, alias="metadata", sa_column=Column(JSON)
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
