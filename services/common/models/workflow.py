from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
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
    agent_id: Optional[str] = Field(None, alias="agentId")
    tool_id: Optional[str] = Field(None, alias="toolId")
    parameters: Optional[Dict[str, Any]] = None
    interrupt: bool = False
    risk: RiskLevel = RiskLevel.LOW

class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class GraphWorkflow(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    version: int = 1
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    initial_state: Optional[Dict[str, Any]] = Field(None, alias="initialState")
    created_by: Optional[UUID] = Field(None, alias="createdBy")
