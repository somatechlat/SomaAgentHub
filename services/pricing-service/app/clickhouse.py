from clickhouse_driver import Client

from .config import get_settings

_client = None


def get_client() -> Client:
    global _client
    if _client is None:
        s = get_settings()
        _client = Client(
            host=s.clickhouse_host,
            port=s.clickhouse_port,
            user=s.clickhouse_user,
            password=s.clickhouse_password,
            database=s.clickhouse_database,
            connect_timeout=5,
            send_receive_timeout=10,
        )
    return _client
