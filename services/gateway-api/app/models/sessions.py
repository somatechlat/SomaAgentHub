"""Session payload models for gateway orchestration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
prompt: str
capsule_id: str | None = None
metadata: dict[str, Any] = Field(default_factory=dict)


class ModerationDetail(BaseModel):
    strike_count: int = 0
    flagged_terms: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
class SessionCreateResponse(BaseModel):
session_id: str
status: str
moderation: ModerationDetail
payload: dict[str, Any] = Field(default_factory=dict)
