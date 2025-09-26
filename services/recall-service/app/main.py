from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

app = FastAPI(title="Recall Service", version="0.1.0")

# Simple in‑memory store – suitable for local dev and the current sprint.
_memory_store: Dict[str, Dict[str, Any]] = {}
collection_name = "recall"

class RecallPayload(BaseModel):
    key: str = Field(..., description="Unique key for the recall entry")
    vector: list[float] = Field(..., description="Embedding vector (128‑dim)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary provenance data")

class RecallResponse(BaseModel):
    key: str
    vector: list[float]
    metadata: Dict[str, Any]

@app.post("/v1/recall", response_model=RecallResponse)
async def store(payload: RecallPayload):
    """Store a vector with provenance metadata.
    Returns the stored record. In a real deployment the vector is indexed in Qdrant for fast similarity search.
    """
    _memory_store[payload.key] = {"vector": payload.vector, "metadata": payload.metadata}
    return RecallResponse(key=payload.key, vector=payload.vector, metadata=payload.metadata)

@app.get("/v1/recall/{key}", response_model=RecallResponse)
async def retrieve(key: str):
    """Retrieve a stored vector by key. Raises 404 if not found."""
    entry = _memory_store.get(key)
    if not entry:
        raise HTTPException(status_code=404, detail="Recall entry not found")
    return RecallResponse(key=key, vector=entry["vector"], metadata=entry["metadata"])
