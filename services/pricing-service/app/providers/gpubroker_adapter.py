from datetime import UTC, datetime

import httpx

from ..config import get_settings
from ..models import PricingOffer
from services.common.config.base_settings import resolve_env


class GPUBrokerAdapter:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def name(self) -> str:
        return "gpubroker"

    def fetch(self) -> list[PricingOffer]:
        url = self.base_url + "/providers"
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(url, params={"page_size": 100})
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []
        offers: list[PricingOffer] = []
        items = data if isinstance(data, list) else data.get("items") or data.get("providers") or []
        now = datetime.now(UTC)
        for it in items:
            try:
                price_hour = float(it.get("price_per_hour"))
                offers.append(
                    PricingOffer(
                        id=str(it.get("id") or it.get("name") or "gpu-offer"),
                        provider=str(it.get("provider") or it.get("source") or "unknown"),
                        gpu_model=str(it.get("gpu") or it.get("gpu_model") or "unknown"),
                        vram_gb=float(it.get("vram_gb") or 0.0),
                        cpu_cores=int(it.get("cpu_cores") or 0),
                        ram_gb=float(it.get("ram_gb") or 0.0),
                        storage_gb=float(it.get("storage_gb") or 0.0),
                        region=str(it.get("region") or it.get("location") or ""),
                        zone=str(it.get("zone") or ""),
                        availability=float(it.get("availability") or 0.0),
                        spot=bool(it.get("spot") or False),
                        currency=str(it.get("currency") or "USD"),
                        price_per_hour=price_hour,
                        price_per_minute=price_hour / 60.0,
                        tags=list(it.get("tags") or []),
                        frameworks=list(it.get("frameworks") or []),
                        billing_increment_min=int(it.get("billing_increment_min") or 0),
                        min_rent_hours=float(it.get("min_rent_hours") or 0.0),
                        provision_latency_s=float(it.get("provision_latency_s") or 0.0),
                        deprovision_latency_s=float(it.get("deprovision_latency_s") or 0.0),
                        last_seen_at=now,
                        source="gpubroker",
                        confidence=0.8,
                    )
                )
            except Exception:
                continue
        return offers


def get_gpubroker_adapter():
    s = get_settings()
    if not s.gpubroker_url:
        return None
    return GPUBrokerAdapter(s.gpubroker_url)
