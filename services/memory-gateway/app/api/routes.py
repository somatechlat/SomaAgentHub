"""API endpoints for memory gateway."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from somagent_somabrain import SomaBrainError

from ..core.config import Settings, get_settings
from ..dependencies import get_somabrain_client
from .schemas import RagRetrieveRequest, RecallRequest, RememberRequest


router = APIRouter(prefix="/v1", tags=["memory"])


def _resolve_tenant(request: Request, settings: Settings) -> str:
    tenant_header_value = request.headers.get(settings.tenant_header)
    if tenant_header_value:
        return tenant_header_value
    if settings.default_tenant_id:
        return settings.default_tenant_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing tenant identifier header.",
    )


@router.post("/remember")
async def remember(
    request: RememberRequest,
    http_request: Request,
    somabrain_client=Depends(get_somabrain_client),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Store a document using SomaBrain."""

    tenant_id = _resolve_tenant(http_request, settings)
    try:
        result = await somabrain_client.remember(tenant_id, request)
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SomaBrain remember failed: {exc}",
        ) from exc
    return result if isinstance(result, dict) else {"result": result}


@router.post("/recall")
async def recall(
    request: RecallRequest,
    http_request: Request,
    somabrain_client=Depends(get_somabrain_client),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Recall documents using SomaBrain."""

    tenant_id = _resolve_tenant(http_request, settings)
    try:
        result = await somabrain_client.recall(tenant_id, request)
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SomaBrain recall failed: {exc}",
        ) from exc
    if isinstance(result, dict):
        return result
    return {"results": result}


@router.post("/rag/retrieve")
async def rag_retrieve(
    request: RagRetrieveRequest,
    http_request: Request,
    somabrain_client=Depends(get_somabrain_client),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Proxy SomaBrain's RAG pipeline."""

    tenant_id = _resolve_tenant(http_request, settings)
    try:
        result = await somabrain_client.rag_retrieve(tenant_id, request)
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SomaBrain RAG failed: {exc}",
        ) from exc
    return result if isinstance(result, dict) else {"data": result}
