from services.common.config.base_settings import resolve_env

DDL_PRICING_OFFERS_LIVE = """
CREATE TABLE IF NOT EXISTS pricing_offers_live (
    id String,
    provider String,
    gpu_model String,
    vram_gb Float32,
    cpu_cores UInt16,
    ram_gb Float32,
    storage_gb Float32,
    region String,
    zone String,
    availability Float32,
    spot UInt8,
    currency FixedString(3),
    price_per_hour Float32,
    price_per_minute Float32,
    tags Array(String),
    frameworks Array(String),
    billing_increment_min UInt16,
    min_rent_hours Float32,
    provision_latency_s Float32,
    deprovision_latency_s Float32,
    last_seen_at DateTime('UTC'),
    source String,
    confidence Float32,
    ingested_at DateTime('UTC') DEFAULT now(),
    PRIMARY KEY (provider, gpu_model, region, id)
) ENGINE = MergeTree ORDER BY (provider, gpu_model, region, id);
"""

DDL_PRICING_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS pricing_snapshots (
    snapshot_id UUID,
    created_at DateTime('UTC') DEFAULT now(),
    offer_count UInt32,
    min_price_hour Float32,
    median_price_hour Float32,
    p95_price_hour Float32,
    hash_fixed String,
    PRIMARY KEY (snapshot_id)
) ENGINE = MergeTree ORDER BY (snapshot_id);
"""

DDL_PRICING_SNAPSHOT_OFFERS = """
CREATE TABLE IF NOT EXISTS pricing_snapshot_offers (
    snapshot_id UUID,
    id String,
    provider String,
    gpu_model String,
    vram_gb Float32,
    cpu_cores UInt16,
    ram_gb Float32,
    storage_gb Float32,
    region String,
    zone String,
    availability Float32,
    spot UInt8,
    currency FixedString(3),
    price_per_hour Float32,
    price_per_minute Float32,
    tags Array(String),
    frameworks Array(String),
    billing_increment_min UInt16,
    min_rent_hours Float32,
    provision_latency_s Float32,
    deprovision_latency_s Float32,
    last_seen_at DateTime('UTC'),
    source String,
    confidence Float32,
    PRIMARY KEY (snapshot_id, provider, gpu_model, region, id)
) ENGINE = MergeTree ORDER BY (snapshot_id, provider, gpu_model, region, id);
"""
