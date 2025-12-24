"""RBAC middleware enforcing role matrix for /api/v2 gateway endpoints."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from asgiref.sync import sync_to_async
from django.http import HttpRequest, JsonResponse

from admin.common.messages import get_message
from admin.core.models import Principal, Tenant

from .context import get_request_context

logger = logging.getLogger(__name__)


def _match(pattern: str, path: str) -> bool:
    """Match simple REST patterns with `{}` placeholders."""
    p_parts = [p for p in pattern.strip("/").split("/")]
    path_parts = [p for p in path.strip("/").split("/")]
    if len(p_parts) != len(path_parts):
        return False
    for expected, actual in zip(p_parts, path_parts):
        if expected.startswith("{") and expected.endswith("}"):
            continue
        if expected != actual:
            return False
    return True


def _has_role(user_roles: Iterable[str], allowed: set[str]) -> bool:
    roles = {r.lower() for r in user_roles}
    if "admin" in roles:
        return True
    return not allowed.isdisjoint(roles)


class RBACMiddleware:
    """Apply coarse-grained RBAC based on documented matrix."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.rules = [
            # Public/system endpoints
            ("GET", "/api/v2/status", None),
            ("GET", "/api/v2/status/aggregate", None),
            ("GET", "/api/v2/health", None),
            ("GET", "/api/v2/healthz", None),
            ("GET", "/api/v2/ready", None),
            ("GET", "/api/v2/", None),
            # Agents
            ("POST", "/api/v2/agents", {"developer", "admin"}),
            ("GET", "/api/v2/agents/{agent_id}", {"viewer", "operator", "developer", "admin"}),
            ("PUT", "/api/v2/agents/{agent_id}", {"developer", "admin"}),
            # Crews
            ("POST", "/api/v2/crews", {"developer", "admin"}),
            # Workflows
            ("POST", "/api/v2/workflows", {"developer", "admin"}),
            ("POST", "/api/v2/workflows/{workflow_id}/execute", {"operator", "developer", "admin"}),
            ("GET", "/api/v2/instances/{instance_id}", {"viewer", "operator", "developer", "admin"}),
            ("POST", "/api/v2/instances/{instance_id}/replay", {"developer", "admin"}),
            # HITL
            ("POST", "/api/v2/hitls/{session_id}/approve", {"operator", "developer", "admin"}),
            ("POST", "/api/v2/hitls/{session_id}/reject", {"operator", "developer", "admin"}),
            # Capsules
            ("POST", "/api/v2/capsules/{capsule_id}/{version}/run", {"operator", "developer", "admin"}),
            # Metrics (unimplemented; restrict)
            ("GET", "/api/v2/metrics", {"admin"}),
        ]

    async def __call__(self, request: HttpRequest):
        if not request.path.startswith("/api/v2/"):
            return await self._get_response_async(request)

        method = request.method.upper()
        ctx = get_request_context(request)
        db_roles = await _load_roles(ctx.tenant_id, ctx.user_id)
        effective_roles = db_roles or ctx.roles
        matched = next(
            (
                (m, pattern, allowed)
                for (m, pattern, allowed) in self.rules
                if m == method and _match(pattern, request.path)
            ),
            None,
        )
        if matched is None:
            # No explicit rule: block unless admin
            if _has_role(effective_roles, {"admin"}):
                return await self._get_response_async(request)
            return JsonResponse(
                {"detail": get_message("gateway.rbac.unknown_route"), "reason": "rbac_no_rule"},
                status=403,
            )

        _, pattern, allowed = matched
        if allowed is None:
            return await self._get_response_async(request)

        if not effective_roles:
            return JsonResponse(
                {"detail": get_message("gateway.rbac.missing_roles"), "reason": "rbac_missing_roles"},
                status=401,
            )

        if not _has_role(effective_roles, allowed):
            return JsonResponse(
                {
                    "detail": get_message("gateway.rbac.denied"),
                    "reason": "rbac_denied",
                    "required": sorted(allowed),
                },
                status=403,
            )

        return await self._get_response_async(request)

    async def _get_response_async(self, request: HttpRequest):
        response = self.get_response
        if callable(getattr(response, "__call__", None)):
            maybe = response(request)
            if hasattr(maybe, "__await__"):
                return await maybe
            return maybe
        return response  # type: ignore[return-value]


async def _load_roles(tenant_identifier: str | None, user_identifier: str | None) -> list[str]:
    """Load role names from the database for the given tenant/user; return [] on any lookup error."""
    if not tenant_identifier or not user_identifier:
        return []
    try:
        tenant = await _get_tenant(tenant_identifier)
        if tenant is None:
            return []
        principal = await _get_principal(tenant, user_identifier)
        if principal is None:
            return []
        roles = await _get_principal_roles(principal)
        return roles
    except Exception as exc:  # noqa: BLE001
        logger.warning("RBAC DB lookup failed: %s", exc)
        return []


@sync_to_async
def _get_tenant(identifier: str):
    try:
        return Tenant.objects.filter(slug=identifier).first() or Tenant.objects.filter(id=identifier).first()
    except Exception:
        return None


@sync_to_async
def _get_principal(tenant: Tenant, identifier: str):
    try:
        return (
            Principal.objects.filter(tenant=tenant, id=identifier).first()
            or Principal.objects.filter(tenant=tenant, email=identifier).first()
        )
    except Exception:
        return None


@sync_to_async
def _get_principal_roles(principal: Principal) -> list[str]:
    try:
        return list(principal.roles.values_list("name", flat=True))
    except Exception:
        return []
