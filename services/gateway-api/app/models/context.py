"""Request context model used across the Gateway service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RequestContext:
    """Lightweight request-scoped context container.

    Fields mirror what the gateway code expects to read/write.
    """

    tenant_id: str
    user_id: Optional[str]
    capabilities: List[str]
    client_type: str
    deployment_mode: str
    request_id: str
