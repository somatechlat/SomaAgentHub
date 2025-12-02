"""Shared service boundary contracts.

Each module defines Pydantic models used for inter-service communication.
Contracts must remain backward compatible; version via additive fields.
"""

from __future__ import annotations

from services.common.config.base_settings import resolve_env

__all__ = [
    "pricing",
    "orchestrator",
]
