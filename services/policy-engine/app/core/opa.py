from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import httpx
from services.common.config.base_settings import resolve_env

POLICY_DIR = Path(__file__).resolve().parents[1] / "policies" / "budget"
_BUNDLE_CACHE: Dict[str, str] = {}


def load_budget_policy() -> str:
"""Return budget policy Rego source (cached)."""
key = "budget.rego"
if key in _BUNDLE_CACHE:
return _BUNDLE_CACHE[key]
source = (POLICY_DIR / key).read_text(encoding="utf-8")
_BUNDLE_CACHE[key] = source
return source


def evaluate_locally(payload: dict[str, Any]) -> dict[str, Any]:
"""Very small local evaluator replicating the Rego logic for fast unit tests.

This avoids requiring a running OPA sidecar for golden tests. Keep logic
mirrored with `budget.rego`.
"""
estimated_total = float(payload.get("estimated_total", 0.0))
budget_cap = float(payload.get("budget_cap", 0.0))
last_quote_age_min = payload.get("last_quote_age_min")
max_price_age_min = payload.get("max_price_age_min", 30)
quota_used = float(payload.get("quota_used", 0.0))
quota_limit = float(payload.get("quota_limit", quota_used)) or quota_used
drift_ratio = payload.get("drift_ratio")
max_drift_ratio = float(payload.get("max_drift_ratio", 0.2))

within_budget = estimated_total <= budget_cap
not_stale = True
if last_quote_age_min is not None:
try:
not_stale = float(last_quote_age_min) <= float(max_price_age_min)
except Exception:
not_stale = False
within_quota = quota_used <= quota_limit
drift_ok = True if drift_ratio is None else drift_ratio <= max_drift_ratio

allow_pricing = all([within_budget, not_stale, within_quota, drift_ok])

return {
"allow_pricing": allow_pricing,
"within_budget": within_budget,
"not_stale": not_stale,
"within_quota": within_quota,
"drift_ok": drift_ok,
"inputs": payload,
}


async def eval_via_opa(
payload: dict[str, Any], opa_url: str | None = None
) -> dict[str, Any]:
"""Evaluate the budget policy via OPA HTTP API if available.

Falls back to local replication if OPA is unreachable.
"""
if not opa_url:
return evaluate_locally(payload)
endpoint = opa_url.rstrip("/") + "/v1/data/soma/budget/decision"
try:
async with httpx.AsyncClient(timeout=2.0) as client:
resp = await client.post(endpoint, json={"input": payload})
resp.raise_for_status()
data = resp.json()
result = data.get("result") or {}
if not result:
return evaluate_locally(payload)
result["inputs"] = payload
return result
except Exception:
return evaluate_locally(payload)
