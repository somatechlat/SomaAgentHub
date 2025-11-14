"""Backwards compatibility shim for legacy somagent_secrets import sites."""

from __future__ import annotations

from .core.config import load_secret
from services.common.config.base_settings import resolve_env

__all__ = ["load_secret"]
