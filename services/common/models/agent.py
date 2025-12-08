from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    HTTP = "http"
    DOCKER = "docker"
    NATIVE = "native"


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolSpec(BaseModel):
    id: str
    type: ToolType
    endpoint: str
    timeout_sec: int = Field(default=30, alias="timeoutSec")
    security_level: SecurityLevel = Field(
        default=SecurityLevel.LOW, alias="securityLevel"
    )
    description: str | None = None
    parameters: dict[str, Any] | None = None


class AgentConstraints(BaseModel):
    max_depth: int | None = Field(None, alias="maxDepth")
    allowed_tool_categories: list[str] = Field(
        default_factory=list, alias="allowedToolCategories"
    )


class AgentSpec(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    role: str | None = None
    instructions: str
    tools: list[ToolSpec] = Field(default_factory=list)
    memory_bindings: list[str] = Field(default_factory=list, alias="memoryBindings")
    constraints: AgentConstraints | None = None
    policy_scope: str | None = Field(None, alias="policyScope")


class RoutingMode(str, Enum):
    SUPERVISOR = "supervisor"
    CLASSIFIER = "classifier"
    STATIC = "static"


class CrewSpec(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    goal: str | None = None
    agents: list[UUID]
    supervisor: UUID | None = None
    routing_mode: RoutingMode = Field(
        default=RoutingMode.SUPERVISOR, alias="routingMode"
    )
