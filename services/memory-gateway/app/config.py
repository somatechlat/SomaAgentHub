"""Memory-gateway configuration (secure, env-driven)."""

from services.common.config import get_service_settings
from services.common.config.env_resolver import resolve_env

_SERVICE_NAME = "memory-gateway"

settings = get_service_settings(_SERVICE_NAME)


def _required_env(name: str) -> str:
    value = resolve_env(name)
    if not value:
        raise RuntimeError(f"{name} must be set for memory-gateway")
    return value


SERVICE_PORT = int(getattr(settings, "service_port", 8082))
DATABASE_URL = getattr(settings, "database_url", None) or resolve_env("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL or SOMA_AGENT_HUB_DATABASE_URL must be set")

REDIS_URL = getattr(settings, "redis_url", None) or resolve_env("REDIS_URL")
MILVUS_HOST = resolve_env("MILVUS_HOST", "milvus")
MILVUS_PORT = int(resolve_env("MILVUS_PORT", "19530"))
MILVUS_COLLECTION = resolve_env("MILVUS_COLLECTION", "experiences")
OBJECT_STORE_BUCKET = getattr(settings, "object_store_bucket", "")
OBJECT_STORE_REGION = getattr(settings, "object_store_region", "")
ENVIRONMENT = getattr(settings, "environment", "development")
DEPLOYMENT_MODE = getattr(settings, "deployment_mode", "DEV").upper()


class MemoryGatewayConfig:
    """Public configuration object retained for backward compatibility."""

    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self.milvus_host = MILVUS_HOST
        self.milvus_port = MILVUS_PORT
        self.milvus_collection = MILVUS_COLLECTION
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.bucket_name = OBJECT_STORE_BUCKET
        self.region = OBJECT_STORE_REGION


def get_settings():
    return settings
