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


class Capsule(Base):
    __tablename__ = "capsules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capsule_id = Column(String(36), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    type = Column(SAEnum(CapsuleType), nullable=False)
    manifest_yaml = Column(Text)
    # Use instance attribute name `metadata` so existing callers continue to
    # access `.metadata`. Column name in Postgres is also `metadata` (JSONB).
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
