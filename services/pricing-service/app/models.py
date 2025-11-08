from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PricingOffer(BaseModel):
    id: str
    provider: str
    gpu_model: str
    vram_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    ram_gb: Optional[float] = None
    storage_gb: Optional[float] = None
    region: Optional[str] = None
    zone: Optional[str] = None
    availability: Optional[float] = Field(None, ge=0, le=1)
    spot: Optional[bool] = None
    currency: str = "USD"
    price_per_hour: float
    price_per_minute: float
    tags: List[str] = []
    frameworks: List[str] = []
    billing_increment_min: Optional[int] = None
    min_rent_hours: Optional[float] = None
    provision_latency_s: Optional[float] = None
    deprovision_latency_s: Optional[float] = None
    last_seen_at: datetime
    source: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)

class LivePricingSummary(BaseModel):
    count: int
    min_price_hour: Optional[float] = None
    median_price_hour: Optional[float] = None
    p95_price_hour: Optional[float] = None
    freshest_at: Optional[datetime] = None
    is_stale: bool = False
    scrape_lag_seconds: Optional[int] = None

class LivePricingResponse(BaseModel):
    offers: List[PricingOffer]
    summary: LivePricingSummary
    paging: dict
    meta: dict
