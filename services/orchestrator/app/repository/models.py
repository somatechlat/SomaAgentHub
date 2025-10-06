"""ORM/DTO models for storing project plan artifacts."""

from __future__ import annotations

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
