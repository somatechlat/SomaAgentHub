"""
SQLAlchemy ORM models for the capsule repository.

We replaced the previous SQLModel definitions with plain SQLAlchemy
declarative models so the codebase can migrate to Pydantic v2 while
retaining an async SQLAlchemy runtime. The table and column names are
unchanged from the old schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import Column, Enum as SAEnum, Text, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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


class Capsule(Base):
    __tablename__ = "capsules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capsule_id = Column(String(36), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    type = Column(SAEnum(CapsuleType), nullable=False)
    kind = Column(SAEnum(CapsuleKind), nullable=False, default=CapsuleKind.STATIC)
    execution_mode = Column(SAEnum(ExecutionMode), nullable=False, default=ExecutionMode.SYNC)
    required_roles = Column(JSONB, default=list)
    requires_payment = Column(String(10), nullable=False, default="false")
    http_config = Column(JSONB, default=dict)
    manifest_yaml = Column(Text)
    # Use instance attribute name `metadata_json` to avoid SQLAlchemy reserved name
    metadata_json = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
