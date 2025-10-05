"""
Integration tests for ClickHouse analytics.
Sprint-7: Test analytics data ingestion and queries.
"""

import pytest
from clickhouse_driver import Client as ClickHouseClient
from datetime import datetime, timedelta
import os


@pytest.fixture
def clickhouse_client():
    """Create ClickHouse client."""
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    
    try:
        client = ClickHouseClient(
            host=host,
            port=port,
            user=user,
            password=password,
            database="somaagent"
        )
        yield client
    except Exception:
        pytest.skip("ClickHouse not available")


class TestClickHouseSchema:
    """Test ClickHouse schema and tables."""
    
    def test_database_exists(self, clickhouse_client):
        """Test somaagent database exists."""
        result = clickhouse_client.execute("SHOW DATABASES")
        databases = [row[0] for row in result]
        assert "somaagent" in databases
    
    def test_tables_exist(self, clickhouse_client):
        """Test all required tables exist."""
        result = clickhouse_client.execute("SHOW TABLES FROM somaagent")
        tables = [row[0] for row in result]
        
        required_tables = [
            "capsule_executions",
            "conversations",
            "policy_decisions",
            "marketplace_transactions",
            "workflow_executions",
        ]
        
        for table in required_tables:
            assert table in tables, f"Table {table} not found"
    
    def test_materialized_views_exist(self, clickhouse_client):
        """Test materialized views exist."""
        result = clickhouse_client.execute("SHOW TABLES FROM somaagent")
        tables = [row[0] for row in result]
        
        expected_views = [
            "capsule_executions_hourly",
            "marketplace_revenue_daily",
            "policy_decisions_hourly",
        ]
        
        for view in expected_views:
            assert view in tables, f"View {view} not found"


class TestCapsuleExecutions:
    """Test capsule_executions table."""
    
    def test_insert_capsule_execution(self, clickhouse_client):
        """Test inserting capsule execution data."""
        
        data = {
            "execution_id": "test_exec_001",
            "capsule_id": "test_capsule",
            "capsule_version": "1.0.0",
            "user_id": "test_user",
            "session_id": "test_session",
            "duration_ms": 1000,
            "status": "completed",
            "exit_code": 0,
            "cpu_time_ms": 900,
            "memory_peak_mb": 128,
            "compute_cost_usd": 0.001,
            "revenue_usd": 0.01,
            "agent_id": "test_agent",
            "environment": "test",
            "region": "us-west-2",
        }
        
        clickhouse_client.execute(
            """
            INSERT INTO capsule_executions (
                execution_id, capsule_id, capsule_version, user_id, session_id,
                duration_ms, status, exit_code, cpu_time_ms, memory_peak_mb,
                compute_cost_usd, revenue_usd, agent_id, environment, region
            ) VALUES
            """,
            [data]
        )
        
        # Verify insertion
        result = clickhouse_client.execute(
            "SELECT COUNT(*) FROM capsule_executions WHERE execution_id = 'test_exec_001'"
        )
        assert result[0][0] >= 1
    
    def test_query_capsule_executions(self, clickhouse_client):
        """Test querying capsule executions."""
        
        result = clickhouse_client.execute(
            """
            SELECT
                capsule_id,
                count() as execution_count,
                avg(duration_ms) as avg_duration
            FROM capsule_executions
            WHERE started_at >= now() - INTERVAL 1 DAY
            GROUP BY capsule_id
            LIMIT 10
            """
        )
        
        assert isinstance(result, list)


class TestConversations:
    """Test conversations table."""
    
    def test_insert_conversation(self, clickhouse_client):
        """Test inserting conversation data."""
        
        data = {
            "conversation_id": "test_conv_001",
            "session_id": "test_session",
            "user_id": "test_user",
            "duration_seconds": 300,
            "message_count": 10,
            "turn_count": 5,
            "total_tokens": 1500,
            "model_used": "llama-3.2-1b",
            "user_satisfaction_score": 0.85,
            "coherence_score": 0.90,
            "safety_score": 0.95,
            "has_code_execution": True,
            "has_capsule_use": True,
            "capsules_used": ["test_capsule"],
            "goal_achieved": True,
            "interface": "test",
            "language": "en",
            "region": "us-west-2",
        }
        
        clickhouse_client.execute(
            """
            INSERT INTO conversations (
                conversation_id, session_id, user_id, duration_seconds,
                message_count, turn_count, total_tokens, model_used,
                user_satisfaction_score, coherence_score, safety_score,
                has_code_execution, has_capsule_use, capsules_used,
                goal_achieved, interface, language, region
            ) VALUES
            """,
            [data]
        )
        
        result = clickhouse_client.execute(
            "SELECT COUNT(*) FROM conversations WHERE conversation_id = 'test_conv_001'"
        )
        assert result[0][0] >= 1


class TestPolicyDecisions:
    """Test policy_decisions table."""
    
    def test_insert_policy_decision(self, clickhouse_client):
        """Test inserting policy decision data."""
        
        data = {
            "decision_id": "test_policy_001",
            "session_id": "test_session",
            "user_id": "test_user",
            "tenant": "test_tenant",
            "evaluation_duration_ms": 50,
            "prompt": "Test prompt",
            "prompt_hash": "test_hash",
            "role": "user",
            "allowed": True,
            "score": 0.95,
            "severity": "safe",
            "violations": [],
            "violation_count": 0,
            "constitution_hash": "const_hash",
            "constitution_version": "1.0.0",
            "rules_evaluated": 5,
            "model_used": "llama-3.2-1b",
            "environment": "test",
        }
        
        clickhouse_client.execute(
            """
            INSERT INTO policy_decisions (
                decision_id, session_id, user_id, tenant, evaluation_duration_ms,
                prompt, prompt_hash, role, allowed, score, severity,
                violations, violation_count, constitution_hash, constitution_version,
                rules_evaluated, model_used, environment
            ) VALUES
            """,
            [data]
        )
        
        result = clickhouse_client.execute(
            "SELECT COUNT(*) FROM policy_decisions WHERE decision_id = 'test_policy_001'"
        )
        assert result[0][0] >= 1


class TestAnalyticsQueries:
    """Test analytics queries."""
    
    def test_top_capsules_query(self, clickhouse_client):
        """Test top capsules by execution count query."""
        
        result = clickhouse_client.execute(
            """
            SELECT
                capsule_id,
                count() as executions,
                sum(revenue_usd) as total_revenue
            FROM capsule_executions
            WHERE started_at >= now() - INTERVAL 7 DAY
            GROUP BY capsule_id
            ORDER BY executions DESC
            LIMIT 10
            """
        )
        
        assert isinstance(result, list)
    
    def test_policy_blocking_rate(self, clickhouse_client):
        """Test policy blocking rate query."""
        
        result = clickhouse_client.execute(
            """
            SELECT
                countIf(NOT allowed) as blocked,
                count() as total,
                (blocked / total) * 100 as block_rate
            FROM policy_decisions
            WHERE evaluated_at >= now() - INTERVAL 24 HOUR
            """
        )
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert len(result[0]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
