from .clickhouse import get_client
from .ddl import (
    DDL_PRICING_OFFERS_LIVE,
    DDL_PRICING_SNAPSHOT_OFFERS,
    DDL_PRICING_SNAPSHOTS,
)


def ensure_tables():
    client = get_client()
    client.execute(DDL_PRICING_OFFERS_LIVE)
    client.execute(DDL_PRICING_SNAPSHOTS)
    client.execute(DDL_PRICING_SNAPSHOT_OFFERS)
