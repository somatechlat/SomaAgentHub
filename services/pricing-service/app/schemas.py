from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class UsageAssumptions(BaseModel):
    hours: float = Field(ge=0, default=1.0)
    tokens: Optional[int] = Field(default=None, ge=0)
    bandwidth_gb: Optional[float] = Field(default=None, ge=0)


class PricingLiveRequest(BaseModel):
    capsule_profile: str
    region: Optional[str] = None
    price_cap: Optional[float] = Field(default=None, ge=0)
    required_tags: List[str] = Field(default_factory=list)
    usage: UsageAssumptions = Field(default_factory=UsageAssumptions)


class SelectedOffer(BaseModel):
    provider: str
    gpu: str
    region: str | None = None
    price_per_hour: float
    availability: str | float | None = None
    last_updated: datetime | None = None


class PricingSummary(BaseModel):
    source: str = "gpubroker"
    snapshot_id: str
    fetched_at: datetime
    ttl_seconds: int = 300
    stale: bool = False
    cache_status: str = "miss"  # hit|miss|stale
    gpubroker_url: Optional[str] = None
    constraints: Dict[str, Any]
    offers_considered: int
    provider_warnings: List[str] = Field(default_factory=list)
    selected_offer: SelectedOffer
    breakdown: Dict[str, Any]
    total_estimated: float


class PricingReconcileRequest(BaseModel):
    snapshot: PricingSummary


class PricingReconcileResponse(BaseModel):
    old_total: float
    new_total: float
    drift_percent: float
    requires_reaccept: bool
    summary: PricingSummary
    receipt_id: Optional[str] = None
