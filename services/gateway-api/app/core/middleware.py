"""Custom middleware for request context propagation."""

from __future__ import annotations

from typing import Callable

from fastapi import Request

from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .context import build_request_context, reset_request_context, set_request_context


class ContextMiddleware(BaseHTTPMiddleware):
    """Populate per-request context from headers."""

    def __init__(self, app) -> None:  # type: ignore[override]
        super().__init__(app)
        settings = get_settings()
        self._defaults = {
            "tenant_header": settings.tenant_header,
            "user_header": settings.user_header,
            "capabilities_header": settings.capabilities_header,
            "client_type_header": settings.client_type_header,
            "deployment_mode_header": settings.deployment_mode_header,
            "default_tenant_id": settings.default_tenant_id,
            "default_client_type": settings.default_client_type,
            "default_deployment_mode": settings.default_deployment_mode,
        }

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            ctx = build_request_context(request, self._defaults)
        except ValueError as exc:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=400,
                content={"detail": str(exc)},
            )

        token = set_request_context(ctx)
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token)
        response.headers.setdefault("X-Request-ID", ctx.request_id or "")
        return response
