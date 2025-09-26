"""Simple in‑memory rule store for the Policy Engine.

For the MVP we keep a very small rule set per tenant: a list of
*forbidden* substrings. In a real system this would be persisted in a
database or loaded from a configuration service.
"""

from __future__ import annotations

import time
from typing import Dict, List

# In‑memory store: tenant -> list of forbidden words
_RULES: Dict[str, List[str]] = {
    "tenantA": ["forbidden", "blocked"],
    "tenantB": ["restricted"],
}

# Simple TTL cache for the rule set – refreshed every 60 seconds.
_CACHE_TTL = 60  # seconds
_cache_timestamp = 0.0
_cached_rules: Dict[str, List[str]] = {}


def _refresh_cache() -> None:
    global _cached_rules, _cache_timestamp
    _cached_rules = _RULES.copy()
    _cache_timestamp = time.time()


def get_rules(tenant: str) -> List[str]:
    """Return the list of forbidden substrings for *tenant*.

    The cache is refreshed lazily; if the TTL has expired we copy the
    underlying ``_RULES`` dict. This keeps the function fast for the unit
    tests while still demonstrating a cache‑refresh pattern.
    """
    now = time.time()
    if now - _cache_timestamp > _CACHE_TTL:
        _refresh_cache()
    return _cached_rules.get(tenant, [])

# Helper used by tests to inject custom rules.
def set_rules(tenant: str, rules: List[str]) -> None:
    _RULES[tenant] = rules
    # Invalidate cache immediately.
    global _cache_timestamp
    _cache_timestamp = 0.0
