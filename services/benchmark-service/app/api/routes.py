"""Benchmark service API."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import Settings, get_settings
from ..core.db import get_engine, get_session_maker, benchmark_results
from ..core.scoring import compute_scores

router = APIRouter(prefix="/v1", tags=["benchmark"])

_engine = get_engine()
_SessionMaker = get_session_maker(_engine)


async def get_session() -> AsyncSession:
    async with _SessionMaker() as session:
        yield session


async def run_single_benchmark(client: httpx.AsyncClient, provider_payload: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    mode = provider_payload.get("mode", "infer_sync")
    endpoint = "/infer_sync" if mode == "infer_sync" else "/embedding"
    start = time.perf_counter()
    response = await client.post(f"{base_url}{endpoint}", json=provider_payload.get("payload", {}))
    elapsed = (time.perf_counter() - start) * 1000
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"SLM call failed: {response.text}")
    data = response.json()
    data.setdefault("latency_ms", elapsed)
    return data


@router.post("/run")
async def run_benchmarks(settings: Settings = Depends(get_settings), session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        results: List[Dict[str, Any]] = []
        for provider in settings.providers:
            payload = {
                "mode": provider.payload.get("mode", "infer_sync"),
                "payload": provider.payload,
            }
            try:
                result = await run_single_benchmark(client, payload, settings.slm_base_url)
            except HTTPException as exc:
                raise exc
            results.append(
                {
                    "provider": provider.name,
                    "model": provider.model,
                    "role": provider.role,
                    "latency_ms": result.get("latency_ms", 0.0),
                    "tokens": result.get("tokens_used") or result.get("tokens"),
                    "cost": result.get("cost"),
                    "quality": result.get("quality"),
                    "refusal": result.get("refusal_rate"),
                }
            )

        for item in results:
            await session.execute(
                benchmark_results.insert().values(**item)
            )
        await session.commit()
    return {"runs": len(results)}


@router.get("/scores")
async def list_scores(session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    scores = await compute_scores(session)
    return {"scores": scores}
