"""Placeholder config for gateway API.

Provides minimal settings required for import.
"""

from __future__ import annotations

from functools import lru_cache

# Service-specific configuration
SERVICE_NAME = "gateway-api"
SERVICE_PORT = 8080


class GatewaySettings:
    def __init__(self) -> None:
        self.service_name = SERVICE_NAME
        self.service_port = SERVICE_PORT


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()


settings = get_settings()
