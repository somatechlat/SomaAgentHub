"""Thin compatibility wrapper exposing the stub Client class under clickhouse_driver.client."""

from __future__ import annotations

from . import Client as _Client


class Client(_Client):
    """Expose the fallback Client under the canonical submodule import."""
