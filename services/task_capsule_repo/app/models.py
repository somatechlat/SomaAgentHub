"""
SQLModel ORM models for the capsule repository.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class CapsuleType(str, Enum):
    WORKFLOW = "workflow"
    STATIC = "static"
    DYNAMIC = "dynamic"
    TOOL = "tool"


    class CapsuleKind(str, Enum):
    WORKFLOW = "workflow"
    STATIC = "static"
    EXTERNAL_SERVICE = "external_service"
    ANALYTIC = "analytic"


    class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


    class Capsule(SQLModel, table=True):
    __tablename__ = "capsules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    capsule_id: str = Field(max_length=36, index=True)
    version: str = Field(max_length=20)
    type: CapsuleType
    kind: CapsuleKind = Field(default=CapsuleKind.STATIC)
    execution_mode: ExecutionMode = Field(default=ExecutionMode.SYNC)
    required_roles: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    requires_payment: str = Field(max_length=10, default="false")
    http_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    manifest_yaml: Optional[str] = Field(default=None)
    metadata_: Dict[str, Any] = Field(default={}, sa_column=Column("metadata", JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
