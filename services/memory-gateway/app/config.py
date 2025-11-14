"""
Memory-gateway configuration using centralized resolver and Vault client.

Two modes only: DEV and PROD. DEV mirrors PROD code paths with local fallbacks.
"""

from services.common.config.base_settings import resolve_env
from services.common.vault_client import init_vault

SERVICE_NAME = "memory-gateway"
SERVICE_PORT = int(resolve_env("SERVICE_PORT", "8082"))

# Database configuration
DATABASE_URL = resolve_env(
"DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/soma"
)
REDIS_URL = resolve_env("MEMORY_GATEWAY_REDIS_URL") or resolve_env(
"REDIS_URL", "redis://redis:6379/0"
)


# Vector store configuration
def _get_qdrant_api_key() -> str:
val = resolve_env("QDRANT_API_KEY")
if val:
return val
try:
client = init_vault(role=SERVICE_NAME)
secret = client.read_secret("services/memory-gateway").data.get(
"qdrant_api_key"
)
if secret:
return secret
except Exception:
pass
return ""


QDRANT_URL = resolve_env("MEMORY_GATEWAY_QDRANT_URL") or resolve_env(
"QDRANT_URL", "http://localhost:6333"
)
QDRANT_API_KEY = _get_qdrant_api_key()

# Object storage configuration
OBJECT_STORE_BUCKET = resolve_env("OBJECT_STORE_BUCKET", "")
OBJECT_STORE_REGION = resolve_env("OBJECT_STORE_REGION", "")

# Environment-specific configuration
ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()


# Backward-compatible helpers
def get_service_url(service_name: str) -> str:
key = f"{service_name.upper().replace('-', '_')}_URL"
return resolve_env(key, f"http://{service_name}")


def get_env_var(name: str, default=None):
return resolve_env(name, default)


class MemoryGatewayConfig:
"""Configuration class for memory-gateway service"""

@classmethod
def from_env(cls):
return cls()

def __init__(self):
self.qdrant_url = QDRANT_URL
self.qdrant_api_key = QDRANT_API_KEY
self.database_url = DATABASE_URL
self.redis_url = REDIS_URL
self.bucket_name = OBJECT_STORE_BUCKET
self.region = OBJECT_STORE_REGION
