from datetime import datetime

from pydantic import BaseModel, Field


class PricingOffer(BaseModel):
    id: str
    provider: str
    gpu_model: str
    vram_gb: float | None = None
    cpu_cores: int | None = None
    ram_gb: float | None = None
    storage_gb: float | None = None
    region: str | None = None
    zone: str | None = None
    availability: float | None = Field(None, ge=0, le=1)
    spot: bool | None = None
    currency: str = "USD"
    price_per_hour: float
    price_per_minute: float
    tags: list[str] = []
    frameworks: list[str] = []
    billing_increment_min: int | None = None
    min_rent_hours: float | None = None
    provision_latency_s: float | None = None
    deprovision_latency_s: float | None = None
    last_seen_at: datetime
    source: str | None = None
    confidence: float | None = Field(None, ge=0, le=1)


class LivePricingSummary(BaseModel):
    count: int
    min_price_hour: float | None = None
    median_price_hour: float | None = None
    p95_price_hour: float | None = None
    freshest_at: datetime | None = None
    is_stale: bool = False
    scrape_lag_seconds: int | None = None


class LivePricingResponse(BaseModel):
    offers: list[PricingOffer]
    summary: LivePricingSummary
    paging: dict
    meta: dict
