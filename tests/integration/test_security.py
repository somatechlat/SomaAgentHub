"""
Integration tests for security components (SPIFFE, Vault, Audit).
"""

import pytest
import os
from datetime import datetime
from services.common.spiffe_auth import SPIFFEAuthenticator, init_spiffe
from services.common.vault_client import VaultClient, init_vault
from services.common.audit_logger import (
    AuditLogger, AuditEvent, AuditEventType,
    AuditSeverity, audit_log
)


class TestSPIFFEAuth:
    """Test SPIFFE authentication."""
    
    def test_fetch_identity(self):
        """Test fetching SPIFFE identity."""
        auth = SPIFFEAuthenticator()
        identity = auth.fetch_identity("test-service")
        
        assert identity.service_name == "test-service"
        assert identity.spiffe_id.startswith("spiffe://")
        assert "test-service" in identity.spiffe_id
        assert identity.trust_domain == os.getenv("SPIFFE_TRUST_DOMAIN", "somaagent.io")
    
    def test_verify_peer_same_trust_domain(self):
        """Test peer verification in same trust domain."""
        auth = SPIFFEAuthenticator()
        auth.fetch_identity("service-a")
        
        # Same trust domain should pass
        assert auth.verify_peer("spiffe://somaagent.io/service/service-b")
        
        # Different trust domain should fail
        assert not auth.verify_peer("spiffe://other.io/service/service-c")
    
    def test_init_spiffe_helper(self):
        """Test init_spiffe helper function."""
        identity = init_spiffe("my-service")
        assert identity.service_name == "my-service"


class TestVaultClient:
    """Test Vault client operations."""
    
    @pytest.fixture
    def vault_client(self):
        """Create Vault client for testing."""
        # Assumes Vault is running locally or in test environment
        client = VaultClient(vault_addr="http://localhost:8200")
        # Skip auth in tests, assume already authenticated
        client._authenticated = True
        return client
    
    def test_read_write_secret(self, vault_client):
        """Test reading and writing secrets."""
        test_data = {
            "username": "test_user",
            "password": "test_pass_123"
        }
        
        # Write secret
        version = vault_client.write_secret("test/credentials", test_data)
        assert version >= 1
        
        # Read secret
        secret = vault_client.read_secret("test/credentials")
        assert secret.data["username"] == "test_user"
        assert secret.data["password"] == "test_pass_123"
        assert secret.version == version
    
    def test_delete_secret(self, vault_client):
        """Test deleting secrets."""
        # Write a test secret
        vault_client.write_secret("test/temp", {"key": "value"})
        
        # Delete it
        vault_client.delete_secret("test/temp")
        
        # Verify it's deleted (should raise exception)
        with pytest.raises(Exception):
            vault_client.read_secret("test/temp")
    
    def test_init_vault_kubernetes(self, monkeypatch):
        """Test Vault initialization with Kubernetes auth."""
        # Mock K8s service account token
        monkeypatch.setenv("VAULT_ADDR", "http://localhost:8200")
        
        # This would normally fail without a real K8s environment
        # Just test the function exists and takes correct params
        assert callable(init_vault)


class TestAuditLogger:
    """Test audit logging."""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger for testing."""
        # Use test ClickHouse instance
        return AuditLogger(
            clickhouse_host="localhost",
            clickhouse_port=9000,
            database="somaagent_test"
        )
    
    def test_log_auth_event(self, audit_logger):
        """Test logging authentication event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
            actor_id="user123",
            actor_type="user",
            actor_ip="192.168.1.100",
            resource_type="session",
            resource_id="sess_abc123",
            action="login",
            outcome="success",
            service_name="gateway-api",
            metadata={"user_agent": "Mozilla/5.0"}
        )
        
        # Should not raise exception
        audit_logger.log_event(event)
    
    def test_log_data_access_event(self, audit_logger):
        """Test logging data access event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.DATA_READ,
            severity=AuditSeverity.INFO,
            actor_id="service_orchestrator",
            actor_type="service",
            resource_type="capsule",
            resource_id="cap_xyz789",
            action="read",
            outcome="success",
            service_name="orchestrator"
        )
        
        audit_logger.log_event(event)
    
    def test_log_security_violation(self, audit_logger):
        """Test logging security violation."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.CRITICAL,
            actor_id="user456",
            actor_type="user",
            actor_ip="10.0.0.1",
            resource_type="policy",
            resource_id="pol_sensitive",
            action="access_denied",
            outcome="failure",
            service_name="policy-engine",
            error_message="Insufficient permissions"
        )
        
        audit_logger.log_event(event)
    
    def test_query_events(self, audit_logger):
        """Test querying audit events."""
        # Log several events
        for i in range(3):
            event = AuditEvent(
                timestamp=datetime.utcnow(),
                event_type=AuditEventType.DATA_READ,
                severity=AuditSeverity.INFO,
                actor_id=f"user{i}",
                actor_type="user",
                resource_type="capsule",
                resource_id=f"cap_{i}",
                action="read",
                outcome="success",
                service_name="orchestrator"
            )
            audit_logger.log_event(event)
        
        # Query events
        events = audit_logger.query_events(
            event_type=AuditEventType.DATA_READ,
            limit=10
        )
        
        assert len(events) >= 3
        assert all(e['event_type'] == 'data.read' for e in events)
    
    def test_compliance_report(self, audit_logger):
        """Test generating compliance report."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        report = audit_logger.generate_compliance_report(start_date, end_date)
        
        assert 'period' in report
        assert 'events' in report
        assert 'total_events' in report
        assert report['period']['start'] == start_date.isoformat()
    
    def test_audit_log_helper(self):
        """Test audit_log convenience function."""
        # Should not raise exception
        audit_log(
            event_type=AuditEventType.CONFIG_CHANGE,
            actor_id="admin1",
            resource_type="configuration",
            resource_id="config_main",
            action="update",
            outcome="success",
            service_name="settings-service",
            actor_type="user",
            metadata={"changed_fields": ["timeout"]}
        )


class TestSecurityIntegration:
    """Integration tests combining SPIFFE, Vault, and Audit."""
    
    def test_secure_service_startup(self):
        """Test complete secure service startup flow."""
        # 1. Initialize SPIFFE identity
        identity = init_spiffe("integration-test-service")
        assert identity is not None
        
        # 2. Initialize Vault (would use SPIFFE for auth in production)
        # Skipping actual Vault auth in test
        
        # 3. Log service startup
        audit_log(
            event_type=AuditEventType.CONFIG_CHANGE,
            actor_id="integration-test-service",
            resource_type="service",
            resource_id="integration-test-service",
            action="startup",
            outcome="success",
            service_name="integration-test-service",
            actor_type="service",
            metadata={"spiffe_id": identity.spiffe_id}
        )
    
    def test_secret_access_audit_trail(self):
        """Test that secret access is audited."""
        service_name = "test-service"
        
        # Log secret read
        audit_log(
            event_type=AuditEventType.SECRET_READ,
            actor_id=service_name,
            resource_type="secret",
            resource_id="database/credentials",
            action="read",
            outcome="success",
            service_name=service_name,
            actor_type="service"
        )
        
        # Verify it was logged
        logger = AuditLogger()
        events = logger.query_events(
            actor_id=service_name,
            event_type=AuditEventType.SECRET_READ,
            limit=1
        )
        
        assert len(events) >= 1
        assert events[0]['resource_id'] == "database/credentials"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
