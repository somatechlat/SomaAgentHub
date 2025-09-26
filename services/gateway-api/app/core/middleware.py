"""Custom middleware for request context propagation."""

from __future__ import annotations

from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware

from .auth import decode_token
from .config import get_settings
from .context import build_request_context, reset_request_context, set_request_context

ALLOWED_ANON_PATHS = {"/health", "/docs", "/openapi.json"}


class ContextMiddleware(BaseHTTPMiddleware):
    """Populate per-request context from JWT claims."""

    def __init__(self, app) -> None:  # type: ignore[override]
        super().__init__(app)
        settings = get_settings()
        self._defaults = {
            "client_type_header": settings.client_type_header,
            "deployment_mode_header": settings.deployment_mode_header,
            "default_tenant_id": settings.default_tenant_id,
            "default_client_type": settings.default_client_type,
            "default_deployment_mode": settings.default_deployment_mode,
        }
        self._allowed_tenants = set(settings.allowed_tenants())

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if any(path.startswith(p) for p in ALLOWED_ANON_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Missing bearer token"})

        token = auth_header.split(" ", 1)[1]
        claims = decode_token(token)

        try:
            ctx = build_request_context(request, self._defaults, claims)
        except ValueError as exc:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

        if self._allowed_tenants and ctx.tenant_id not in self._allowed_tenants:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Tenant not authorised for this region",
                    "tenant": ctx.tenant_id,
                },
            )

        token_var = set_request_context(ctx)
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token_var)
        response.headers.setdefault("X-Request-ID", ctx.request_id or "")
        return response
