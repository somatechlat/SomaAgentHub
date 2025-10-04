"""Configuration for the constitution service."""

from functools import lru_cache
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "constitution-service"
    # Service URLs are resolved via environment variables for K8s DNS.
    somabrain_base_url: str = os.getenv("SOMABRAIN_BASE_URL", "http://memory-gateway:9696")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_ttl_seconds: int = 30
    http_timeout_seconds: float = 30.0
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    bundle_path: Path | None = None
    public_key_path: Path | None = None
    tenants: list[str] = Field(default_factory=lambda: ["somagent", "tenantA", "tenantB"])
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_CONSTITUTION_", extra="allow")

    def model_post_init(self, __context) -> None:  # pragma: no cover - simple config wiring
        if self.bundle_path is None:
            self.bundle_path = self.data_dir / "constitution_bundle.json"
        if self.public_key_path is None:
            self.public_key_path = self.data_dir / "constitution_public_key.pem"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
