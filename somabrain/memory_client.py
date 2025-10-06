"""Client utilities for interacting with SomaBrain memory stores."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:  # pragma: no cover - optional dependency for production
    import numpy as _np  # type: ignore
except Exception:  # pragma: no cover - fallback to standard library math
    _np = None

from .geometry import GeodesicKernel


@dataclass(slots=True)
class RetrievalConfig:
    """Configuration for memory retrieval operations."""

    top_k: int = 8
    include_scores: bool = True
    use_geodesic: Optional[bool] = None


@dataclass(slots=True)
class MemoryResult:
    """Represents a single retrieved memory with optional metadata."""

    memory_id: str
    score: float
    payload: Dict[str, Any]


class MemoryClient:
    """High-level helper for SomaBrain retrieval workflows.

    The client currently expects an injected vector store implementing ``search`` and an optional
    graph store for future bridge-planning experiments. Geodesic similarity is feature-gated via
    ``use_geodesic`` in the ``RetrievalConfig`` or the ``SOMABRAIN_GEODESIC_ENABLED`` environment
    variable.
    """

    def __init__(
        self,
        vector_store: Any,
        *,
        geodesic_kernel: Optional[GeodesicKernel] = None,
        default_top_k: int = 8,
    ) -> None:
        self._vector_store = vector_store
        self._geodesic_kernel = geodesic_kernel or GeodesicKernel()
        env_flag = os.getenv("SOMABRAIN_GEODESIC_ENABLED", "0")
        self._geodesic_enabled_default = env_flag.lower() in {"1", "true", "yes"}
        self._default_top_k = default_top_k

    async def retrieve(
        self,
        embedding: Sequence[float],
        *,
        config: Optional[RetrievalConfig] = None,
    ) -> List[MemoryResult]:
        """Retrieve relevant memories using cosine or geodesic similarity."""

        cfg = config or RetrievalConfig(top_k=self._default_top_k)
        top_k = cfg.top_k or self._default_top_k
        raw_hits = await self._vector_store.search(embedding, limit=top_k)

        use_geodesic = (
            cfg.use_geodesic
            if cfg.use_geodesic is not None
            else self._geodesic_enabled_default
        )
        scores = self._score_results(embedding, raw_hits, use_geodesic)

        results: List[MemoryResult] = []
        for hit, score in zip(raw_hits, scores):
            payload = getattr(hit, "payload", {}) or {}
            memory_id = payload.get("id") or getattr(hit, "id", "unknown")
            result = MemoryResult(memory_id=memory_id, score=score, payload=payload)
            results.append(result)
        return results

    def set_geodesic_default(self, enabled: bool) -> None:
        """Toggle geodesic similarity globally for this client instance."""

        self._geodesic_enabled_default = enabled

    def _score_results(
        self,
        query: Sequence[float],
        hits: Iterable[Any],
        use_geodesic: bool,
    ) -> List[float]:
        embeddings = [self._extract_embedding(hit) for hit in hits]
        if not embeddings:
            return []
        if use_geodesic:
            return self._geodesic_kernel.compute_scores(query, embeddings)
        return self._cosine_scores(query, embeddings)

    def _cosine_scores(
        self,
        query: Sequence[float],
        embeddings: List[Sequence[float]],
    ) -> List[float]:
        if _np is not None:
            q = _np.asarray(query)
            q_norm = _np.linalg.norm(q) or 1.0
            q = q / q_norm
            scores = []
            for emb in embeddings:
                v = _np.asarray(emb)
                v_norm = _np.linalg.norm(v) or 1.0
                v = v / v_norm
                scores.append(float(q.dot(v)))
            return scores

        # Fallback pure Python implementation
        def dot(a: Sequence[float], b: Sequence[float]) -> float:
            return sum(x * y for x, y in zip(a, b))

        def norm(a: Sequence[float]) -> float:
            return sum(x * x for x in a) ** 0.5 or 1.0

        q_norm = norm(query)
        normalized_query = [x / q_norm for x in query]
        scores: List[float] = []
        for emb in embeddings:
            v_norm = norm(emb)
            normalized = [x / v_norm for x in emb]
            scores.append(dot(normalized_query, normalized))
        return scores

    @staticmethod
    def _extract_embedding(hit: Any) -> Sequence[float]:
        if hasattr(hit, "vector") and hit.vector is not None:
            return hit.vector
        if isinstance(hit, dict) and "vector" in hit:
            return hit["vector"]
        raise ValueError("Vector store hit does not contain an embedding vector")
