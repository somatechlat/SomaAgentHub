"""Centralized message catalog for user-facing strings."""

from __future__ import annotations

from typing import Any

_MESSAGES: dict[str, str] = {
    "gateway.aggregate.unreachable": "Downstream service '{service}' is unreachable.",
    "gateway.aggregate.unhealthy_status": "Downstream service '{service}' returned status {code}.",
    "gateway.forward.error": "Downstream service '{service}' returned an error.",
    "gateway.forward.not_found": "Resource not found in downstream service '{service}'.",
    "gateway.forward.unreachable": "Downstream service '{service}' is unreachable.",
    "gateway.opa.denied": "Request blocked by policy (OPA).",
    "gateway.opa.unreachable": "Authorization service unreachable; request blocked.",
    "gateway.auth.expired": "Authentication token is expired.",
    "gateway.auth.invalid": "Authentication token is invalid.",
    "gateway.auth.unreachable": "Authentication service unreachable.",
    "gateway.rbac.denied": "Insufficient role to perform this action.",
    "gateway.rbac.missing_roles": "No roles provided; access denied.",
    "gateway.rbac.unknown_route": "Route not allowed by RBAC configuration.",
    "gateway.rbac.lookup_failed": "Role lookup failed; access denied.",
}


def get_message(code: str, **kwargs: Any) -> str:
    """Return a formatted message for the given code or raise if missing."""
    template = _MESSAGES.get(code)
    if template is None:
        raise KeyError(f"Message code not found: {code}")
    return template.format(**kwargs)
