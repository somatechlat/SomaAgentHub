"""Backwards compatibility shim for legacy somagent_secrets import sites."""

from __future__ import annotations

from .core.config import load_secret

__all__ = ["load_secret"]
