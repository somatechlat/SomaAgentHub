from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SOMABrain Metrics Service")

@app.on_event("startup")
async def startup_event():
    """Initialize Qdrant collections on startup."""
    if _use_qdrant:
        try:
            # Try to create the collection (will fail if it already exists)
            await _qdrant_client.create_collection(
                collection_name="memory",
                vector_size=768,  # Standard embedding size for most models
            )
            print("[STARTUP] Created Qdrant collection: memory (768-dim)")
        except Exception as exc:
            # Collection might already exist, which is fine
            print(f"[STARTUP] Qdrant collection setup: {exc}")

# Qdrant client for vector-backed semantic memory
try:
    from services.common.qdrant_client import get_qdrant_client
    _qdrant_client = get_qdrant_client()
    _use_qdrant = True
except Exception as exc:
    print(f"[QDRANT_WARNING] Qdrant client unavailable, using in-memory store: {exc}")
    _qdrant_client = None
    _use_qdrant = False
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
    if _use_qdrant:
        # Generate embedding via SLM service
        import httpx
        import os
        import json
        
        # Convert value to text for embedding
        text_to_embed = json.dumps(payload.value) if not isinstance(payload.value, str) else payload.value
        
        try:
            slm_url = os.getenv("SOMALLM_PROVIDER_URL") or os.getenv("SLM_SERVICE_URL", "http://localhost:8003")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{slm_url}/v1/embeddings",
                    json={"input": [text_to_embed]}
                )
                response.raise_for_status()
                data = response.json()
                vector = data["vectors"][0]["embedding"]
        except Exception as exc:
            print(f"[SOMALLM_WARNING] Embedding generation failed, using zero vector: {exc}")
            vector = [0.0] * 768  # Fallback to zero vector
        
        await _qdrant_client.upsert_points(
            collection_name="memory",
            points=[
                {
                    "id": payload.key,
                    "vector": vector,
                    "payload": {"key": payload.key, "value": payload.value, "text": text_to_embed},
                }
            ],
        )
    else:
        MEMORY_STORE[payload.key] = payload.value
    return payload

@app.get("/v1/recall/{key}", response_model=RecallResponse)
async def recall(key: str):
    if _use_qdrant:
        try:
            point = await _qdrant_client.get_point(collection_name="memory", point_id=key)
            if point is None:
                raise HTTPException(status_code=404, detail="Key not found")
            return RecallResponse(key=key, value=point.payload.get("value"))
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Key not found: {exc}")
    else:
        if key not in MEMORY_STORE:
            raise HTTPException(status_code=404, detail="Key not found")
        return RecallResponse(key=key, value=MEMORY_STORE[key])

@app.post("/v1/rag/retrieve", response_model=RAGResponse)
async def rag(request: RAGRequest):
    if _use_qdrant:
        # Generate query embedding via SLM service
        import httpx
        import os
        
        try:
            slm_url = os.getenv("SOMALLM_PROVIDER_URL") or os.getenv("SLM_SERVICE_URL", "http://localhost:8003")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{slm_url}/v1/embeddings",
                    json={"input": [request.query]}
                )
                response.raise_for_status()
                data = response.json()
                query_vector = data["vectors"][0]["embedding"]
        except Exception as exc:
            print(f"[SOMALLM_WARNING] Query embedding failed, using zero vector: {exc}")
            query_vector = [0.0] * 768  # Fallback to zero vector
        
        results = await _qdrant_client.search(
            collection_name="memory",
            query_vector=query_vector,
            limit=5,
            score_threshold=0.7,
        )
        
        sources = [r.payload.get("key", "unknown") for r in results]
        # Build answer from retrieved context
        context_texts = [r.payload.get("text", "") for r in results]
        answer = f"Found {len(results)} relevant memories. Top result: {context_texts[0][:100] if context_texts else 'None'}"
        return RAGResponse(answer=answer, sources=sources)
    else:
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
