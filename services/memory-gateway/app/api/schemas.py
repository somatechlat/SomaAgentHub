"""Request/response models for the memory gateway."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from somagent_somabrain import RecallPayload, RememberPayload, RagRequest


class RememberRequest(RememberPayload):
    """Inherit payload structure while allowing arbitrary extras."""


class RememberResponse(BaseModel):
    status: str = Field(default="accepted")
    memory_id: str

    model_config = {
        "extra": "allow",
    }


class RecallRequest(RecallPayload):
    """Proxy model for recall requests."""


class RecallResponse(BaseModel):
    results: list[Dict[str, Any]]

    model_config = {
        "extra": "allow",
    }


class RagRetrieveRequest(RagRequest):
    """Proxy request body for RAG retrieve operations."""


class RagRetrieveResponse(BaseModel):
    data: Dict[str, Any]

    model_config = {
        "extra": "allow",
    }
