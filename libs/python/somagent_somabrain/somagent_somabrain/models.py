"""Pydantic models mirroring key SomaBrain payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SomaBrainBaseModel(BaseModel):
    """Base model allowing unknown fields for forward compatibility."""

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class RememberPayload(SomaBrainBaseModel):
    """Request body for `/remember`."""

    text: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class RecallPayload(SomaBrainBaseModel):
    """Request body for `/recall`."""

    query: str
    limit: int = Field(default=10, ge=1, le=100)


class RagRequest(SomaBrainBaseModel):
    """Subset of the SomaBrain RAG request structure."""

    query: str
    universe: Optional[str] = None
    trace_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)
