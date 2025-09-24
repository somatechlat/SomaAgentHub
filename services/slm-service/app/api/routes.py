"""API endpoints for SLM service management."""

from __future__ import annotations

import logging
import time
import httpx
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import Settings, get_settings
from ..core.metrics import EMBED_LATENCY, EMBED_REQUESTS, INFER_LATENCY, INFER_REQUESTS
from ..core.providers import SyncProvider
from ..dependencies import provider_dependency, queue_manager_dependency
from .schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
    InferSyncRequest,
    InferSyncResponse,
    QueueRequest,
    QueueResponse,
    QueueStatusResponse,
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioSynthesisRequest,
    AudioSynthesisResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["slm"])


def _resolve_model(response: Dict[str, Any], request_model: str | None, fallback: str) -> str:
    return str(response.get("model") or request_model or fallback)


@router.post("/infer_sync", response_model=InferSyncResponse)
async def infer_sync(
    request: InferSyncRequest,
    provider: SyncProvider = Depends(provider_dependency),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Run a synchronous inference via the default provider."""

    start = time.perf_counter()
    try:
        result = await provider.infer_sync(request.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("SLM infer_sync provider error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider failure: {exc}",
        ) from exc
    elapsed = time.perf_counter() - start

    model_name = _resolve_model(result if isinstance(result, dict) else {}, request.model, settings.default_provider)
    INFER_REQUESTS.labels(provider=settings.default_provider, model=model_name).inc()
    INFER_LATENCY.labels(provider=settings.default_provider, model=model_name).observe(elapsed)

    if isinstance(result, dict):
        result.setdefault("model", model_name)
        return result
    return {"model": model_name, "output": str(result)}


@router.post("/embedding", response_model=EmbeddingResponse)
async def embedding(
    request: EmbeddingRequest,
    provider: SyncProvider = Depends(provider_dependency),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Generate embeddings via the default provider."""

    start = time.perf_counter()
    try:
        result = await provider.embedding(request.model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("SLM embedding provider error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider failure: {exc}",
        ) from exc
    elapsed = time.perf_counter() - start

    model_name = _resolve_model(result if isinstance(result, dict) else {}, request.model, settings.default_provider)
    EMBED_REQUESTS.labels(provider=settings.default_provider, model=model_name).inc()
    EMBED_LATENCY.labels(provider=settings.default_provider, model=model_name).observe(elapsed)

    if isinstance(result, dict):
        result.setdefault("model", model_name)
        return result
    return {"model": model_name, "embedding": result, "dim": len(result)}


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Simple health indicator."""

    return {
        "status": "ok",
        "provider": settings.default_provider,
        "metadata": {},
    }


@router.post("/requests", response_model=QueueResponse)
async def queue_request(
    request: QueueRequest,
    queue_manager=Depends(queue_manager_dependency),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Enqueue a synchronous or embedding SLM request for async processing."""

    payload = dict(request.payload)
    payload.setdefault("mode", request.mode)
    payload.setdefault("model", request.model)
    payload.setdefault("provider", request.provider or settings.default_provider)
    request_id = await queue_manager.enqueue(payload)
    return {"request_id": request_id, "status": "queued"}


@router.get("/requests/{request_id}", response_model=QueueStatusResponse)
async def get_request_status(
    request_id: str,
    queue_manager=Depends(queue_manager_dependency),
) -> Dict[str, Any]:
    """Return status/result for an async request."""

    result = await queue_manager.fetch_result(request_id)
    if result is None:
        return {"request_id": request_id, "status": "pending", "result": None}
    status_value = result.get("status", "completed")
    return {"request_id": request_id, "status": status_value, "result": result}


@router.post("/audio/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(
    request: AudioTranscriptionRequest,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    if not settings.asr_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ASR provider not configured")
    payload = request.model_dump(mode="json")
    headers = {}
    if settings.voice_api_key:
        headers["Authorization"] = f"Bearer {settings.voice_api_key}"
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(settings.asr_url, json=payload, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=resp.text)
    elapsed = (time.perf_counter() - start) * 1000
    data = resp.json()
    return {
        "text": data.get("text") or data.get("transcript", ""),
        "elapsed_ms": elapsed,
    }


@router.post("/audio/synthesize", response_model=AudioSynthesisResponse)
async def synthesize_audio(
    request: AudioSynthesisRequest,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    if not settings.tts_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TTS provider not configured")
    payload = request.model_dump(mode="json")
    headers = {}
    if settings.voice_api_key:
        headers["Authorization"] = f"Bearer {settings.voice_api_key}"
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(settings.tts_url, json=payload, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=resp.text)
    elapsed = (time.perf_counter() - start) * 1000
    data = resp.json()
    audio = data.get("audio_base64") or data.get("audio")
    if not audio:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Missing audio data")
    return {
        "audio_base64": audio,
        "elapsed_ms": elapsed,
    }
