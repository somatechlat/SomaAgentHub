from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SOMABrain Metrics Service")

# In‑memory key/value store for demo purposes
MEMORY_STORE: dict[str, Any] = {}

class RememberRequest(BaseModel):
    key: str = Field(..., description="Identifier for the memory entry")
    value: Any = Field(..., description="Arbitrary JSON‑serialisable value")

class RecallResponse(BaseModel):
    key: str
    value: Any

class RAGRequest(BaseModel):
    query: str = Field(..., description="Search query for retrieval‑augmented generation")

class RAGResponse(BaseModel):
    answer: str
    sources: list[str] = []

@app.post("/v1/remember", response_model=RememberRequest)
async def remember(payload: RememberRequest):
    MEMORY_STORE[payload.key] = payload.value
    return payload

@app.get("/v1/recall/{key}", response_model=RecallResponse)
async def recall(key: str):
    if key not in MEMORY_STORE:
        raise HTTPException(status_code=404, detail="Key not found")
    return RecallResponse(key=key, value=MEMORY_STORE[key])

@app.post("/v1/rag/retrieve", response_model=RAGResponse)
async def rag(request: RAGRequest):
    # Dummy implementation – echo the query as answer
    return RAGResponse(answer=f"Result for query: {request.query}", sources=[])

# Example metric: a simple counter that increments on each scrape
REQUESTS = Counter("somabrain_requests_total", "Total requests to SOMABrain metrics endpoint")

@app.get("/metrics", response_class=Response)
async def metrics():
    """Expose Prometheus metrics for SOMABrain.

    This endpoint returns a plain‑text format that Prometheus can scrape.
    The default metric increments on every request so that the endpoint is not empty.
    """
    REQUESTS.inc()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/health", tags=["system"])
async def health() -> Response:
    """Simple health check for the memory‑gateway service."""
    return Response(content="OK", media_type="text/plain")
