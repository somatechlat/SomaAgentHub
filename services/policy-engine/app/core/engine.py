"""Core evaluation helpers for the policy engine."""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..constitution_cache import get_cached_hash
from ..policy_rules import RuleViolation, evaluate_prompt


def _violation_to_dict(violation: RuleViolation) -> Dict[str, str | float]:
    rule = violation.rule
    return {
        "name": rule.name,
        "pattern": rule.pattern,
        "weight": rule.weight,
        "severity": rule.severity,
        "description": rule.description,
        "excerpt": violation.excerpt,
    }


def compute_severity(score: float) -> str:
    if score >= 0.8:
        return "low"
    if score >= 0.5:
        return "medium"
    if score >= 0.2:
        return "high"
    return "critical"


async def evaluate(tenant: str, prompt: str) -> Tuple[bool, float, List[Dict[str, str | float]], str]:
    allowed, score, violations = evaluate_prompt(tenant, prompt)
    constitution_hash = await get_cached_hash(tenant)
    violation_payload = [_violation_to_dict(v) for v in violations]
    return allowed, score, violation_payload, constitution_hash


async def score_only(tenant: str, prompt: str) -> Tuple[float, List[Dict[str, str | float]], str]:
    _, score, violations = evaluate_prompt(tenant, prompt)
    constitution_hash = await get_cached_hash(tenant)
    violation_payload = [_violation_to_dict(v) for v in violations]
    return score, violation_payload, constitution_hash