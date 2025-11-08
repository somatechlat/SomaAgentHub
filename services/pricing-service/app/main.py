from fastapi import FastAPI, Query
from typing import Optional, List
from datetime import datetime, timezone
import statistics

from .config import get_settings
from .models import LivePricingResponse, LivePricingSummary, PricingOffer
from .aggregator import fetch_live_offers

app = FastAPI(title="Pricing Service", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/v1/pricing/live", response_model=LivePricingResponse)
def get_live_pricing(
    gpu_model: Optional[str] = Query(None),
    gpu_class: Optional[str] = Query(None),  # placeholder for future grouping
    min_vram_gb: Optional[float] = Query(None, ge=0),
    region: Optional[str] = Query(None),
    cloud: Optional[str] = Query(None),
    spot: Optional[bool] = Query(None),
    max_price_hour: Optional[float] = Query(None, ge=0),
    framework: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str = Query("price_hour"),
    order: str = Query("asc"),
):
    _ = get_settings()  # future: cache usage and OPA hooks
    offers: List[PricingOffer] = fetch_live_offers()

    # Filtering
    def keep(o: PricingOffer) -> bool:
        if gpu_model and gpu_model.lower() not in o.gpu_model.lower():
            return False
        if min_vram_gb is not None and (o.vram_gb or 0) < min_vram_gb:
            return False
        if region and (o.region or "").lower() != region.lower():
            return False
        if cloud and cloud.lower() != o.provider.lower():
            return False
        if spot is not None and o.spot != spot:
            return False
        if max_price_hour is not None and o.price_per_hour > max_price_hour:
            return False
        if framework and framework.lower() not in [f.lower() for f in o.frameworks]:
            return False
        return True

    filtered = [o for o in offers if keep(o)]

    # Sorting
    reverse = order.lower() == "desc"
    key_map = {
        "price_hour": lambda x: x.price_per_hour,
        "availability": lambda x: (x.availability or 0.0),
        "last_seen": lambda x: x.last_seen_at,
    }
    key_fn = key_map.get(sort_by, key_map["price_hour"])  # default
    filtered.sort(key=key_fn, reverse=reverse)

    # Paging
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    # Summary
    prices = [o.price_per_hour for o in filtered]
    median = statistics.median(prices) if prices else None
    p95 = None
    if prices:
        idx = max(0, int(round(0.95 * (len(prices) - 1))))
        p95 = sorted(prices)[idx]
    freshest = max((o.last_seen_at for o in filtered), default=None)

    summary = LivePricingSummary(
        count=total,
        min_price_hour=min(prices) if prices else None,
        median_price_hour=median,
        p95_price_hour=p95,
        freshest_at=freshest,
        is_stale=False,
        scrape_lag_seconds=None,
    )

    meta = {
        "request_id": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    paging = {"page": page, "page_size": page_size, "total": total}

    return LivePricingResponse(offers=page_items, summary=summary, paging=paging, meta=meta)
