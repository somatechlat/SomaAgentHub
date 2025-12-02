from __future__ import annotations

from time import perf_counter

from fastapi import Depends, FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field, constr

from .local_models import GenerationResult, get_embedding_model, get_text_generator

app = FastAPI(
    title="SomaAgent LLM Hub",
    version="0.1.0",
    description="Centralized deterministic local LLM capabilities (initial hub bootstrap).",
    )

    INFER_REQUESTS = Counter(
    "llm_hub_infer_sync_requests_total", "Number of sync inference requests", ["model"]
    )
    INFER_LATENCY = Histogram(
    "llm_hub_infer_sync_latency_seconds", "Sync inference latency", ["model"]
    )
    EMBED_REQUESTS = Counter(
    "llm_hub_embedding_requests_total", "Embedding requests", ["model"]
    )
    EMBED_LATENCY = Histogram(
    "llm_hub_embedding_latency_seconds", "Embedding latency", ["model"]
    )

    MODEL_NAME = "local-markov-v1"


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
            input: list[constr(strip_whitespace=True, min_length=1)] = Field(
                ..., min_length=1
            )

            class EmbeddingVector(BaseModel):
                embedding: list[float]

                class EmbeddingResponse(BaseModel):
                    model: str
                    vectors: list[EmbeddingVector]
                    vector_length: int

                    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "healthy", "service": "llm-hub"}

        @app.get("/metrics")
    def metrics() -> Response:
        return Response(
    generate_latest(), media_type=CONTENT_TYPE_LATEST
    )

    @app.post(
    "/v1/infer/sync", response_model=InferSyncResponse
    )
    def infer_sync(
    request: InferSyncRequest,
    generator=Depends(get_text_generator),
    ) -> InferSyncResponse:
    start = perf_counter()
    result: GenerationResult = generator.generate(
        request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )
    INFER_REQUESTS.labels(model=MODEL_NAME).inc()
    INFER_LATENCY.labels(model=MODEL_NAME).observe(
        perf_counter() - start
    )
    usage = Usage(
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
    )
    return InferSyncResponse(
        model=MODEL_NAME,
        completion=result.text.strip(),
        usage=usage,
    )

    @app.post(
        "/v1/embeddings",
        response_model=EmbeddingResponse,
    )
    def create_embeddings(
    request: EmbeddingRequest,
    model=Depends(get_embedding_model),
    ) -> EmbeddingResponse:
    start = perf_counter()
    vectors = model.embed(request.input)
    EMBED_REQUESTS.labels(model=model.name).inc()
    EMBED_LATENCY.labels(model=model.name).observe(
        perf_counter() - start
    )
    payload = [
        EmbeddingVector(
            embedding=[float(x) for x in vec]
        )
        for vec in vectors
    ]
    return EmbeddingResponse(
        model=model.name,
        vectors=payload,
        vector_length=len(payload[0].embedding),
    )

    @app.get("/models")
    def list_models():
        return {
    "models": [
        {
            "id": MODEL_NAME,
            "name": "Local Markov Text",
            "status": "ready",
        },
        {
            "id": "local-tfidf-v1",
            "name": "Local TF-IDF Embeddings",
            "status": "ready",
        },
    ]
    }
