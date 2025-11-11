"""Redis-backed rule pack persistence for policy engine.

Allows canonical rule definitions per tenant to be cached in Redis,
supporting dynamic updates and deterministic scoring.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..policy_rules import PolicyRule
from ..redis_client import redis_client
from services.common.config.base_settings import resolve_env

RULE_PACK_TTL = 3600  # 1 hour cache TTL


logger = logging.getLogger("policy.rule_store")


async def get_rule_pack(tenant: str) -> list[dict[str, Any]] | None:
"""Fetch rule pack for tenant from Redis cache.

Returns None if missing. Logs and propagates errors only for deserialization issues;
connection errors are logged and result in None (tolerant read path).
"""
key = f"policy:rules:{tenant}"
try:
data = await redis_client.get(key)
if data:
try:
return json.loads(data)
except Exception as exc:
logger.error("Failed to decode rule pack for %s: %s", tenant, exc)
raise
except Exception as exc:
logger.warning("Redis rule pack fetch failed for %s: %s", tenant, exc)
return None


async def set_rule_pack(tenant: str, rules: list[dict[str, Any]]) -> None:
"""Store rule pack for tenant in Redis with TTL."""
key = f"policy:rules:{tenant}"
try:
await redis_client.setex(key, RULE_PACK_TTL, json.dumps(rules))
except Exception as exc:
logger.error("Failed to persist rule pack for %s: %s", tenant, exc)


async def invalidate_rule_pack(tenant: str) -> None:
"""Invalidate cached rule pack for tenant."""
key = f"policy:rules:{tenant}"
try:
await redis_client.delete(key)
except Exception as exc:
logger.warning("Failed to invalidate rule pack for %s: %s", tenant, exc)


def rules_to_dicts(rules: list[PolicyRule]) -> list[dict[str, Any]]:
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


async def load_and_cache_rules(tenant: str, rules: list[PolicyRule]) -> None:
"""Persist canonical rule definitions to Redis for given tenant."""
await set_rule_pack(tenant, rules_to_dicts(rules))
