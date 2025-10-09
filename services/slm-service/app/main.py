"""Entry point for the production SLM service (formerly SomaLLMProvider)."""

from __future__ import annotations

from time import perf_counter
from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field, constr
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from slm.local_models import get_embedding_model, get_text_generator
from .observability import setup_observability


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class InferSyncRequest(BaseModel):
    prompt: constr(strip_whitespace=True, min_length=1)
    max_tokens: int = Field(64, ge=1, le=256)
    temperature: float = Field(0.8, ge=0.0, le=2.0)


class InferSyncResponse(BaseModel):
    model: str
    completion: str
    usage: Usage


class EmbeddingRequest(BaseModel):
    input: List[constr(strip_whitespace=True, min_length=1)] = Field(..., min_length=1)


class EmbeddingVector(BaseModel):
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    model: str
    vectors: List[EmbeddingVector]
    vector_length: int


app = FastAPI(
    title="SomaGent SLM Service",
    version="1.0.0",
    description="Serves deterministic local language capabilities without mocks.",
)

# REAL OpenTelemetry instrumentation - no mocks, exports to Prometheus
setup_observability("slm-service", app, service_version="1.0.0")

INFER_REQUESTS = Counter(
    "slm_infer_sync_requests_total",
    "Number of sync inference requests",
    ["model"],
)
INFER_LATENCY = Histogram(
    "slm_infer_sync_latency_seconds",
    "Sync inference latency in seconds",
    ["model"],
)
EMBED_REQUESTS = Counter(
    "slm_embedding_requests_total",
    "Number of embedding requests",
    ["model"],
)
EMBED_LATENCY = Histogram(
    "slm_embedding_latency_seconds",
    "Embedding latency in seconds",
    ["model"],
)


MODEL_NAME = "somasuite-markov-v1"


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    # Standardized health payload
    return {"status": "healthy", "service": "slm-service"}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root():
    return {"message": "SomaGent SLM Service"}


@app.post("/v1/infer/sync", response_model=InferSyncResponse, tags=["slm-service"])
def infer_sync(request: InferSyncRequest, generator=Depends(get_text_generator)) -> InferSyncResponse:
    start = perf_counter()
    result = generator.generate(request.prompt, max_tokens=request.max_tokens, temperature=request.temperature)
    duration = perf_counter() - start
    INFER_REQUESTS.labels(model=MODEL_NAME).inc()
    INFER_LATENCY.labels(model=MODEL_NAME).observe(duration)
    completion = result.text.strip()
    usage = Usage(
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
    )
    return InferSyncResponse(model=MODEL_NAME, completion=completion, usage=usage)


@app.post("/v1/embeddings", response_model=EmbeddingResponse, tags=["slm-service"])
def create_embeddings(request: EmbeddingRequest, model=Depends(get_embedding_model)) -> EmbeddingResponse:
    start = perf_counter()
    vectors = model.embed(request.input)
    duration = perf_counter() - start
    EMBED_REQUESTS.labels(model=model.name).inc()
    EMBED_LATENCY.labels(model=model.name).observe(duration)
    payload = [EmbeddingVector(embedding=[float(x) for x in vec]) for vec in vectors]
    vector_length = len(payload[0].embedding) if payload else 0
    return EmbeddingResponse(model=model.name, vectors=payload, vector_length=vector_length)


@app.post("/v1/chat/completions", response_model=InferSyncResponse, tags=["slm-service"])
def chat_completion(request: InferSyncRequest, generator=Depends(get_text_generator)) -> InferSyncResponse:
    """Backward-compatible endpoint that mirrors the sync inference capability."""
    return infer_sync(request, generator=generator)


@app.get("/models", tags=["slm-service"])
def list_models():
    return {"models": [{"id": MODEL_NAME, "name": "SomaSuite Markov Text", "status": "ready"}]}


@app.post("/models/load", tags=["slm-service"])
def load_model(model: dict):
    requested = model.get("id", MODEL_NAME)
    if requested != MODEL_NAME:
        return {"message": "Model not recognised", "model_id": requested, "status": "ignored"}
    # Model is lazily initialised via get_text_generator; calling it ensures readiness.
    get_text_generator()
    return {"message": "Model ready", "model_id": MODEL_NAME, "status": "ready"}