"""Request/response schemas for SLM HTTP fallback."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class SLMBaseModel(BaseModel):
    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class InferSyncRequest(SLMBaseModel):
    prompt: str | None = None
    model: str | None = None


class InferSyncResponse(SLMBaseModel):
    model: str
    output: str
    tokens_used: int | None = None


class EmbeddingRequest(SLMBaseModel):
    text: str | None = None
    model: str | None = None


class EmbeddingResponse(SLMBaseModel):
    model: str
    embedding: list[float]
    dim: int


class HealthResponse(BaseModel):
    status: str = "ok"
    provider: str
    metadata: Dict[str, Any] = {}


class QueueRequest(SLMBaseModel):
    mode: str = "infer_sync"  # infer_sync or embedding
    provider: str | None = None
    model: str | None = None
    payload: Dict[str, Any]


class QueueResponse(BaseModel):
    request_id: str
    status: str = "queued"


class QueueStatusResponse(BaseModel):
    request_id: str
    status: str
    result: Dict[str, Any] | None = None


class AudioTranscriptionRequest(SLMBaseModel):
    audio_base64: str
    format: str = 'wav'
    language: str | None = None
    model: str | None = None


class AudioTranscriptionResponse(BaseModel):
    text: str
    elapsed_ms: float


class AudioSynthesisRequest(SLMBaseModel):
    text: str
    voice: str | None = None
    format: str = 'mp3'
    model: str | None = None


class AudioSynthesisResponse(BaseModel):
    audio_base64: str
    elapsed_ms: float
