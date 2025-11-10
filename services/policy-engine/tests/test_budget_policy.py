from __future__ import annotations

import pytest

import sys
from pathlib import Path

# Ensure this service's app/ is importable as top-level for tests
_APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from core.opa import evaluate_locally


@pytest.mark.parametrize(
    "payload,expect",
    [
        (
            {
                "estimated_total": 50,
                "budget_cap": 100,
                "last_quote_age_min": 5,
                "quota_used": 10,
                "quota_limit": 100,
            },
            {"allow_pricing": True, "within_budget": True, "not_stale": True, "within_quota": True, "drift_ok": True},
        ),
        (
            {"estimated_total": 150, "budget_cap": 100, "last_quote_age_min": 5, "quota_used": 10, "quota_limit": 100},
            {"allow_pricing": False, "within_budget": False},
        ),
        (
            {"estimated_total": 50, "budget_cap": 100, "last_quote_age_min": 120, "max_price_age_min": 30, "quota_used": 10, "quota_limit": 100},
            {"allow_pricing": False, "not_stale": False},
        ),
        (
            {"estimated_total": 50, "budget_cap": 100, "last_quote_age_min": 5, "quota_used": 110, "quota_limit": 100},
            {"allow_pricing": False, "within_quota": False},
        ),
        (
            {"estimated_total": 50, "budget_cap": 100, "last_quote_age_min": 5, "quota_used": 10, "quota_limit": 100, "drift_ratio": 0.5, "max_drift_ratio": 0.2},
            {"allow_pricing": False, "drift_ok": False},
        ),
    ],
)
def test_budget_policy_cases(payload, expect):
    result = evaluate_locally(payload)
    for k, v in expect.items():
        assert result[k] == v, f"Expected {k} == {v} got {result[k]} for payload {payload}"

    # Sanity: allow_pricing matches conjunction logic
    conj = all(
        [
            result["within_budget"],
            result["not_stale"],
            result["within_quota"],
            result["drift_ok"],
        ]
    )
    assert result["allow_pricing"] == conj
