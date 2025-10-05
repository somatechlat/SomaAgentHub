-- ClickHouse migration: Model performance metrics
-- Tracks model usage, costs, latency, and quality metrics

-- Model usage tracking
CREATE TABLE IF NOT EXISTS model_usage (
    timestamp DateTime,
    model_id String,
    model_provider String,
    user_id String,
    conversation_id String,
    prompt_tokens UInt32,
    completion_tokens UInt32,
    total_tokens UInt32,
    latency_ms Float32,
    cost_usd Float32,
    success UInt8,
    error_type String,
    metadata String  -- JSON metadata
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, model_id, user_id);

-- Model performance aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS model_performance_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, model_id)
AS SELECT
    toStartOfHour(timestamp) as hour,
    model_id,
    model_provider,
    count() as request_count,
    sum(success) as successful_requests,
    sum(total_tokens) as total_tokens,
    avg(latency_ms) as avg_latency_ms,
    quantile(0.95)(latency_ms) as p95_latency_ms,
    quantile(0.99)(latency_ms) as p99_latency_ms,
    sum(cost_usd) as total_cost_usd,
    avg(cost_usd) as avg_cost_usd
FROM model_usage
GROUP BY hour, model_id, model_provider;

-- Cost analytics by model
CREATE MATERIALIZED VIEW IF NOT EXISTS model_cost_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, model_id)
AS SELECT
    toDate(timestamp) as day,
    model_id,
    model_provider,
    count() as request_count,
    sum(cost_usd) as total_cost_usd,
    sum(prompt_tokens) as total_prompt_tokens,
    sum(completion_tokens) as total_completion_tokens,
    avg(cost_usd) as avg_cost_per_request
FROM model_usage
GROUP BY day, model_id, model_provider;

-- A/B test results
CREATE TABLE IF NOT EXISTS ab_test_results (
    experiment_id String,
    variant_id String,
    timestamp DateTime,
    user_id String,
    latency_ms Float32,
    cost_usd Float32,
    user_rating Float32,
    success UInt8,
    metadata String  -- JSON metadata
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (experiment_id, variant_id, timestamp);

-- Fine-tuning jobs
CREATE TABLE IF NOT EXISTS finetuning_jobs (
    job_id String,
    provider String,
    base_model String,
    fine_tuned_model String,
    status String,
    training_examples UInt32,
    validation_examples UInt32,
    epochs UInt8,
    created_at DateTime,
    started_at DateTime,
    completed_at DateTime,
    total_cost_usd Float32,
    metrics String  -- JSON metrics (loss, accuracy, etc.)
) ENGINE = MergeTree()
ORDER BY (created_at, job_id);

-- Model quality ratings
CREATE TABLE IF NOT EXISTS model_quality_ratings (
    timestamp DateTime,
    model_id String,
    conversation_id String,
    user_id String,
    rating Float32,  -- 1-5 scale
    feedback_text String,
    task_category String,
    metadata String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, model_id);

-- Model quality aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS model_quality_daily
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, model_id)
AS SELECT
    toDate(timestamp) as day,
    model_id,
    task_category,
    count() as rating_count,
    avg(rating) as avg_rating,
    quantile(0.5)(rating) as median_rating,
    countIf(rating >= 4) / count() as positive_rate
FROM model_quality_ratings
GROUP BY day, model_id, task_category;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_model_usage_user ON model_usage(user_id) TYPE bloom_filter GRANULARITY 4;
CREATE INDEX IF NOT EXISTS idx_model_usage_conversation ON model_usage(conversation_id) TYPE bloom_filter GRANULARITY 4;
CREATE INDEX IF NOT EXISTS idx_ab_test_experiment ON ab_test_results(experiment_id) TYPE bloom_filter GRANULARITY 4;

-- Insert sample data for testing
INSERT INTO model_usage VALUES
    (now() - INTERVAL 1 HOUR, 'claude-3-sonnet', 'anthropic', 'user1', 'conv1', 100, 200, 300, 1500.0, 0.015, 1, '', '{}'),
    (now() - INTERVAL 1 HOUR, 'gpt-4-turbo', 'openai', 'user2', 'conv2', 150, 250, 400, 2000.0, 0.020, 1, '', '{}'),
    (now() - INTERVAL 2 HOURS, 'llama-3-8b', 'together', 'user3', 'conv3', 120, 180, 300, 800.0, 0.005, 1, '', '{}');

INSERT INTO model_quality_ratings VALUES
    (now() - INTERVAL 1 DAY, 'claude-3-sonnet', 'conv1', 'user1', 4.5, 'Great response', 'coding', '{}'),
    (now() - INTERVAL 1 DAY, 'gpt-4-turbo', 'conv2', 'user2', 4.8, 'Excellent', 'data-analysis', '{}'),
    (now() - INTERVAL 2 DAYS, 'llama-3-8b', 'conv3', 'user3', 4.0, 'Good for simple tasks', 'general', '{}');
