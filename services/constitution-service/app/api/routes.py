"""API routes for the constitution service."""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from somagent_somabrain import SomaBrainError

from ..core.config import Settings, get_settings
from ..dependencies import get_redis, get_somabrain_client


router = APIRouter(prefix="/v1", tags=["constitution"])


async def _cache_set(redis_client, key: str, value: Dict[str, Any], ttl: int) -> None:
    await redis_client.setex(key, ttl, json.dumps(value))


async def _cache_get(redis_client, key: str) -> Dict[str, Any] | None:
    data = await redis_client.get(key)
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


@router.get("/version")
async def get_version(
    somabrain_client=Depends(get_somabrain_client),
    redis_client=Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Fetch the constitution version, caching it temporarily."""

    cache_key = "constitution:version"
    cached = await _cache_get(redis_client, cache_key)
    if cached:
        return cached
    try:
        result = await somabrain_client.get_constitution_version()
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch constitution version: {exc}",
        ) from exc
    await _cache_set(redis_client, cache_key, result, settings.cache_ttl_seconds)
    return result


@router.post("/validate")
async def validate(
    payload: Dict[str, Any],
    somabrain_client=Depends(get_somabrain_client),
) -> Dict[str, Any]:
    """Validate a constitution payload via SomaBrain."""

    try:
        result = await somabrain_client.validate_constitution(payload)
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Constitution validation failed: {exc}",
        ) from exc
    if isinstance(result, dict):
        return result
    return {"result": result}


@router.post("/checksum")
async def checksum(
    payload: Dict[str, Any],
    somabrain_client=Depends(get_somabrain_client),
) -> Dict[str, Any]:
    """Return checksum for provided constitution payload."""

    try:
        result = await somabrain_client.checksum_constitution(payload)
    except SomaBrainError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Constitution checksum failed: {exc}",
        ) from exc
    if isinstance(result, dict):
        return result
    return {"result": result}
