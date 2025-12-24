"""OPA authorization middleware for Django API v2."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings
from django.http import HttpRequest, JsonResponse

from admin.common.messages import get_message

from .context import RequestContext

logger = logging.getLogger(__name__)


class OPAMiddleware:
    """Fail-closed OPA authorization middleware for /api/v2 routes."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.opa_url = getattr(settings, "OPA_URL", "http://opa:8181").rstrip("/")
        self.timeout = getattr(settings, "OPA_TIMEOUT", 5.0)

    async def __call__(self, request: HttpRequest):
        # Only guard the Django API surface
        if not request.path.startswith("/api/v2/"):
            return await self._get_response_async(request)

        ctx = getattr(request, "sah_ctx", None) or RequestContext.from_request(request)
        input_data = {
            "tenant_id": ctx.tenant_id,
            "user_id": ctx.user_id or "anonymous",
            "method": request.method,
            "path": request.path,
            "capabilities": ctx.capabilities,
            "deployment_mode": ctx.deployment_mode,
        }

        allowed = await self._evaluate_policy("somagent/authorization/allow", input_data)
        if allowed is True:
            return await self._get_response_async(request)

        if allowed is False:
            return JsonResponse(
                {
                    "detail": get_message("gateway.opa.denied"),
                    "reason": "opa_denied",
                },
                status=403,
            )

        # Fail closed on unreachable/unknown
        return JsonResponse(
            {
                "detail": get_message("gateway.opa.unreachable"),
                "reason": "opa_unreachable",
            },
            status=503,
        )

    async def _get_response_async(self, request: HttpRequest):
        response = self.get_response
        if callable(getattr(response, "__call__", None)):
            maybe = response(request)
            if hasattr(maybe, "__await__"):
                return await maybe
            return maybe
        return response  # type: ignore[return-value]

    async def _evaluate_policy(self, policy: str, input_data: dict[str, Any]) -> bool | None:
        """Call OPA; return True/False, or None on error."""
        url = f"{self.opa_url}/v1/data/{policy}"
        payload = {"input": input_data}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()
                result = data.get("result")
                if isinstance(result, bool):
                    return result
                if isinstance(result, dict) and "allow" in result:
                    allow = result.get("allow")
                    if isinstance(allow, bool):
                        return allow
        except Exception as exc:
            logger.warning("OPA evaluation failed: %s", exc)
            return None
        return None
