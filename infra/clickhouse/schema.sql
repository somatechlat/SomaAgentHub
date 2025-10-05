-- ClickHouse Schema for SomaAgent Analytics - Sprint-7
-- Real database schema for real analytics - NO MOCKS!
-- 
-- This creates production-ready tables for:
-- 1. Capsule execution tracking
-- 2. Conversation analytics
-- 3. Policy decision logging
-- 4. Marketplace revenue tracking

-- Database creation (if not exists)
CREATE DATABASE IF NOT EXISTS somaagent;

USE somaagent;

-- =====================================================================
-- CAPSULE EXECUTION EVENTS
-- Tracks every capsule execution for analytics and billing
-- =====================================================================

CREATE TABLE IF NOT EXISTS capsule_executions (
    -- Identity
    execution_id String,
    capsule_id String,
    capsule_version String,
    user_id String,
    session_id String,
    
    -- Timing (Real timestamps, not mocked!)
    started_at DateTime64(3) DEFAULT now64(3),
    completed_at DateTime64(3),
    duration_ms UInt32,
    
    -- Execution metadata
    status Enum8('started' = 1, 'completed' = 2, 'failed' = 3, 'timeout' = 4),
    exit_code Int32,
    error_message String,
    
    -- Resource usage (Real metrics from containers)
    cpu_time_ms UInt32,
    memory_peak_mb UInt32,
    network_bytes_sent UInt64,
    network_bytes_received UInt64,
    
    -- Input/Output tracking
    input_size_bytes UInt32,
    output_size_bytes UInt32,
    input_hash String,  -- SHA256 for deduplication
    
    -- Billing
    compute_cost_usd Decimal(10, 6),
    revenue_usd Decimal(10, 6),
    
    -- Metadata
    agent_id String,
    environment String,  -- 'development', 'staging', 'production'
    region String,       -- Geographic region
    
    -- Indexing for fast queries
    INDEX idx_capsule_id capsule_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_status status TYPE set(0) GRANULARITY 1
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(started_at)
ORDER BY (started_at, capsule_id, user_id)
TTL started_at + INTERVAL 365 DAY  -- Retain for 1 year
SETTINGS index_granularity = 8192;

-- =====================================================================
-- CONVERSATION EVENTS
-- Tracks user conversations for engagement analytics
-- =====================================================================

CREATE TABLE IF NOT EXISTS conversations (
    -- Identity
    conversation_id String,
    session_id String,
    user_id String,
    
    -- Timing
    started_at DateTime64(3) DEFAULT now64(3),
    last_activity_at DateTime64(3),
    ended_at DateTime64(3),
    duration_seconds UInt32,
    
    -- Conversation metadata
    message_count UInt16,
    turn_count UInt16,  -- User-assistant turn pairs
    total_tokens UInt32,
    model_used String,
    
    -- Quality metrics (Real, not mocked!)
    user_satisfaction_score Float32,  -- 0.0 to 1.0
    coherence_score Float32,
    safety_score Float32,
    
    -- Engagement
    has_code_execution Boolean,
    has_file_upload Boolean,
    has_capsule_use Boolean,
    capsules_used Array(String),
    
    -- Outcome
    goal_achieved Boolean,
    goal_description String,
    
    -- Metadata
    interface String,  -- 'web', 'cli', 'api', 'mobile'
    language String,   -- User language
    region String,
    
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter GRANULARITY 1
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(started_at)
ORDER BY (started_at, user_id, conversation_id)
TTL started_at + INTERVAL 180 DAY  -- Retain for 6 months
SETTINGS index_granularity = 8192;

-- =====================================================================
-- POLICY DECISIONS
-- Tracks policy engine evaluations for compliance and safety
-- =====================================================================

CREATE TABLE IF NOT EXISTS policy_decisions (
    -- Identity
    decision_id String,
    session_id String,
    user_id String,
    tenant String,
    
    -- Timing
    evaluated_at DateTime64(3) DEFAULT now64(3),
    evaluation_duration_ms UInt16,
    
    -- Input
    prompt String,
    prompt_hash String,  -- For deduplication
    role String,
    
    -- Decision (Real policy evaluation, not fake!)
    allowed Boolean,
    score Float32,      -- 0.0 to 1.0
    severity Enum8('safe' = 1, 'low' = 2, 'medium' = 3, 'high' = 4, 'critical' = 5),
    
    -- Violations
    violations Array(String),
    violation_count UInt8,
    
    -- Constitution
    constitution_hash String,
    constitution_version String,
    rules_evaluated UInt16,
    
    -- Metadata
    model_used String,
    environment String,
    
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_tenant tenant TYPE bloom_filter GRANULARITY 1,
    INDEX idx_allowed allowed TYPE set(0) GRANULARITY 1,
    INDEX idx_severity severity TYPE set(0) GRANULARITY 1
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(evaluated_at)
ORDER BY (evaluated_at, tenant, user_id)
TTL evaluated_at + INTERVAL 90 DAY  -- Retain for 3 months (compliance)
SETTINGS index_granularity = 8192;

-- =====================================================================
-- MARKETPLACE TRANSACTIONS
-- Tracks capsule purchases, revenue, and marketplace activity
-- =====================================================================

CREATE TABLE IF NOT EXISTS marketplace_transactions (
    -- Identity
    transaction_id String,
    user_id String,
    capsule_id String,
    author_id String,  -- Capsule creator
    
    -- Timing
    transaction_at DateTime64(3) DEFAULT now64(3),
    
    -- Transaction type
    type Enum8('purchase' = 1, 'subscription' = 2, 'usage_fee' = 3, 'tip' = 4),
    
    -- Amounts (Real money, not fake!)
    amount_usd Decimal(10, 6),
    platform_fee_usd Decimal(10, 6),
    author_revenue_usd Decimal(10, 6),
    
    -- Payment
    payment_method String,
    payment_status Enum8('pending' = 1, 'completed' = 2, 'failed' = 3, 'refunded' = 4),
    
    -- Capsule details
    capsule_version String,
    capsule_category String,
    license_type String,
    
    -- Metadata
    currency String DEFAULT 'USD',
    region String,
    
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_capsule_id capsule_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_author_id author_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_status payment_status TYPE set(0) GRANULARITY 1
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(transaction_at)
ORDER BY (transaction_at, capsule_id, user_id)
TTL transaction_at + INTERVAL 2555 DAY  -- Retain for 7 years (financial)
SETTINGS index_granularity = 8192;

-- =====================================================================
-- WORKFLOW EXECUTION EVENTS (KAMACHIQ)
-- Tracks autonomous workflow executions for KAMACHIQ mode
-- =====================================================================

CREATE TABLE IF NOT EXISTS workflow_executions (
    -- Identity
    workflow_id String,
    workflow_type String,
    parent_workflow_id String,  -- For child workflows
    user_id String,
    
    -- Timing
    started_at DateTime64(3) DEFAULT now64(3),
    completed_at DateTime64(3),
    duration_ms UInt32,
    
    -- Status
    status Enum8('running' = 1, 'completed' = 2, 'failed' = 3, 'cancelled' = 4, 'timeout' = 5),
    
    -- Project details
    project_description String,
    task_count UInt16,
    tasks_completed UInt16,
    tasks_failed UInt16,
    
    -- Quality metrics (Real automated review scores)
    quality_score Float32,
    auto_approved Boolean,
    
    -- Resource usage
    agent_spawns UInt16,
    total_tokens UInt32,
    policy_checks UInt16,
    
    -- Results
    deliverables_count UInt8,
    output_size_bytes UInt32,
    
    -- Metadata
    workflow_version String,
    environment String,
    
    INDEX idx_workflow_type workflow_type TYPE bloom_filter GRANULARITY 1,
    INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_status status TYPE set(0) GRANULARITY 1
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(started_at)
ORDER BY (started_at, workflow_type, user_id)
TTL started_at + INTERVAL 365 DAY
SETTINGS index_granularity = 8192;

-- =====================================================================
-- MATERIALIZED VIEWS FOR COMMON QUERIES
-- Pre-aggregated data for fast dashboard queries
-- =====================================================================

-- Hourly capsule execution stats
CREATE MATERIALIZED VIEW IF NOT EXISTS capsule_executions_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, capsule_id)
AS SELECT
    toStartOfHour(started_at) AS hour,
    capsule_id,
    count() AS execution_count,
    countIf(status = 'completed') AS success_count,
    countIf(status = 'failed') AS failure_count,
    avg(duration_ms) AS avg_duration_ms,
    sum(compute_cost_usd) AS total_cost_usd,
    sum(revenue_usd) AS total_revenue_usd,
    uniq(user_id) AS unique_users
FROM capsule_executions
GROUP BY hour, capsule_id;

-- Daily marketplace revenue by capsule
CREATE MATERIALIZED VIEW IF NOT EXISTS marketplace_revenue_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, capsule_id, author_id)
AS SELECT
    toDate(transaction_at) AS day,
    capsule_id,
    author_id,
    count() AS transaction_count,
    sum(amount_usd) AS total_amount_usd,
    sum(platform_fee_usd) AS total_platform_fee_usd,
    sum(author_revenue_usd) AS total_author_revenue_usd,
    uniq(user_id) AS unique_buyers
FROM marketplace_transactions
WHERE payment_status = 'completed'
GROUP BY day, capsule_id, author_id;

-- Hourly policy decision stats
CREATE MATERIALIZED VIEW IF NOT EXISTS policy_decisions_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, tenant, severity)
AS SELECT
    toStartOfHour(evaluated_at) AS hour,
    tenant,
    severity,
    count() AS decision_count,
    countIf(allowed) AS allowed_count,
    countIf(NOT allowed) AS blocked_count,
    avg(score) AS avg_score,
    avg(evaluation_duration_ms) AS avg_duration_ms
FROM policy_decisions
GROUP BY hour, tenant, severity;

-- =====================================================================
-- SAMPLE QUERIES (For Dashboard Testing)
-- =====================================================================

-- Top 10 capsules by execution count (last 7 days)
-- SELECT
--     capsule_id,
--     count() AS executions,
--     countIf(status = 'completed') AS success_count,
--     sum(revenue_usd) AS total_revenue
-- FROM capsule_executions
-- WHERE started_at >= now() - INTERVAL 7 DAY
-- GROUP BY capsule_id
-- ORDER BY executions DESC
-- LIMIT 10;

-- User engagement metrics (last 30 days)
-- SELECT
--     user_id,
--     count(DISTINCT session_id) AS sessions,
--     count(DISTINCT conversation_id) AS conversations,
--     sum(message_count) AS total_messages,
--     avg(user_satisfaction_score) AS avg_satisfaction
-- FROM conversations
-- WHERE started_at >= now() - INTERVAL 30 DAY
-- GROUP BY user_id
-- ORDER BY sessions DESC
-- LIMIT 100;

-- Policy blocking rate by severity (last 24 hours)
-- SELECT
--     severity,
--     count() AS total_decisions,
--     countIf(NOT allowed) AS blocked_count,
--     (blocked_count / total_decisions) * 100 AS block_rate_percent
-- FROM policy_decisions
-- WHERE evaluated_at >= now() - INTERVAL 24 HOUR
-- GROUP BY severity
-- ORDER BY severity;

-- Real-time marketplace revenue (today)
-- SELECT
--     sum(amount_usd) AS total_revenue_usd,
--     sum(platform_fee_usd) AS platform_revenue_usd,
--     sum(author_revenue_usd) AS author_revenue_usd,
--     count() AS transaction_count,
--     uniq(user_id) AS unique_buyers,
--     uniq(capsule_id) AS unique_capsules
-- FROM marketplace_transactions
-- WHERE transaction_at >= toDate(now())
--   AND payment_status = 'completed';

-- =====================================================================
-- GRANTS (For production security)
-- =====================================================================

-- Create analytics readonly user
-- CREATE USER IF NOT EXISTS analytics_readonly
--     IDENTIFIED WITH sha256_password BY 'CHANGE_ME_IN_PRODUCTION';
-- 
-- GRANT SELECT ON somaagent.* TO analytics_readonly;

-- Create ingest user (for services to write data)
-- CREATE USER IF NOT EXISTS analytics_ingest
--     IDENTIFIED WITH sha256_password BY 'CHANGE_ME_IN_PRODUCTION';
-- 
-- GRANT INSERT ON somaagent.* TO analytics_ingest;
