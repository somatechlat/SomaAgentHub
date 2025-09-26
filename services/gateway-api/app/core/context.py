"""Context storage utilities for per-request metadata."""

from __future__ import annotations

import contextvars
import uuid
from typing import Any, Dict

from fastapi import Request

from ..models.context import RequestContext

_request_context_var: contextvars.ContextVar[RequestContext] = contextvars.ContextVar(
    "request_context"
)


def build_request_context(
    request: Request,
    defaults: dict[str, str],
    claims: Dict[str, Any],
) -> RequestContext:
    tenant_id = claims.get("tenant_id") or defaults.get("default_tenant_id")
    if not tenant_id:
        raise ValueError("tenant id is required")
    user_id = claims.get("sub")
    capabilities_raw: Any = claims.get("capabilities") or []
    if isinstance(capabilities_raw, str):
        capabilities = [capabilities_raw]
    else:
        capabilities = list(capabilities_raw)
    client_type = request.headers.get(
        defaults["client_type_header"], defaults["default_client_type"]
    )
    deployment_mode = request.headers.get(
        defaults["deployment_mode_header"], defaults["default_deployment_mode"]
    )
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return RequestContext(
        tenant_id=tenant_id,
        user_id=str(user_id) if user_id else None,
        capabilities=capabilities,
        client_type=client_type,
        deployment_mode=deployment_mode,
        request_id=request_id,
    )


def set_request_context(ctx: RequestContext) -> contextvars.Token[RequestContext]:
    return _request_context_var.set(ctx)


def reset_request_context(token: contextvars.Token[RequestContext]) -> None:
    _request_context_var.reset(token)


def get_request_context() -> RequestContext | None:
    return _request_context_var.get(None)  # type: ignore[arg-type]
