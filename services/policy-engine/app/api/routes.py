"""API endpoints for the policy engine."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..core.config import Settings, get_settings
from .schemas import PolicyEvaluationRequest, PolicyEvaluationResponse


router = APIRouter(prefix="/v1", tags=["policy"])


def _compute_threshold(request: PolicyEvaluationRequest, settings: Settings) -> float:
    if request.deployment_mode in {"production", "production-debug"}:
        return settings.production_threshold
    return settings.default_threshold


@router.post("/evaluate", response_model=PolicyEvaluationResponse)
def evaluate(
    action: PolicyEvaluationRequest,
    settings: Settings = Depends(get_settings),
) -> PolicyEvaluationResponse:
    """Evaluate an action payload against policy heuristics."""

    threshold = _compute_threshold(action, settings)

    # Compute normalized budget ratio
    if action.budget_remaining is not None and action.budget_required > 0:
        ratio = min(1.0, action.budget_remaining / max(action.budget_required, 1e-9))
    else:
        ratio = 1.0

    score = (
        settings.confidence_weight * action.confidence
        + settings.risk_weight * (1.0 - action.risk_score)
        + settings.cost_weight * ratio
    )

    reasons: List[str] = []
    reasons.append(f"confidence contribution: {settings.confidence_weight * action.confidence:.2f}")
    reasons.append(f"risk contribution: {settings.risk_weight * (1.0 - action.risk_score):.2f}")
    reasons.append(f"cost contribution: {settings.cost_weight * ratio:.2f}")

    if action.requires_human:
        score -= settings.human_gate_penalty
        reasons.append(f"human review penalty: -{settings.human_gate_penalty:.2f}")

    allow = score >= threshold
    reasons.append(f"threshold: {threshold:.2f}")

    return PolicyEvaluationResponse(
        score=float(round(score, 4)),
        allow=allow,
        threshold=threshold,
        reasons=reasons,
    )
