"""Request context models for the gateway."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RequestContext(BaseModel):
    tenant_id: str
    user_id: Optional[str] = None
    capabilities: List[str] = []
    client_type: str = "web"
    deployment_mode: str = "developer-light"
    request_id: Optional[str] = None
