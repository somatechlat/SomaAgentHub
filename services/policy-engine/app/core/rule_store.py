"""Redis-backed rule pack persistence for policy engine.

Allows canonical rule definitions per tenant to be cached in Redis,
supporting dynamic updates and deterministic scoring.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..redis_client import redis_client
from ..policy_rules import PolicyRule


RULE_PACK_TTL = 3600  # 1 hour cache TTL


async def get_rule_pack(tenant: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch rule pack for tenant from Redis cache."""
    key = f"policy:rules:{tenant}"
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def set_rule_pack(tenant: str, rules: List[Dict[str, Any]]) -> None:
    """Store rule pack for tenant in Redis with TTL."""
    key = f"policy:rules:{tenant}"
    try:
        await redis_client.setex(key, RULE_PACK_TTL, json.dumps(rules))
    except Exception:
        pass


async def invalidate_rule_pack(tenant: str) -> None:
    """Invalidate cached rule pack for tenant."""
    key = f"policy:rules:{tenant}"
    try:
        await redis_client.delete(key)
    except Exception:
        pass


def rules_to_dicts(rules: List[PolicyRule]) -> List[Dict[str, Any]]:
    """Convert PolicyRule objects to serializable dicts."""
    return [
        {
            "name": r.name,
            "pattern": r.pattern,
            "weight": r.weight,
            "description": r.description,
            "severity": r.severity,
        }
        for r in rules
    ]


async def load_and_cache_rules(tenant: str, rules: List[PolicyRule]) -> None:
    """Persist canonical rule definitions to Redis for given tenant."""
    await set_rule_pack(tenant, rules_to_dicts(rules))
