"""Session payload models for gateway orchestration."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    prompt: str
    capsule_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModerationDetail(BaseModel):
    strike_count: int = 0
    flagged_terms: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    bypassed: bool = False


class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    moderation: ModerationDetail
    payload: Dict[str, Any] = Field(default_factory=dict)
