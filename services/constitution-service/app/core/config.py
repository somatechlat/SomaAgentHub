"""Configuration for the constitution service, using the canonical resolver.

All environment variables are accessed through ``resolve_env`` which reads only
variables prefixed with ``SOMA_AGENT_HUB_``.  This eliminates legacy prefixes and
centralises configuration handling.
"""

from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from services.common.config.base_settings import resolve_env


class Settings(BaseSettings):
    """Runtime configuration for the constitution service."""

    service_name: str = "constitution-service"
    # Build base URL using MEMORY_GATEWAY_PORT (default 10021).
    default_port: ClassVar[str] = resolve_env("MEMORY_GATEWAY_PORT", "10021")
    somabrain_base_url: str = resolve_env(
        "SOMABRAIN_BASE_URL",
        f"http://memory-gateway:{default_port}",
    )
    redis_url: str = resolve_env("REDIS_URL", "redis://redis:6379/0")
    cache_ttl_seconds: int = 30
    http_timeout_seconds: float = 30.0
    sync_interval_seconds: float = 300.0
    sync_enabled: bool = True
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    bundle_path: Path | None = None
    public_key_path: Path | None = None
    private_key_path: Path | None = None
    tenants: list[str] = Field(default_factory=lambda: ["somagent", "tenantA", "tenantB"])
    # No legacy env_prefix – rely on ``resolve_env`` for all values.
    model_config = SettingsConfigDict(env_prefix="", extra="allow")

    def model_post_init(self, __context) -> None:  # pragma: no cover - simple config wiring
        if self.bundle_path is None:
            self.bundle_path = self.data_dir / "constitution_bundle.json"
        if self.public_key_path is None:
            self.public_key_path = self.data_dir / "constitution_public_key.pem"
        if self.private_key_path is None:
            self.private_key_path = self.data_dir / "constitution_private_key.pem"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
