"""Offer aggregation with adapter failure accounting and TTL cache."""

import time

from prometheus_client import Counter

from .config import get_settings
from .models import PricingOffer
from .providers.aws_adapter import AWS_ADAPTER
from .providers.gpubroker_adapter import get_gpubroker_adapter
from .providers.runpod_adapter import RUNPOD_ADAPTER

_CACHE: tuple[float, list[PricingOffer]] | None = None
CACHE_HITS = Counter("pricing_cache_hits_total", "Cache hits in live offers fetch")
ADAPTER_FAILS = Counter("pricing_adapter_fail_total", "Adapter failures", ["adapter"])


def fetch_live_offers() -> list[PricingOffer]:
    """Fetch live offers from all enabled adapters with caching.

    On adapter failure, increments a failure counter but continues processing other adapters.
    """
    global _CACHE
    now = time.time()
    ttl = get_settings().cache_ttl_seconds
    if _CACHE and (now - _CACHE[0]) < ttl:
        CACHE_HITS.inc()
        return _CACHE[1]

    adapters = [AWS_ADAPTER, RUNPOD_ADAPTER]
    gpubroker = get_gpubroker_adapter()
    if gpubroker:
        adapters.append(gpubroker)

    offers: list[PricingOffer] = []
    for adapter in adapters:
        try:
            for offer in adapter.fetch():
                offers.append(offer)
        except Exception:  # noqa: BLE001
            try:
                name = adapter.name()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                name = adapter.__class__.__name__
            ADAPTER_FAILS.labels(adapter=name).inc()

    _CACHE = (now, offers)
    return offers
