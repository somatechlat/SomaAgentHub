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


class WizardApprovedEvent(BaseModel):
"""Event emitted when a wizard flow is approved by a user.

The test suite expects the following fields:
- ``wizard_id``: unique identifier for the wizard instance
- ``project_id``: identifier of the associated project
- ``user_id``: identifier of the approving user
- ``wizard_type``: type/name of the wizard (e.g. ``marketing_campaign``)
- ``configuration``: arbitrary configuration dict supplied to the wizard
- ``timestamp``: ISO‑8601 timestamp string when the approval occurred
"""

wizard_id: str
project_id: str
user_id: str
wizard_type: str
configuration: dict[str, Any]
timestamp: str
