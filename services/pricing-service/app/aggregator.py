from typing import List, Tuple
from datetime import datetime, timezone
import time
from .config import get_settings
from .models import PricingOffer

# Placeholder provider data; will be replaced by real adapters.
# Intentionally minimal (not a mock of external calls, just internal stub) to unblock API work.

_SAMPLE = [
    {
        "id": "aws-g5.xlarge",
        "provider": "aws",
        "gpu_model": "A10G",
        "vram_gb": 24,
        "cpu_cores": 4,
        "ram_gb": 16,
        "storage_gb": 50,
        "region": "us-east-1",
        "zone": "us-east-1a",
        "availability": 0.92,
        "spot": False,
        "currency": "USD",
        "price_per_hour": 0.9,
        "tags": ["general"],
        "frameworks": ["pytorch", "tensorflow"],
        "billing_increment_min": 1,
        "last_seen_at": datetime.now(timezone.utc),
        "source": "internal-seed",
        "confidence": 0.7,
    },
    {
        "id": "runpod-a100",
        "provider": "runpod",
        "gpu_model": "A100",
        "vram_gb": 80,
        "cpu_cores": 16,
        "ram_gb": 128,
        "storage_gb": 200,
        "region": "us-west-2",
        "zone": "us-west-2a",
        "availability": 0.65,
        "spot": True,
        "currency": "USD",
        "price_per_hour": 3.2,
        "tags": ["training"],
        "frameworks": ["pytorch"],
        "billing_increment_min": 10,
        "last_seen_at": datetime.now(timezone.utc),
        "source": "internal-seed",
        "confidence": 0.6,
    },
]

_CACHE: Tuple[float, List[PricingOffer]] | None = None


def fetch_live_offers() -> List[PricingOffer]:
    global _CACHE
    now = time.time()
    ttl = get_settings().cache_ttl_seconds
    if _CACHE and (now - _CACHE[0]) < ttl:
        return _CACHE[1]

    offers: List[PricingOffer] = []
    for raw in _SAMPLE:
        raw["price_per_minute"] = raw["price_per_hour"] / 60.0
        offers.append(PricingOffer(**raw))
    _CACHE = (now, offers)
    return offers
