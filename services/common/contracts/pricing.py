from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class BudgetPrecheckRequest(BaseModel):
    budget_cap: float = Field(..., description="Maximum allowed spend for the run")
    hours_planned: float = Field(..., description="Planned duration in hours")
    quantity: int = Field(1, ge=1, description="Number of parallel resources")
    gpu_model: str | None = Field(None, description="Optional GPU model hint")


class PolicyDecision(BaseModel):
    policy: str
    allowed: bool
    reason: str | None = None


class CostBreakdown(BaseModel):
    hourly_rate: float | None = None
    estimated_hours: float | None = None
    estimated_total: float | None = None
    currency: str | None = "USD"
    details: dict[str, Any] | None = None


class BudgetPrecheckDecision(BaseModel):
    within_budget: bool = Field(..., description="True if request fits within budget")
    reason: str | None = Field(None, description="Explanation if blocked or borderline")
    cost: CostBreakdown | None = None
    policy: list[PolicyDecision] | None = None


class PricingSnapshot(BaseModel):
    snapshot_id: str
    created_at: str
    source: str | None = None
    prices: dict[str, Any] = Field(default_factory=dict)
