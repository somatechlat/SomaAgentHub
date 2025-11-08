"""SQLModel definitions for persisting planner artefacts.

We use **SQLModel** (an async‑friendly wrapper around SQLAlchemy) because the
project already depends on PostgreSQL for other services.  The ``Plan`` model
mirrors the ``ProjectPlan`` Pydantic schema defined in ``planner/schemas.py`` but
stores the JSON payload as a ``JSON`` column for flexibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class Plan(SQLModel, table=True):
    """Database representation of a ``ProjectPlan``.

    The ``payload`` column stores the full JSON representation of the plan –
    this allows the service to evolve the schema without requiring a migration
    for every new field.  ``created_at`` and ``updated_at`` are managed by the
    application code.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant: str = Field(index=True)
    plan_id: str = Field(index=True)  # matches ``ProjectPlan.plan_id``
    status: str = Field(default="draft", index=True)
    # Store the full plan JSON. Use SQLAlchemy's JSON column type for proper
    # serialization. ``sa_column`` accepts a full ``Column`` instance.
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BuildRun(SQLModel, table=True):
    """Represents a single build workflow execution snapshot.

    Links pricing snapshot + budget evaluation + selected template set.
    Status flow: pending -> initializing -> provisioning -> building -> deploying -> completed / failed.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant: str = Field(index=True)
    project_id: str = Field(index=True)
    pricing_snapshot_id: str = Field(index=True)
    budget_cap: float = Field(default=0.0)
    estimated_cost: float = Field(default=0.0)
    status: str = Field(default="pending", index=True)
    template_set: str = Field(default="default")
    policy_reason: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
"""ORM/DTO models for storing project plan artifacts."""

# NOTE: ``from __future__ import annotations`` must appear only once at the top
# of the file. The duplicate import caused a ``SyntaxError`` during module
# import. It has been removed.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class PlanRecord:
    """Top-level plan metadata."""

    plan_id: str
    tenant: str
    capsule: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanModuleRecord:
    """State for a single plan module."""

    plan_id: str
    module_id: str
    status: str
    dependencies: List[str] = field(default_factory=list)
    answers: Dict[str, Any] = field(default_factory=dict)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanEvent:
    """Timeline event for auditing."""

    plan_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ToolBindingRecord:
    """Stores tool choices and related metadata."""

    plan_id: str
    capability: str
    tool_name: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvisioningTaskRecord:
    """Tracks provisioning capsules triggered by a plan."""

    plan_id: str
    task_id: str
    capsule_id: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
