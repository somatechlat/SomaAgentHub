"""Shared service boundary contracts.

Each module defines Pydantic models used for inter-service communication.
Contracts must remain backward compatible; version via additive fields.
"""
from __future__ import annotations

__all__ = [
    "pricing",
    "orchestrator",
]
