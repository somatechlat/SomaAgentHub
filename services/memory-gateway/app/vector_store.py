"""Vector store abstraction (Milvus-backed with in-memory fallback)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from services.common.config.base_settings import resolve_env
from services.common.milvus_client import MilvusClient

logger = logging.getLogger(__name__)


class VectorBackend(str, Enum):
    MILVUS = "milvus"
    MEMORY = "memory"


@dataclass
class VectorDocument:
    id: str
    embedding: list[float]
    metadata: dict[str, Any]


class VectorStore:
    """Minimal vector store wrapper supporting upsert and search."""

    def __init__(self, backend: VectorBackend = VectorBackend.MILVUS):
        self.backend = backend
        self._memory: dict[str, VectorDocument] = {}
        if self.backend == VectorBackend.MILVUS:
            host = resolve_env("MILVUS_HOST", "milvus")
            port = int(resolve_env("MILVUS_PORT", "19530"))
            collection = resolve_env("MILVUS_COLLECTION", "experiences")
            self.client = MilvusClient(host=host, port=port, collection=collection)
        else:
            self.client = None

    def upsert(self, documents: Sequence[VectorDocument]) -> None:
        if not documents:
            return
        if self.backend == VectorBackend.MILVUS and self.client:
            points = [{"id": doc.id, "vector": doc.embedding, "payload": doc.metadata} for doc in documents]
            self.client.upsert(points)
            return
        for doc in documents:
            self._memory[doc.id] = doc

    def search(self, embedding: list[float], top_k: int = 5) -> list[VectorDocument]:
        if self.backend == VectorBackend.MILVUS and self.client:
            hits = self.client.search(query_vector=embedding, limit=top_k)
            return [
                VectorDocument(
                    id=str(hit["id"]),
                    embedding=embedding,
                    metadata=hit.get("payload", {}),
                )
                for hit in hits
            ]

        # naive cosine similarity for memory fallback
        def _cos(a: list[float], b: list[float]) -> float:
            import math

            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            return dot / (na * nb + 1e-9)

        scored = [(_cos(embedding, doc.embedding), doc) for doc in self._memory.values()]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        backend = VectorBackend(resolve_env("VECTOR_BACKEND", "milvus"))
        _vector_store = VectorStore(backend=backend)
    return _vector_store
