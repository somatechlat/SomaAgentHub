"""
SQLModel definitions for the capsule repository.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Enum as SAEnum, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

class CapsuleType(str, Enum):
    WORKFLOW = "workflow"
    STATIC = "static"
    DYNAMIC = "dynamic"
    TOOL = "tool"

class Capsule(SQLModel, table=True):
    __tablename__ = "capsules"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    capsule_id: str = Field(index=True, nullable=False, max_length=36)
    version: str = Field(nullable=False, max_length=20)
    type: CapsuleType = Field(sa_column=Column(SAEnum(CapsuleType), nullable=False))
    manifest_yaml: str = Field(sa_column=Column(Text), nullable=False)
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()))
