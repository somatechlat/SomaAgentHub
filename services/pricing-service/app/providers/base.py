from typing import List, Protocol
from datetime import datetime, timezone
from ..models import PricingOffer

class ProviderAdapter(Protocol):
    def name(self) -> str: ...
    def fetch(self) -> List[PricingOffer]: ...


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

class StaticAdapter:
    def __init__(self, name: str, rows: List[dict]):
        self._name = name
        self._rows = rows

    def name(self) -> str:
        return self._name

    def fetch(self) -> List[PricingOffer]:
        offers: List[PricingOffer] = []
        for r in self._rows:
            r = dict(r)
            r.setdefault("provider", self._name)
            r.setdefault("currency", "USD")
            r.setdefault("last_seen_at", _now())
            r.setdefault("price_per_minute", r.get("price_per_hour", 0.0) / 60.0)
            offers.append(PricingOffer(**r))
        return offers
