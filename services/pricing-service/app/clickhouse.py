from clickhouse_driver import Client

from .config import get_settings
from services.common.config.base_settings import resolve_env

_client = None


def get_client() -> Client:
    global _client
    if _client is None:
        s = get_settings()
        # Minimal parameters; underlying stub may not support extended timeouts.
        _client = Client(
            host=s.clickhouse_host,
            port=s.clickhouse_port,
            user=s.clickhouse_user,
            password=s.clickhouse_password,
            database=s.clickhouse_database,
        )
    return _client
