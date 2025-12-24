"""Request context extraction for the Django gateway."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.http import HttpRequest


@dataclass
class RequestContext:
    tenant_id: str
    user_id: str | None
    client_type: str
    deployment_mode: str
    capabilities: list[str]
    roles: list[str]

    @classmethod
    def from_request(cls, request: HttpRequest) -> RequestContext:
        headers = request.headers
        tenant_id = headers.get("X-Tenant-ID") or settings.DEFAULT_TENANT_ID
        user_id = headers.get("X-User-ID")
        client_type = headers.get("X-Client-Type") or settings.DEFAULT_CLIENT_TYPE
        deployment_mode = headers.get("X-Deployment-Mode") or settings.DEFAULT_DEPLOYMENT_MODE
        capabilities_header = headers.get("X-Capabilities", "")
        capabilities = [c.strip() for c in capabilities_header.split(",") if c.strip()]
        roles_header = headers.get("X-Roles", "")
        roles = [r.strip() for r in roles_header.split(",") if r.strip()]
        return cls(
            tenant_id=tenant_id,
            user_id=user_id,
            client_type=client_type,
            deployment_mode=deployment_mode,
            capabilities=capabilities,
            roles=roles,
        )

    def as_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "X-Tenant-ID": self.tenant_id,
            "X-Client-Type": self.client_type,
            "X-Deployment-Mode": self.deployment_mode,
        }
        if self.user_id:
            headers["X-User-ID"] = self.user_id
        if self.capabilities:
            headers["X-Capabilities"] = ",".join(self.capabilities)
        if self.roles:
            headers["X-Roles"] = ",".join(self.roles)
        return headers


def get_request_context(request: HttpRequest) -> RequestContext:
    """Return context attached by middleware or derive from headers."""
    ctx = getattr(request, "sah_ctx", None)
    if isinstance(ctx, RequestContext):
        return ctx
    return RequestContext.from_request(request)
