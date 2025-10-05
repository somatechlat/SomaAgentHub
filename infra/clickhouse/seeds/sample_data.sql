-- Sample data for ClickHouse testing
-- Sprint-7: Seed data for development and testing

USE somaagent;

-- Sample capsule executions
INSERT INTO capsule_executions (
    execution_id,
    capsule_id,
    capsule_version,
    user_id,
    session_id,
    started_at,
    completed_at,
    duration_ms,
    status,
    exit_code,
    cpu_time_ms,
    memory_peak_mb,
    compute_cost_usd,
    revenue_usd,
    agent_id,
    environment,
    region
) VALUES
    ('exec_001', 'capsule_python_calculator', '1.0.0', 'user_demo', 'session_001', now64(3) - INTERVAL 1 HOUR, now64(3) - INTERVAL 59 MINUTE, 60000, 'completed', 0, 45000, 128, 0.001, 0.01, 'agent_001', 'production', 'us-west-2'),
    ('exec_002', 'capsule_data_analyzer', '2.1.0', 'user_demo', 'session_002', now64(3) - INTERVAL 30 MINUTE, now64(3) - INTERVAL 25 MINUTE, 300000, 'completed', 0, 280000, 512, 0.005, 0.05, 'agent_002', 'production', 'us-west-2'),
    ('exec_003', 'capsule_image_processor', '1.5.2', 'user_test', 'session_003', now64(3) - INTERVAL 15 MINUTE, now64(3) - INTERVAL 10 MINUTE, 300000, 'failed', 1, 120000, 1024, 0.003, 0.00, 'agent_003', 'staging', 'us-east-1');

-- Sample conversations
INSERT INTO conversations (
    conversation_id,
    session_id,
    user_id,
    started_at,
    last_activity_at,
    ended_at,
    duration_seconds,
    message_count,
    turn_count,
    total_tokens,
    model_used,
    user_satisfaction_score,
    coherence_score,
    safety_score,
    has_code_execution,
    has_capsule_use,
    capsules_used,
    goal_achieved,
    interface,
    language,
    region
) VALUES
    ('conv_001', 'session_001', 'user_demo', now64(3) - INTERVAL 2 HOUR, now64(3) - INTERVAL 1 HOUR, now64(3) - INTERVAL 1 HOUR, 3600, 25, 12, 4500, 'llama-3.2-1b', 0.85, 0.92, 0.98, true, true, ['capsule_python_calculator'], true, 'web', 'en', 'us-west-2'),
    ('conv_002', 'session_002', 'user_demo', now64(3) - INTERVAL 1 HOUR, now64(3) - INTERVAL 30 MINUTE, now64(3) - INTERVAL 30 MINUTE, 1800, 18, 9, 3200, 'llama-3.2-3b', 0.90, 0.88, 0.95, true, true, ['capsule_data_analyzer'], true, 'web', 'en', 'us-west-2'),
    ('conv_003', 'session_003', 'user_test', now64(3) - INTERVAL 30 MINUTE, now64(3) - INTERVAL 15 MINUTE, now64(3) - INTERVAL 15 MINUTE, 900, 10, 5, 1800, 'llama-3.2-1b', 0.65, 0.75, 0.88, true, true, ['capsule_image_processor'], false, 'cli', 'en', 'us-east-1');

-- Sample policy decisions
INSERT INTO policy_decisions (
    decision_id,
    session_id,
    user_id,
    tenant,
    evaluated_at,
    evaluation_duration_ms,
    prompt,
    prompt_hash,
    role,
    allowed,
    score,
    severity,
    violations,
    violation_count,
    constitution_hash,
    constitution_version,
    rules_evaluated,
    model_used,
    environment
) VALUES
    ('policy_001', 'session_001', 'user_demo', 'tenant_default', now64(3) - INTERVAL 2 HOUR, 45, 'Calculate 2+2', 'hash_001', 'user', true, 0.98, 'safe', [], 0, 'const_v1', '1.0.0', 5, 'llama-3.2-1b', 'production'),
    ('policy_002', 'session_002', 'user_demo', 'tenant_default', now64(3) - INTERVAL 1 HOUR, 52, 'Analyze sales data', 'hash_002', 'user', true, 0.92, 'safe', [], 0, 'const_v1', '1.0.0', 8, 'llama-3.2-3b', 'production'),
    ('policy_003', 'session_003', 'user_test', 'tenant_test', now64(3) - INTERVAL 30 MINUTE, 68, 'Execute system command', 'hash_003', 'user', false, 0.35, 'high', ['system_command_attempt'], 1, 'const_v1', '1.0.0', 12, 'llama-3.2-1b', 'staging');

-- Sample marketplace transactions
INSERT INTO marketplace_transactions (
    transaction_id,
    user_id,
    capsule_id,
    author_id,
    transaction_at,
    type,
    amount_usd,
    platform_fee_usd,
    author_revenue_usd,
    payment_method,
    payment_status,
    capsule_version,
    capsule_category,
    license_type,
    region
) VALUES
    ('txn_001', 'user_demo', 'capsule_python_calculator', 'author_alice', now64(3) - INTERVAL 3 DAY, 'purchase', 9.99, 2.00, 7.99, 'credit_card', 'completed', '1.0.0', 'utilities', 'MIT', 'us-west-2'),
    ('txn_002', 'user_demo', 'capsule_data_analyzer', 'author_bob', now64(3) - INTERVAL 1 DAY, 'subscription', 49.99, 10.00, 39.99, 'credit_card', 'completed', '2.1.0', 'analytics', 'Commercial', 'us-west-2'),
    ('txn_003', 'user_test', 'capsule_image_processor', 'author_charlie', now64(3) - INTERVAL 12 HOUR, 'usage_fee', 2.50, 0.50, 2.00, 'credit_card', 'completed', '1.5.2', 'media', 'Apache-2.0', 'us-east-1');

-- Sample workflow executions
INSERT INTO workflow_executions (
    workflow_id,
    workflow_type,
    parent_workflow_id,
    user_id,
    started_at,
    completed_at,
    duration_ms,
    status,
    project_description,
    task_count,
    tasks_completed,
    tasks_failed,
    quality_score,
    auto_approved,
    agent_spawns,
    total_tokens,
    policy_checks,
    deliverables_count,
    output_size_bytes,
    workflow_version,
    environment
) VALUES
    ('wf_001', 'KAMACHIQProjectWorkflow', '', 'user_demo', now64(3) - INTERVAL 6 HOUR, now64(3) - INTERVAL 5 HOUR, 3600000, 'completed', 'Create Python calculator CLI', 5, 5, 0, 0.88, true, 5, 8500, 15, 3, 4096, '1.0.0', 'production'),
    ('wf_002', 'KAMACHIQProjectWorkflow', '', 'user_demo', now64(3) - INTERVAL 3 HOUR, now64(3) - INTERVAL 2 HOUR, 3000000, 'completed', 'Build data analysis dashboard', 8, 8, 0, 0.92, true, 8, 15000, 24, 5, 12288, '1.0.0', 'production'),
    ('wf_003', 'AgentTaskWorkflow', 'wf_002', 'user_demo', now64(3) - INTERVAL 2 HOUR, now64(3) - INTERVAL 1 HOUR, 600000, 'completed', 'Task: Create charts module', 1, 1, 0, 0.90, true, 1, 2500, 3, 1, 2048, '1.0.0', 'production');

-- Verify data loaded
SELECT 'Capsule Executions:' as table_name, count() as row_count FROM capsule_executions
UNION ALL
SELECT 'Conversations:', count() FROM conversations
UNION ALL
SELECT 'Policy Decisions:', count() FROM policy_decisions
UNION ALL
SELECT 'Marketplace Transactions:', count() FROM marketplace_transactions
UNION ALL
SELECT 'Workflow Executions:', count() FROM workflow_executions;
