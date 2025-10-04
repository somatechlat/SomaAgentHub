"""Configuration for identity service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.somagent_secrets import load_secret


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "identity-service"
    debug: bool = False
    jwk_set_url: str = "https://auth.example.com/.well-known/jwks.json"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str | None = None
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_IDENTITY_", extra="allow")

    def resolve_jwt_secret(self) -> str:
        secret = load_secret("SOMAGENT_IDENTITY_JWT_SECRET", file_env="SOMAGENT_IDENTITY_JWT_SECRET_FILE", default=self.jwt_secret)
        if not secret:
            raise ValueError("JWT secret not configured")
        return secret


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
