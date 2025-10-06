"""Geometry helpers for SomaBrain retrieval strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import math


@dataclass
class GeodesicConfig:
    """Tuning parameters for geodesic similarity."""

    beta: float = 0.8
    temperature: float = 0.05
    epsilon: float = 1e-9


class GeodesicKernel:
    """Computes soft geodesic scores over spherical embeddings.

    This implementation is intentionally lightweight: it provides the structure for future
    accelerated implementations while offering a deterministic fallback that mirrors cosine
    similarity. The kernel normalizes embeddings onto the unit sphere and then computes
    exponential weights over the angular distance.
    """

    def __init__(self, config: GeodesicConfig | None = None) -> None:
        self._config = config or GeodesicConfig()

    def compute_scores(
        self,
        query: Sequence[float],
        candidates: Iterable[Sequence[float]],
    ) -> List[float]:
        """Return a score per candidate using a soft geodesic kernel."""

        q = _normalize(query, self._config.epsilon)
        scores: List[float] = []
        for vector in candidates:
            v = _normalize(vector, self._config.epsilon)
            cosine = _dot(q, v)
            theta = math.acos(max(-1.0, min(1.0, cosine)))
            score = math.exp(-self._config.beta * theta) / max(
                self._config.temperature, self._config.epsilon
            )
            scores.append(score)
        return scores


def _normalize(vector: Sequence[float], epsilon: float) -> Tuple[float, ...]:
    norm = math.sqrt(sum(component * component for component in vector))
    if norm <= epsilon:
        return tuple(vector)
    return tuple(component / norm for component in vector)


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
