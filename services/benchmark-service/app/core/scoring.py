"""Scoring heuristics for benchmark results."""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import benchmark_results


async def compute_scores(session: AsyncSession) -> list[dict[str, float | str]]:
    stmt = select(
        benchmark_results.c.provider,
        benchmark_results.c.model,
        benchmark_results.c.role,
        benchmark_results.c.latency_ms,
        benchmark_results.c.tokens,
        benchmark_results.c.cost,
        benchmark_results.c.quality,
        benchmark_results.c.refusal,
    ).order_by(benchmark_results.c.created_at.desc())
    rows = (await session.execute(stmt)).all()
    grouped: dict[tuple[str, str, str], list] = {}
    for row in rows:
        key = (row.provider, row.model, row.role)
        grouped.setdefault(key, []).append(row)

    scores: list[dict[str, float | str]] = []
    for (provider, model, role), items in grouped.items():
        score = _score_items(items)
        scores.append(
            {
                "provider": provider,
                "model": model,
                "role": role,
                "score": score,
                "latency_ms": float(sum(i.latency_ms for i in items) / len(items)),
            }
        )
    return scores


def _score_items(items: Iterable) -> float:
    if not items:
        return 0.0
    total = 0.0
    count = 0
    for item in items:
        latency = max(item.latency_ms, 1.0)
        tokens = item.tokens or 100
        cost = item.cost or 0.0
        quality = item.quality if item.quality is not None else 0.5
        refusal = item.refusal if item.refusal is not None else 0.0

        latency_score = max(0.0, 1.0 - (latency / 2000.0))
        token_score = max(0.0, 1.0 - (tokens / 4000.0))
        cost_score = max(0.0, 1.0 - cost)
        quality_score = quality
        refusal_penalty = max(0.0, 1.0 - refusal)

        total += 0.3 * quality_score + 0.2 * latency_score + 0.2 * token_score + 0.2 * cost_score + 0.1 * refusal_penalty
        count += 1
    return round(total / count, 4)
