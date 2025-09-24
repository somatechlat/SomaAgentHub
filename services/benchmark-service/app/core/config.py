"""Configuration for benchmark service."""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderConfig(BaseModel):
    name: str
    model: str
    role: str = "chat"
    payload: dict


class Settings(BaseSettings):
    service_name: str = "benchmark-service"
    debug: bool = False
    slm_base_url: AnyHttpUrl = "http://localhost:8700/v1"
    database_url: str = "postgresql+asyncpg://somagent:somagent@localhost:5432/somagent"
    providers: List[ProviderConfig] = [
        ProviderConfig(name="stub", model="stub", role="chat", payload={"prompt": "Hello"})
    ]
    batch_size: int = 1

    model_config = SettingsConfigDict(env_prefix="SOMAGENT_BENCH_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
