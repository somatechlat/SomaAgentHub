"""HTTP routes for the Gateway API."""

from fastapi import APIRouter, Depends

from ..dependencies import request_context_dependency
from ..models.context import RequestContext
from .dashboard import router as dashboard_router

router = APIRouter(prefix="/v1", tags=["gateway"])


@router.get("/status")
def read_status(ctx: RequestContext = Depends(request_context_dependency)) -> dict[str, str]:
    """Return gateway status plus basic request context."""

    return {
        "service": "gateway",
        "state": "ready",
        "tenant": ctx.tenant_id,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }

router.include_router(dashboard_router)
