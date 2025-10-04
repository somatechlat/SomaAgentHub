"""Rule engine used by the policy service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List


@dataclass
class PolicyRule:
    """Represents a single policy rule.

    Attributes:
        name: Human-readable rule identifier.
        pattern: Text fragment searched for in prompts (case-insensitive).
        weight: Contribution to risk score; higher weights penalise more.
        description: Optional explanation shown in violations.
        severity: qualitative label used by dashboards.
    """

    name: str
    pattern: str
    weight: float = 0.35
    description: str = ""
    severity: str = "medium"


@dataclass
class RuleViolation:
    rule: PolicyRule
    excerpt: str

    def model_dump(self) -> Dict[str, str | float]:
        payload = asdict(self.rule)
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


@dataclass
class RuleEngine:
    """In-memory rule registry with simple scoring."""

    rules: Dict[str, List[PolicyRule]] = field(default_factory=dict)

    def list_tenants(self) -> Iterable[str]:
        return self.rules.keys()

    def get_rules(self, tenant: str) -> List[PolicyRule]:
        return list(self.rules.get(tenant, []))

    def set_rules(self, tenant: str, rules: List[PolicyRule]) -> None:
        self.rules[tenant] = rules

    def add_rule(self, tenant: str, rule: PolicyRule) -> None:
        tenant_rules = self.rules.setdefault(tenant, [])
        tenant_rules.append(rule)

    def evaluate(self, tenant: str, prompt: str) -> tuple[bool, float, List[RuleViolation]]:
        violations: List[RuleViolation] = []
        total_weight = 0.0
        for rule in self.get_rules(tenant):
            if rule.pattern.lower() in prompt.lower():
                violations.append(RuleViolation(rule=rule, excerpt=_excerpt_for_pattern(prompt, rule.pattern)))
                total_weight += rule.weight
        score = max(0.0, 1.0 - total_weight)
        allowed = not violations
        return allowed, score, violations


# Default rule set bootstrapped for local development/tests.
DEFAULT_RULES: Dict[str, List[PolicyRule]] = {
    "tenantA": [
        PolicyRule(name="blocked-term", pattern="forbidden", weight=0.5, severity="high", description="Tenant A forbids the word 'forbidden'."),
        PolicyRule(name="blocked-term-2", pattern="blocked", weight=0.25, severity="medium"),
    ],
    "tenantB": [
        PolicyRule(name="restricted", pattern="restricted", weight=0.4, severity="high"),
    ],
}


engine = RuleEngine(rules={tenant: list(rules) for tenant, rules in DEFAULT_RULES.items()})


def get_rules(tenant: str) -> List[PolicyRule]:
    return engine.get_rules(tenant)


def set_rules(tenant: str, rules: List[PolicyRule]) -> None:
    engine.set_rules(tenant, rules)


def evaluate_prompt(tenant: str, prompt: str) -> tuple[bool, float, List[RuleViolation]]:
    return engine.evaluate(tenant, prompt)
