"""Configuration for the SLM service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from somagent_secrets import load_secret


class Settings(BaseSettings):
    """Runtime settings."""

    service_name: str = "slm-service"
    debug: bool = False
    default_provider: str = "stub"
    metrics_namespace: str = "somagent_slm"
    redis_url: str = "redis://localhost:6379/0"
    request_stream: str = "slm:requests"
    result_prefix: str = "slm:results:"
    stream_block_ms: int = 5000
    max_pending: int = 1000
    asr_url: str | None = None
    tts_url: str | None = None
    voice_api_key: str | None = None

    def resolve_voice_api_key(self) -> str | None:
        """Load voice API key via env or file."""

        return load_secret("SOMAGENT_SLM_VOICE_API_KEY", file_env="SOMAGENT_SLM_VOICE_API_KEY_FILE", default=self.voice_api_key)
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_SLM_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
