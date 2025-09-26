"""Moderation utilities for gateway request handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import redis.asyncio as redis

from ..models.context import RequestContext
from .config import Settings, get_settings
from .redis import get_redis_client


class ModerationError(RuntimeError):
    """Raised when the moderation system cannot evaluate a request."""


@dataclass
class ModerationVerdict:
    """Result of moderation evaluation."""

    allowed: bool
    strike_count: int
    flagged_terms: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    bypassed: bool = False
    strike_delta: int = 0


class ModerationGuard:
    """Performs lightweight content moderation with strike tracking."""

    def __init__(self, redis_client: redis.Redis, settings: Settings | None = None) -> None:
        self.redis = redis_client
        self.settings = settings or get_settings()
        self.block_terms = self.settings.moderation_terms()
        self.block_after = max(1, self.settings.moderation_block_after_strikes)

    def _strike_key(self, tenant_id: str, user_id: str | None) -> str:
        suffix = user_id or "anonymous"
        return f"{self.settings.moderation_strike_prefix}{tenant_id}:{suffix}"

    async def _get_current_strikes(self, tenant_id: str, user_id: str | None) -> int:
        key = self._strike_key(tenant_id, user_id)
        try:
            value = await self.redis.get(key)
        except redis.RedisError as exc:  # noqa: BLE001
            raise ModerationError("failed to read strike counter") from exc
        if value is None:
            return 0
        try:
            return int(value)
        except ValueError:
            return 0

    async def _increment_strike(self, tenant_id: str, user_id: str | None) -> int:
        key = self._strike_key(tenant_id, user_id)
        try:
            strikes = await self.redis.incr(key)
            if self.settings.moderation_strike_ttl_seconds > 0:
                await self.redis.expire(key, self.settings.moderation_strike_ttl_seconds)
        except redis.RedisError as exc:  # noqa: BLE001
            raise ModerationError("failed to increment strike counter") from exc
        return int(strikes)

    async def evaluate(self, ctx: RequestContext, content: str | None) -> ModerationVerdict:
        """Evaluate content and update strike counters as needed."""

        if "moderation:bypass" in ctx.capabilities:
            strikes = await self._get_current_strikes(ctx.tenant_id, ctx.user_id)
            return ModerationVerdict(
                allowed=True,
                strike_count=strikes,
                bypassed=True,
                reasons=["moderation bypass capability present"],
            )

        text = (content or "").lower()
        if not text.strip():
            strikes = await self._get_current_strikes(ctx.tenant_id, ctx.user_id)
            return ModerationVerdict(allowed=True, strike_count=strikes)

        flagged = [term for term in self.block_terms if term and term in text]
        reasons: List[str] = []
        strikes = await self._get_current_strikes(ctx.tenant_id, ctx.user_id)
        allowed = True
        strike_delta = 0

        if flagged:
            strikes = await self._increment_strike(ctx.tenant_id, ctx.user_id)
            strike_delta = 1
            reasons.append(f"flagged terms: {', '.join(flagged)}")
            if strikes >= self.block_after:
                allowed = False
                reasons.append(
                    f"strike threshold reached ({strikes}/{self.block_after})"
                )
            elif strikes >= self.settings.moderation_warning_strikes:
                reasons.append(
                    f"warning strike {strikes} of {self.block_after}"
                )
        else:
            # decay strikes naturally without mutating counters
            pass

        return ModerationVerdict(
            allowed=allowed,
            strike_count=strikes,
            flagged_terms=flagged,
            reasons=reasons,
            strike_delta=strike_delta,
        )


_moderation_guard: ModerationGuard | None = None


def get_moderation_guard() -> ModerationGuard:
    """Return a cached moderation guard instance."""

    global _moderation_guard
    if _moderation_guard is None:
        client = get_redis_client()
        _moderation_guard = ModerationGuard(client)
    return _moderation_guard
