"""LLM Hub configuration using centralized resolver and Vault client."""

import os
from services.common.config.base_settings import resolve_env
from services.common.vault_client import init_vault

SERVICE_NAME = "llm-hub"
SERVICE_PORT = int(resolve_env("SERVICE_PORT", "8084"))

DATABASE_URL = resolve_env(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/soma"
)


def _get_api_key(env_name: str, vault_key: str) -> str:
    # Prefer env variable; fallback to Vault path services/llm-hub
    val = resolve_env(env_name)
    if val:
        return val
    try:
        client = init_vault(role=SERVICE_NAME)
        secret = client.read_secret("services/llm-hub").data.get(vault_key)
        if secret:
            return secret
    except Exception:
        pass
    return ""


OPENAI_API_KEY = _get_api_key("OPENAI_API_KEY", "openai_api_key")
ANTHROPIC_API_KEY = _get_api_key("ANTHROPIC_API_KEY", "anthropic_api_key")
GOOGLE_API_KEY = _get_api_key("GOOGLE_API_KEY", "google_api_key")

DEFAULT_MODEL_PROVIDER = resolve_env("DEFAULT_MODEL_PROVIDER", "openai")
DEFAULT_MODEL = resolve_env("DEFAULT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(resolve_env("MAX_TOKENS", "4000"))
TEMPERATURE = float(resolve_env("TEMPERATURE", "0.7"))

REQUESTS_PER_MINUTE = int(resolve_env("REQUESTS_PER_MINUTE", "60"))
TOKENS_PER_MINUTE = int(resolve_env("TOKENS_PER_MINUTE", "40000"))

ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()


class LLMHubConfig:
    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self.database_url = DATABASE_URL
        self.openai_api_key = OPENAI_API_KEY
        self.anthropic_api_key = ANTHROPIC_API_KEY
        self.google_api_key = GOOGLE_API_KEY
        self.default_model_provider = DEFAULT_MODEL_PROVIDER
        self.default_model = DEFAULT_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.requests_per_minute = REQUESTS_PER_MINUTE
        self.tokens_per_minute = TOKENS_PER_MINUTE
