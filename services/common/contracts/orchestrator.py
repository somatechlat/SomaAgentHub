from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class AgentDirective(BaseModel):
    agent_id: str
    goal: str
    prompt: str
    capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartRequest(BaseModel):
    tenant: str
    initiator: str
    directives: list[AgentDirective]
    notification_channel: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    orchestration_id: str
    task_queue: str


class SessionStartRequest(BaseModel):
    tenant: str
    user: str
    prompt: str
    model: str = "somagent-demo"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionStartResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    session_id: str
    task_queue: str


class OrchestrationStartedEvent(BaseModel):
    """Event emitted when a multi-agent orchestration is started."""
    mao_id: str
    project_id: str
    workflow_type: str
    agent_ids: list[str]
    input_data: dict[str, Any]
    timestamp: str
