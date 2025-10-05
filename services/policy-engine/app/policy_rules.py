"""Rule engine used by the policy service."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Literal

from pydantic import BaseModel, Field, ValidationError

try:  # pragma: no cover - redis is optional in tests/local runs
    from redis.asyncio import Redis, from_url as redis_from_url
except Exception:  # pragma: no cover
    Redis = None  # type: ignore[assignment]
    redis_from_url = None  # type: ignore[assignment]

_RULES_FILE = Path(__file__).resolve().parent / "data" / "rules.json"
_REDIS_NAMESPACE = "policy:rules"


class PolicyRule(BaseModel):
    """Definition of a single policy rule."""

    name: str
    pattern: str
    weight: float = Field(default=0.35, ge=0.0, le=1.0)
    description: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"

    model_config = {"extra": "forbid"}


class RulePack(BaseModel):
    """Collection of rules for a specific tenant."""

    tenant: str
    rules: List[PolicyRule]
    version: str = "default"
    source: str = "default"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "allow"}

    def ordered_rules(self) -> List[PolicyRule]:
        return sorted(self.rules, key=lambda rule: (rule.pattern.lower(), rule.name))


class RuleViolation(BaseModel):
    rule: PolicyRule
    excerpt: str

    def model_dump(self) -> Dict[str, str | float]:  # noqa: D401 - compatibility helper
        payload = self.rule.model_dump()
        payload["excerpt"] = self.excerpt
        return payload


def _excerpt_for_pattern(text: str, pattern: str, window: int = 40) -> str:
    lowered = text.lower()
    idx = lowered.find(pattern.lower())
    if idx == -1:
        return text[:window]
    start = max(0, idx - window)
    end = min(len(text), idx + len(pattern) + window)
    return text[start:end]


class RuleEngine:
    """In-memory rule registry with deterministic ordering."""

    def __init__(self, rules: Dict[str, List[PolicyRule]] | None = None) -> None:
        self._rules: Dict[str, List[PolicyRule]] = {}
        if rules:
            for tenant, rule_list in rules.items():
                self.set_rules(tenant, rule_list)

    def list_tenants(self) -> Iterable[str]:
        return self._rules.keys()

    def get_rules(self, tenant: str) -> List[PolicyRule]:
        return list(self._rules.get(tenant, []))

    def set_rules(self, tenant: str, rules: List[PolicyRule]) -> None:
        ordered = [PolicyRule.model_validate(rule) for rule in rules]
        ordered.sort(key=lambda rule: (rule.pattern.lower(), rule.name))
        self._rules[tenant] = ordered

    def add_rule(self, tenant: str, rule: PolicyRule) -> None:
        tenant_rules = self._rules.setdefault(tenant, [])
        tenant_rules.append(PolicyRule.model_validate(rule))
        tenant_rules.sort(key=lambda item: (item.pattern.lower(), item.name))

    def replace(self, mapping: Dict[str, List[PolicyRule]]) -> None:
        self._rules.clear()
        for tenant, rules in mapping.items():
            self.set_rules(tenant, list(rules))

    def evaluate(self, tenant: str, prompt: str) -> tuple[bool, float, List[RuleViolation]]:
        violations: List[RuleViolation] = []
        total_weight = 0.0
        lowered_prompt = prompt.lower()
        for rule in self.get_rules(tenant):
            if rule.pattern.lower() in lowered_prompt:
                violations.append(RuleViolation(rule=rule, excerpt=_excerpt_for_pattern(prompt, rule.pattern)))
                total_weight += rule.weight
        score = round(max(0.0, 1.0 - total_weight), 6)
        allowed = len(violations) == 0
        return allowed, score, violations


def _load_default_rule_packs() -> Dict[str, RulePack]:
    if not _RULES_FILE.exists():  # pragma: no cover - defensive guard
        return {}
    raw = json.loads(_RULES_FILE.read_text(encoding="utf-8"))
    version = raw.get("version", "default")
    packs: Dict[str, RulePack] = {}
    for entry in raw.get("tenants", []):
        tenant = entry.get("tenant")
        if not tenant:
            continue
        try:
            rules = [PolicyRule.model_validate(rule) for rule in entry.get("rules", [])]
        except ValidationError as exc:  # pragma: no cover - invalid config
            raise ValueError(f"Invalid rule definition for tenant '{tenant}'") from exc
        packs[tenant] = RulePack(
            tenant=tenant,
            rules=rules,
            version=entry.get("version", version),
            source="default",
        )
    return packs


RULE_PACKS: Dict[str, RulePack] = _load_default_rule_packs()
engine = RuleEngine({tenant: pack.ordered_rules() for tenant, pack in RULE_PACKS.items()})


async def _get_redis_client() -> Redis | None:
    if redis_from_url is None:
        return None
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    client: Redis = redis_from_url(redis_url, decode_responses=True)
    try:
        await client.ping()
    except Exception:  # pragma: no cover - connection failure
        await client.close()
        return None
    return client


def _apply_rule_packs(packs: Dict[str, RulePack]) -> None:
    RULE_PACKS.clear()
    RULE_PACKS.update(packs)
    engine.replace({tenant: pack.ordered_rules() for tenant, pack in packs.items()})


async def bootstrap_rule_engine(namespace: str = _REDIS_NAMESPACE) -> Dict[str, RulePack]:
    """Load rule packs from Redis if available, otherwise persist defaults."""

    packs: Dict[str, RulePack] = dict(RULE_PACKS)
    client = await _get_redis_client()
    if client is not None:
        try:
            pattern = f"{namespace}:*"
            async for key in client.scan_iter(match=pattern):
                data = await client.get(key)
                if not data:
                    continue
                try:
                    pack = RulePack.model_validate_json(data)
                except ValidationError:
                    continue
                packs[pack.tenant] = pack

            # Persist the merged rules back to Redis to keep canonical view.
            for pack in packs.values():
                await client.set(f"{namespace}:{pack.tenant}", pack.model_dump_json())
        finally:
            await client.close()

    _apply_rule_packs(packs)
    return packs


def get_rule_pack(tenant: str) -> RulePack | None:
    return RULE_PACKS.get(tenant)


def get_rules(tenant: str) -> List[PolicyRule]:
    return engine.get_rules(tenant)


def list_tenants() -> List[str]:
    return sorted(engine.list_tenants())


def set_rules(tenant: str, rules: List[PolicyRule], *, version: str = "runtime", source: str = "in-memory") -> RulePack:
    pack = RulePack(tenant=tenant, rules=[PolicyRule.model_validate(rule) for rule in rules], version=version, source=source)
    RULE_PACKS[tenant] = pack
    engine.set_rules(tenant, pack.ordered_rules())
    return pack


def evaluate_prompt(tenant: str, prompt: str) -> tuple[bool, float, List[RuleViolation]]:
    return engine.evaluate(tenant, prompt)
