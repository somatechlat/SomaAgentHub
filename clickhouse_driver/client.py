"""Thin compatibility wrapper exposing the stub Client class under clickhouse_driver.client."""

from __future__ import annotations

from . import Client as _Client
from services.common.config.base_settings import resolve_env


class Client(_Client):
