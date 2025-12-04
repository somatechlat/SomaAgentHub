"""
Data models for SomaAgent SDK.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TenantRef:
    """Tenant reference."""
    id: str
    name: str
    tier: str
    status: str

@dataclass
class TaskRecord:
    """Task record."""
    id: str
    tenant_id: str
    workflow_instance_id: str
    name: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoleDefinition:
    """Role definition."""
    id: str
    tenant_id: str
    name: str
    description: str
    capabilities: List[str]
    constraints: Dict[str, Any]
    created_at: datetime

@dataclass
class AgentBinding:
    """Agent binding to a role."""
    id: str
    tenant_id: str
    role_id: str
    agent_id: str
    status: str
    created_at: datetime

@dataclass
class ToolDefinition:
    """Tool definition."""
    id: str
    tenant_id: str
    name: str
    description: str
    version: str
    parameters: Dict[str, Any]
    created_at: datetime

@dataclass
class MemoryBindingSpec:
    """Memory binding specification."""
    id: str
    tenant_id: str
    name: str
    type: str
    config: Dict[str, Any]
    created_at: datetime

@dataclass
class BlueprintDefinition:
    """Blueprint definition."""
    id: str
    tenant_id: str
    name: str
    version: str
    content: Dict[str, Any]
    created_at: datetime

@dataclass
class ReasoningPipelineSpec:
    """Reasoning pipeline specification."""
    id: str
    tenant_id: str
    name: str
    steps: List[Dict[str, Any]]
    created_at: datetime

@dataclass
class EvaluationScenarioDefinition:
    """Evaluation scenario definition."""
    id: str
    tenant_id: str
    name: str
    criteria: Dict[str, Any]
    created_at: datetime

@dataclass
class HumanReviewerAssignment:
    """Human reviewer assignment."""
    id: str
    tenant_id: str
    workflow_instance_id: str
    node_id: str
    reviewer_id: str
    status: str
    created_at: datetime

@dataclass
class Message:
    """Chat message."""
    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Chat conversation."""
    id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Capsule:
    """Marketplace capsule metadata."""
    id: str
    name: str
    description: str
    category: str
    version: str
    publisher: str
    price: float
    rating: float
    install_count: int
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Agent:
    """AI agent."""
    id: str
    name: str
    instructions: str
    model: str
    tools: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowRun:
    """Workflow execution run."""
    id: str
    workflow_type: str
    status: str  # running, completed, failed
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
