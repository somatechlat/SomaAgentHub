"""Context storage utilities for per-request metadata."""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

from fastapi import Request

from ..models.context import RequestContext

_request_context_var: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context"
)


def build_request_context(request: Request, defaults: dict[str, str]) -> RequestContext:
    headers = request.headers
    tenant_id = headers.get(defaults["tenant_header"], defaults["default_tenant_id"])
    if not tenant_id:
        raise ValueError("tenant id is required")
    user_id = headers.get(defaults["user_header"])
    capabilities_raw = headers.get(defaults["capabilities_header"], "")
    capabilities = [c.strip() for c in capabilities_raw.split(",") if c.strip()]
    client_type = headers.get(defaults["client_type_header"], defaults["default_client_type"])
    deployment_mode = headers.get(
        defaults["deployment_mode_header"], defaults["default_deployment_mode"]
    )
    request_id = headers.get("X-Request-ID", str(uuid.uuid4()))
    return RequestContext(
        tenant_id=tenant_id,
        user_id=user_id,
        capabilities=capabilities,
        client_type=client_type,
        deployment_mode=deployment_mode,
        request_id=request_id,
    )


def set_request_context(ctx: RequestContext) -> contextvars.Token[RequestContext]:
    return _request_context_var.set(ctx)


def reset_request_context(token: contextvars.Token[RequestContext]) -> None:
    _request_context_var.reset(token)


def get_request_context() -> Optional[RequestContext]:
    return _request_context_var.get(None)  # type: ignore[arg-type]
