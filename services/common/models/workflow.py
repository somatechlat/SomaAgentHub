from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    SUBGRAPH = "subgraph"
    HUMAN_INTERRUPT = "human_interrupt"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WorkflowNode(BaseModel):
    id: str
    type: NodeType
    agent_id: str | None = Field(None, alias="agentId")
    tool_id: str | None = Field(None, alias="toolId")
    parameters: dict[str, Any] | None = None
    interrupt: bool = False
    risk: RiskLevel = RiskLevel.LOW


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class GraphWorkflow(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    version: int = 1
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    initial_state: dict[str, Any] | None = Field(None, alias="initialState")
    created_by: UUID | None = Field(None, alias="createdBy")
