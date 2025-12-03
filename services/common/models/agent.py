from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
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
    security_level: SecurityLevel = Field(default=SecurityLevel.LOW, alias="securityLevel")
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class AgentConstraints(BaseModel):
    max_depth: Optional[int] = Field(None, alias="maxDepth")
    allowed_tool_categories: List[str] = Field(default_factory=list, alias="allowedToolCategories")

class AgentSpec(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    role: Optional[str] = None
    instructions: str
    tools: List[ToolSpec] = Field(default_factory=list)
    memory_bindings: List[str] = Field(default_factory=list, alias="memoryBindings")
    constraints: Optional[AgentConstraints] = None
    policy_scope: Optional[str] = Field(None, alias="policyScope")

class RoutingMode(str, Enum):
    SUPERVISOR = "supervisor"
    CLASSIFIER = "classifier"
    STATIC = "static"

class CrewSpec(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    goal: Optional[str] = None
    agents: List[UUID]
    supervisor: Optional[UUID] = None
    routing_mode: RoutingMode = Field(default=RoutingMode.SUPERVISOR, alias="routingMode")
