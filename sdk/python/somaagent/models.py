"""
Data models for SomaAgent SDK.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


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
    """Task capsule."""
    
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
