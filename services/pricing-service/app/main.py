import logging
import statistics
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, HTTPException, Query
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

from .aggregator import fetch_live_offers
from .bootstrap import ensure_tables
from .clickhouse import get_client
from .config import get_settings
from .models import LivePricingResponse, LivePricingSummary, PricingOffer
from .refresh import start_refresh_loop, stop_refresh_loop


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_tables()
    except Exception as e:
        # Allow app to start even if ClickHouse isn't ready yet
        logger.warning("[pricing-service] table ensure failed: %s", e)
    try:
        Instrumentator().instrument(app).expose(app)
    except Exception as e:
        logger.warning("[pricing-service] metrics init failed: %s", e)
    try:
        start_refresh_loop()
    except Exception as e:
        logger.warning("[pricing-service] refresh loop failed to start: %s", e)
    yield
    try:
        stop_refresh_loop()
    except Exception:
        pass


app = FastAPI(title="Pricing Service", version="0.1.0", lifespan=lifespan)

REQS = Counter("pricing_requests_total", "Requests to pricing endpoints", ["endpoint"])
BUDGET_DECISIONS = Counter(
    "pricing_budget_decisions_total",
    "Budget evaluation decisions",
    ["within_budget", "policy_allow"],
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/pricing/live", response_model=LivePricingResponse)
def get_live_pricing(
    gpu_model: str | None = Query(None),
    gpu_class: str | None = Query(None),  # placeholder for future grouping
    min_vram_gb: float | None = Query(None, ge=0),
    region: str | None = Query(None),
    cloud: str | None = Query(None),
    spot: bool | None = Query(None),
    max_price_hour: float | None = Query(None, ge=0),
    framework: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str = Query("price_hour"),
    order: str = Query("asc"),
):
    _ = get_settings()  # future: cache usage and OPA hooks
    offers: list[PricingOffer] = fetch_live_offers()

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
    REQS.labels(endpoint="live").inc()

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
        "generated_at": datetime.now(UTC).isoformat(),
    }

    paging = {"page": page, "page_size": page_size, "total": total}

    return LivePricingResponse(
        offers=page_items, summary=summary, paging=paging, meta=meta
    )


@app.post("/v1/pricing/snapshot")
def create_snapshot():
    REQS.labels(endpoint="snapshot_create").inc()
    offers: list[PricingOffer] = fetch_live_offers()
    if not offers:
        raise HTTPException(status_code=503, detail="No offers available to snapshot")

    prices = [o.price_per_hour for o in offers]
    median = statistics.median(prices)
    p95 = sorted(prices)[max(0, int(round(0.95 * (len(prices) - 1))))]

    payload_str = "|".join(
        sorted(
            f"{o.provider}:{o.gpu_model}:{o.region}:{o.price_per_hour}" for o in offers
        )
    )
    hash_fixed = uuid.uuid5(uuid.NAMESPACE_DNS, payload_str).hex

    sid = uuid.uuid4()
    ch = get_client()
    # header
    ch.execute(
        """
        INSERT INTO pricing_snapshots (snapshot_id, offer_count, min_price_hour, median_price_hour, p95_price_hour, hash_fixed)
        VALUES
        """,
        [(sid, len(offers), min(prices), median, p95, hash_fixed)],
        types_check=True,
    )
    # rows
    rows = [
        (
            sid,
            o.id,
            o.provider,
            o.gpu_model,
            o.vram_gb or 0.0,
            int(o.cpu_cores or 0),
            o.ram_gb or 0.0,
            o.storage_gb or 0.0,
            o.region or "",
            o.zone or "",
            float(o.availability or 0.0),
            1 if o.spot else 0,
            o.currency,
            o.price_per_hour,
            o.price_per_minute,
            o.tags,
            o.frameworks,
            int(o.billing_increment_min or 0),
            float(o.min_rent_hours or 0.0),
            float(o.provision_latency_s or 0.0),
            float(o.deprovision_latency_s or 0.0),
            o.last_seen_at,
            o.source or "",
            float(o.confidence or 0.0),
        )
        for o in offers
    ]
    ch.execute(
        """
        INSERT INTO pricing_snapshot_offers (
            snapshot_id,id,provider,gpu_model,vram_gb,cpu_cores,ram_gb,storage_gb,region,zone,availability,spot,currency,price_per_hour,price_per_minute,tags,frameworks,billing_increment_min,min_rent_hours,provision_latency_s,deprovision_latency_s,last_seen_at,source,confidence
        ) VALUES
        """,
        rows,
        types_check=True,
    )

    return {"snapshot_id": str(sid), "hash": hash_fixed, "offers": len(offers)}


@app.get("/v1/pricing/snapshot/{snapshot_id}")
def get_snapshot(snapshot_id: str):
    REQS.labels(endpoint="snapshot_get").inc()
    try:
        sid = uuid.UUID(snapshot_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid snapshot_id")

    ch = get_client()
    header = ch.execute(
        "SELECT snapshot_id, created_at, offer_count, min_price_hour, median_price_hour, p95_price_hour, hash_fixed FROM pricing_snapshots WHERE snapshot_id = %(sid)s LIMIT 1",
        {"sid": sid},
        with_column_types=True,
    )
    rows = header[0][0] if header and header[0] else None
    if not rows:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    offers_rows = ch.execute(
        "SELECT id, provider, gpu_model, vram_gb, cpu_cores, ram_gb, storage_gb, region, zone, availability, spot, currency, price_per_hour, price_per_minute, tags, frameworks, billing_increment_min, min_rent_hours, provision_latency_s, deprovision_latency_s, last_seen_at, source, confidence FROM pricing_snapshot_offers WHERE snapshot_id = %(sid)s",
        {"sid": sid},
    )
    offers: list[PricingOffer] = []
    for r in offers_rows:
        offers.append(
            PricingOffer(
                id=r[0],
                provider=r[1],
                gpu_model=r[2],
                vram_gb=r[3],
                cpu_cores=r[4],
                ram_gb=r[5],
                storage_gb=r[6],
                region=r[7],
                zone=r[8],
                availability=r[9],
                spot=bool(r[10]),
                currency=r[11],
                price_per_hour=r[12],
                price_per_minute=r[13],
                tags=r[14],
                frameworks=r[15],
                billing_increment_min=r[16],
                min_rent_hours=r[17],
                provision_latency_s=r[18],
                deprovision_latency_s=r[19],
                last_seen_at=r[20],
                source=r[21],
                confidence=r[22],
            )
        )

    return {
        "snapshot_id": snapshot_id,
        "created_at": rows[1].isoformat() if rows[1] else None,
        "offer_count": rows[2],
        "min_price_hour": rows[3],
        "median_price_hour": rows[4],
        "p95_price_hour": rows[5],
        "hash": rows[6],
        "offers": [o.model_dump() for o in offers],
    }


@app.post("/v1/pricing/evaluate-budget")
def evaluate_budget(
    gpu_model: str | None = None,
    region: str | None = None,
    hours_planned: float = Query(..., gt=0),
    quantity: int = Query(1, ge=1),
    budget_cap: float = Query(..., gt=0),
):
    offers: list[PricingOffer] = fetch_live_offers()
    if gpu_model:
        offers = [o for o in offers if gpu_model.lower() in o.gpu_model.lower()]
    if region:
        offers = [o for o in offers if (o.region or "").lower() == region.lower()]
    if not offers:
        raise HTTPException(status_code=404, detail="No matching offers to evaluate")

    best = min(offers, key=lambda o: o.price_per_hour)
    estimated_cost = best.price_per_hour * hours_planned * quantity
    within = estimated_cost <= budget_cap

    BUDGET_DECISIONS.labels(within_budget=str(within), policy_allow="").inc()
    REQS.labels(endpoint="evaluate_budget").inc()
    return {
        "within_budget": within,
        "estimated_cost": estimated_cost,
        "currency": best.currency,
        "chosen_offer": best.model_dump(),
        "blocking_reason": None if within else "Estimated cost exceeds budget cap",
    }


def _opa_decide(payload: dict) -> dict | None:
    settings = get_settings()
    url = settings.opa_url.rstrip("/") + "/v1/data/somagent/policies/decision"
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.post(url, json={"input": payload})
        if r.status_code == 200:
            data = r.json()
            return data.get("result")
    except Exception as e:
        logger.warning("[pricing-service] OPA call failed: %s", e)
    return None


@app.post("/v1/pricing/evaluate-budget/with-policy")
def evaluate_budget_with_policy(
    gpu_model: str | None = None,
    region: str | None = None,
    hours_planned: float = Query(..., gt=0),
    quantity: int = Query(1, ge=1),
    budget_cap: float = Query(..., gt=0),
    payment_approved: bool = Query(False),
    required_feature: str | None = Query(None),
    current_agents: int = Query(0, ge=0),
):
    offers: list[PricingOffer] = fetch_live_offers()
    if gpu_model:
        offers = [o for o in offers if gpu_model.lower() in o.gpu_model.lower()]
    if region:
        offers = [o for o in offers if (o.region or "").lower() == region.lower()]
    if not offers:
        raise HTTPException(status_code=404, detail="No matching offers to evaluate")

    best = min(offers, key=lambda o: o.price_per_hour)
    estimated_cost = best.price_per_hour * hours_planned * quantity
    within = estimated_cost <= budget_cap

    # Construct OPA input
    opa_input = {
        "estimated_cost": estimated_cost,
        "budget_cap": budget_cap,
        "payment_approved": payment_approved,
        "required_feature": required_feature,
        "current_agents": current_agents,
        "requested_agents": quantity,
        "plan": {
            "max_agents_per_user": None,
            "features": [],
        },
    }

    decision = _opa_decide(opa_input)

    allowed = True
    if isinstance(decision, dict):
        allowed = bool(decision.get("allow_build", True))
    BUDGET_DECISIONS.labels(within_budget=str(within), policy_allow=str(allowed)).inc()
    REQS.labels(endpoint="evaluate_budget_with_policy").inc()
    return {
        "within_budget": within,
        "estimated_cost": estimated_cost,
        "currency": best.currency,
        "chosen_offer": best.model_dump(),
        "policy_decision": decision,
        "blocking_reason": None if within else "Estimated cost exceeds budget cap",
    }
