"""API routes for the policy engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from ..core.engine import compute_severity, evaluate as engine_evaluate, score_only as engine_score_only
from ..policy_rules import PolicyRule, get_rules, set_rules
from .schemas import (
    EvaluationRequest,
    EvaluationResponse,
    PolicyRuleModel,
    PolicyUpdateRequest,
    PolicyViolationModel,
    ScoreRequest,
    ScoreResponse,
)

router = APIRouter(prefix="/v1", tags=["policy"])


def _to_violation_model(payload: Dict[str, str | float]) -> PolicyViolationModel:
    data = dict(payload)
    data["description"] = data.get("description") or None
    return PolicyViolationModel(**data)


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_policy(request: EvaluationRequest) -> EvaluationResponse:
    allowed, score, violations_payload, constitution_hash = await engine_evaluate(request.tenant, request.prompt)
    violations = [_to_violation_model(v) for v in violations_payload]
    reasons: Dict[str, List[Dict[str, str | float]]] = {"violations": violations_payload}
    return EvaluationResponse(
        allowed=allowed,
        score=score,
        violations=violations,
        reasons=reasons,
        constitution_hash=constitution_hash,
        evaluated_at=datetime.now(timezone.utc),
    )


@router.post("/score", response_model=ScoreResponse)
async def score_prompt(request: ScoreRequest) -> ScoreResponse:
    score, violations_payload, constitution_hash = await engine_score_only(request.tenant, request.prompt)
    violations = [_to_violation_model(v) for v in violations_payload]
    severity = compute_severity(score)
    return ScoreResponse(
        score=score,
        violation_count=len(violations),
        severity=severity,
        constitution_hash=constitution_hash,
        violations=violations,
    )


@router.get("/policies/{tenant}", response_model=list[PolicyRuleModel])
async def list_policies(tenant: str) -> list[PolicyRuleModel]:
    rules = get_rules(tenant)
    return [PolicyRuleModel(**rule.__dict__) for rule in rules]


@router.put("/policies/{tenant}", response_model=list[PolicyRuleModel])
async def update_policies(tenant: str, payload: PolicyUpdateRequest) -> list[PolicyRuleModel]:
    rules = [
        PolicyRule(
            name=rule.name,
            pattern=rule.pattern,
            weight=rule.weight,
            description=rule.description or "",
            severity=rule.severity,
        )
        for rule in payload.rules
    ]
    set_rules(tenant, rules)
    return payload.rules


@router.post("/policies/{tenant}/rules", response_model=PolicyRuleModel, status_code=status.HTTP_201_CREATED)
async def append_rule(tenant: str, rule: PolicyRuleModel) -> PolicyRuleModel:
    existing = get_rules(tenant)
    if any(r.name == rule.name for r in existing):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rule name already exists")
    updated = existing + [
        PolicyRule(
            name=rule.name,
            pattern=rule.pattern,
            weight=rule.weight,
            description=rule.description or "",
            severity=rule.severity,
        )
    ]
    set_rules(tenant, updated)
    return rule
