"""JWT authentication middleware for Django API v2."""

from __future__ import annotations

import logging

import jwt
from django.http import HttpRequest, JsonResponse

from admin.common.messages import get_message

from .auth import JWKSVerifier, fetch_jwks_url
from .context import RequestContext

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Optional JWT verification for /api/v2; enriches RequestContext when present."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._verifier: JWKSVerifier | None = None

    async def __call__(self, request: HttpRequest):
        if request.path.startswith("/api/v2/"):
            await self._ensure_verifier()
            ctx = RequestContext.from_request(request)
            token = _extract_token(request)
            if token and self._verifier:
                try:
                    claims = await self._verifier.verify(token)
                    ctx.user_id = claims.get("sub") or claims.get("user_id")
                    ctx.tenant_id = claims.get("tenant_id") or ctx.tenant_id
                    ctx.capabilities = list(claims.get("capabilities", []) or [])
                    ctx.roles = list(claims.get("roles", []) or [])
                    request.sah_claims = claims  # type: ignore[attr-defined]
                except jwt.ExpiredSignatureError:
                    return JsonResponse(
                        {
                            "detail": get_message("gateway.auth.expired"),
                            "reason": "token_expired",
                        },
                        status=401,
                    )
                except jwt.InvalidTokenError as exc:
                    logger.warning("Invalid token: %s", exc)
                    return JsonResponse(
                        {
                            "detail": get_message("gateway.auth.invalid"),
                            "reason": "token_invalid",
                        },
                        status=401,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Auth verification failed: %s", exc)
                    return JsonResponse(
                        {
                            "detail": get_message("gateway.auth.unreachable"),
                            "reason": "auth_unreachable",
                        },
                        status=503,
                    )
            request.sah_ctx = ctx  # type: ignore[attr-defined]
        return await self._get_response_async(request)

    async def _ensure_verifier(self) -> None:
        if self._verifier is None:
            jwks_url = await fetch_jwks_url()
            self._verifier = JWKSVerifier(jwks_url)

    async def _get_response_async(self, request: HttpRequest):
        response = self.get_response
        if callable(getattr(response, "__call__", None)):
            maybe = response(request)
            if hasattr(maybe, "__await__"):
                return await maybe
            return maybe
        return response  # type: ignore[return-value]


def _extract_token(request: HttpRequest) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return None
