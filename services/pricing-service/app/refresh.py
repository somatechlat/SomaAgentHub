import logging
import threading
import time

from .aggregator import fetch_live_offers
from .clickhouse import get_client
from .config import get_settings
from .models import PricingOffer

_running = False
logger = logging.getLogger(__name__)


def _ingest_offers(offers: list[PricingOffer]) -> None:
    ch = get_client()
    rows = [
        (
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
        INSERT INTO pricing_offers (
            id, provider, gpu_model, vram_gb, cpu_cores, ram_gb, storage_gb,
            region, zone, availability, spot, currency, price_per_hour,
            price_per_minute, tags, frameworks, billing_increment_min,
            min_rent_hours, provision_latency_s, deprovision_latency_s,
            last_seen_at, source, confidence
        ) VALUES
        """,
        rows,
        types_check=True,
    )


def _refresh_task():
    global _running
    settings = get_settings()
    while _running:
        try:
            logger.info("[pricing-service] Refreshing offers...")
            offers = fetch_live_offers()
            _ingest_offers(offers)
            logger.info(f"[pricing-service] Ingested {len(offers)} offers.")
        except Exception as e:
            logger.error(f"[pricing-service] Refresh failed: {e}")
        time.sleep(settings.refresh_interval_seconds)


def start_refresh_loop():
    global _running
    if _running:
        return
    _running = True
    t = threading.Thread(target=_refresh_task, daemon=True)
    t.start()
    logger.info("[pricing-service] Refresh loop started.")


def stop_refresh_loop():
    global _running
    _running = False
    logger.info("[pricing-service] Refresh loop stopping...")
