from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from services.common.config.base_settings import resolve_env


class Settings(BaseSettings):
app_name: str = "pricing-service"
clickhouse_host: str = Field("localhost", alias="CLICKHOUSE_HOST")
clickhouse_port: int = Field(8123, alias="CLICKHOUSE_PORT")
clickhouse_user: str = Field("default", alias="CLICKHOUSE_USER")
clickhouse_password: str = Field("", alias="CLICKHOUSE_PASSWORD")
clickhouse_database: str = Field("soma", alias="CLICKHOUSE_DATABASE")
opa_url: str = Field("http://opa:8181", alias="OPA_URL")
cache_ttl_seconds: int = Field(300, alias="PRICING_CACHE_TTL_SECONDS")
gpubroker_url: str | None = Field(None, alias="GPUBROKER_URL")

model_config = SettingsConfigDict(
env_file=".env", env_file_encoding="utf-8", extra="ignore"
)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
return Settings()  # type: ignore[call-arg]
