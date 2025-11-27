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
from typing import Any, Dict, List, Optional

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
    type: Optional[CapsuleType] = Field(default=None, description="Logical capsule type")
    kind: Optional[CapsuleKind] = Field(default=None, description="Execution kind")
    execution_mode: Optional[ExecutionMode] = Field(default=None, description="Sync/async mode")

    # Optional JSON blobs
    required_roles: List[str] = Field(default_factory=list)
    requires_payment: str = Field(default="false")
    http_config: Dict[str, Any] = Field(default_factory=dict)
    manifest_yaml: Optional[str] = Field(default=None)
    metadata_json: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
"""Capsule model persisted in the orchestrator PostgreSQL database.

Sprint 1 introduces a PostgreSQL‑backed capsule registry.  The model mirrors the
schema used by the ``task‑capsule‑repo`` service but is defined with ``SQLModel``
so it participates in the existing ``init_db`` routine (which calls
``SQLModel.metadata.create_all``).  Only the fields required by the current
API are stored – additional columns can be added later without breaking
compatibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Field, SQLModel


class Capsule(SQLModel, table=True):
    """Persisted capsule metadata.

    * ``id`` – internal UUID primary key.
    * ``capsule_id`` – human‑readable identifier (e.g. ``org/name``).
    * ``version`` – semantic version or tag.
    * ``type`` – logical capsule type (workflow, static, etc.).
    * ``kind`` – execution kind (sync, async, etc.).
    * ``manifest`` – full capsule manifest stored as JSON.
    * ``metadata_json`` – optional extra metadata.
    * ``tenant`` – owning tenant identifier.
    * ``created_at`` / ``updated_at`` – timestamps.
    """

    __tablename__ = "capsules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    capsule_id: str = Field(index=True, description="Human readable capsule identifier")
    version: str = Field(default="latest", description="Capsule version tag")
    type: Optional[str] = Field(default=None, description="Capsule type")
    kind: Optional[str] = Field(default=None, description="Capsule kind")
    manifest: Optional[Dict[str, Any]] = Field(default=None, description="Full capsule manifest as JSON")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    tenant: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
