"""Integration tests for security components (SPIFFE, Vault, Audit)."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime

import pytest

# Skip the integration tests if Docker daemon is not available in the environment.
try:
    import docker  # type: ignore
    _docker_client = docker.from_env()
    _docker_client.ping()
except Exception:
    pytest.skip(
        "Docker daemon not available; skipping integration tests.",
        allow_module_level=True,
    )
import requests
from testcontainers.clickhouse import ClickHouseContainer
from testcontainers.core.container import DockerContainer

from common.config.settings import get_settings
from services.common import audit_logger as audit_logger_module
from services.common import spiffe_auth as spiffe_module
from services.common.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    audit_log,
)
from services.common.spiffe_auth import SPIFFEAuthenticator, init_spiffe
from services.common.vault_client import VaultClient


@pytest.fixture(scope="session")
def clickhouse_container():
    container = ClickHouseContainer()
    container.start()

    host = container.get_container_host_ip()
    native_port = container.get_exposed_port("9000/tcp")

    os.environ["SOMASTACK_CLICKHOUSE_HOST"] = host
    os.environ["SOMASTACK_CLICKHOUSE_PORT"] = str(native_port)
    # Use the default "test" database and credentials provided by the ClickHouse test container.
    os.environ["SOMASTACK_CLICKHOUSE_DATABASE"] = "test"
    os.environ["SOMASTACK_CLICKHOUSE_USERNAME"] = "test"
    os.environ["SOMASTACK_CLICKHOUSE_PASSWORD"] = "test"

    # The default "test" database already exists; no additional setup required.

    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def vault_container():
    container = (
        DockerContainer("hashicorp/vault:1.15.4")
        .with_command(
            "server -dev -dev-root-token-id=root -dev-listen-address=0.0.0.0:8200"
        )
        .with_env("VAULT_DEV_ROOT_TOKEN_ID", "root")
        .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
        .with_env("VAULT_LOG_LEVEL", "info")
        .with_exposed_ports("8200/tcp")
    )
    container.start()

    host = container.get_container_host_ip()
    port = container.get_exposed_port("8200/tcp")
    addr = f"http://{host}:{port}"

    os.environ["VAULT_ADDR"] = addr
    os.environ["VAULT_TOKEN"] = "root"
    os.environ["VAULT_NAMESPACE"] = ""

    session = requests.Session()
    for _ in range(60):
        try:
            response = session.get(f"{addr}/v1/sys/health", timeout=2)
            if response.status_code < 500:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    else:
        container.stop()
        raise RuntimeError("Vault container failed to start")

    try:
        session.post(
            f"{addr}/v1/sys/mounts/secret",
            headers={"X-Vault-Token": "root"},
            json={"type": "kv", "options": {"version": "2"}},
            timeout=2,
        )
    except requests.exceptions.RequestException:
        pass

    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(autouse=True)
def configure_test_environment(tmp_path, clickhouse_container):
    cert_dir = tmp_path / "spiffe"
    cert_dir.mkdir()

    for filename in ("svid.pem", "svid_key.pem", "bundle.pem"):
        (cert_dir / filename).write_text("test-cert-data")

    os.environ["SPIFFE_CERT_DIR"] = str(cert_dir)
    os.environ["SOMA_USE_CLICKHOUSE"] = "1"

    audit_logger_module._audit_logger = None
    spiffe_module._authenticator = None
    get_settings.cache_clear()

    yield

    spiffe_module._authenticator = None
    audit_logger_module._audit_logger = None


@pytest.fixture
def audit_logger(clickhouse_container):
    get_settings.cache_clear()
    logger = AuditLogger.from_settings()
    # Truncate the audit_events table in the test database (the same database used by the logger).
    logger.client.execute("TRUNCATE TABLE IF EXISTS audit_events")
    return logger


@pytest.fixture
def vault_client(vault_container):
    client = VaultClient(
        vault_addr=os.environ["VAULT_ADDR"],
        vault_namespace=os.getenv("VAULT_NAMESPACE", ""),
    )
    client.client.token = os.environ["VAULT_TOKEN"]
    client._authenticated = True
    return client


class TestSPIFFEAuth:
    """Basic SPIFFE authenticator coverage."""

    def test_fetch_identity(self):
        auth = SPIFFEAuthenticator()
        identity = auth.fetch_identity("test-service")

        assert identity.service_name == "test-service"
        assert identity.spiffe_id.startswith("spiffe://")
        assert identity.trust_domain == os.getenv("SPIFFE_TRUST_DOMAIN", "somaagent.io")

    def test_verify_peer_same_trust_domain(self):
        auth = SPIFFEAuthenticator()
        auth.fetch_identity("service-a")

        assert auth.verify_peer("spiffe://somaagent.io/service/service-b")
        assert not auth.verify_peer("spiffe://other.io/service/service-c")

    def test_init_spiffe_helper(self):
        identity = init_spiffe("my-service")
        assert identity.service_name == "my-service"


class TestVaultClient:
    """Exercise Vault CRUD paths with dev server."""

    def test_read_write_secret(self, vault_client):
        payload = {"username": "test_user", "password": "test_pass_123"}

        version = vault_client.write_secret("test/credentials", payload)
        assert version >= 1

        secret = vault_client.read_secret("test/credentials")
        assert secret.data["username"] == "test_user"
        assert secret.data["password"] == "test_pass_123"
        assert secret.version == version

    def test_delete_secret(self, vault_client):
        vault_client.write_secret("test/temp", {"key": "value"})
        vault_client.delete_secret("test/temp")

        with pytest.raises(Exception):
            vault_client.read_secret("test/temp")


class TestAuditLogger:
    """Validate ClickHouse-backed audit logging."""

    def test_log_auth_event(self, audit_logger):
        event = AuditEvent(
            timestamp=datetime.now(UTC),
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
            metadata={"user_agent": "Mozilla/5.0"},
        )

        audit_logger.log_event(event)

    def test_log_data_access_event(self, audit_logger):
        event = AuditEvent(
            timestamp=datetime.now(UTC),
            event_type=AuditEventType.DATA_READ,
            severity=AuditSeverity.INFO,
            actor_id="service_orchestrator",
            actor_type="service",
            resource_type="capsule",
            resource_id="cap_xyz789",
            action="read",
            outcome="success",
            service_name="orchestrator",
        )

        audit_logger.log_event(event)

    def test_log_security_violation(self, audit_logger):
        event = AuditEvent(
            timestamp=datetime.now(UTC),
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
            error_message="Insufficient permissions",
        )

        audit_logger.log_event(event)

    def test_query_events(self, audit_logger):
        for index in range(3):
            audit_logger.log_event(
                AuditEvent(
                    timestamp=datetime.now(UTC),
                    event_type=AuditEventType.DATA_READ,
                    severity=AuditSeverity.INFO,
                    actor_id=f"user{index}",
                    actor_type="user",
                    resource_type="capsule",
                    resource_id=f"cap_{index}",
                    action="read",
                    outcome="success",
                    service_name="orchestrator",
                )
            )

        events = audit_logger.query_events(
            event_type=AuditEventType.DATA_READ,
            limit=10,
        )

        assert len(events) >= 3
        assert all(item["event_type"] == "data.read" for item in events)

    def test_compliance_report(self, audit_logger):
        audit_logger.log_event(
            AuditEvent(
                timestamp=datetime.now(UTC),
                event_type=AuditEventType.CONFIG_CHANGE,
                severity=AuditSeverity.INFO,
                actor_id="admin",
                actor_type="user",
                resource_type="settings",
                resource_id="global",
                action="update",
                outcome="success",
                service_name="settings-service",
            )
        )

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 12, 31, tzinfo=UTC)

        report = audit_logger.generate_compliance_report(start_date, end_date)

        assert "period" in report
        assert "events" in report
        assert "total_events" in report
        assert report["period"]["start"] == start_date.isoformat()

    def test_audit_log_helper(self):
        audit_log(
            event_type=AuditEventType.CONFIG_CHANGE,
            actor_id="admin1",
            resource_type="configuration",
            resource_id="config_main",
            action="update",
            outcome="success",
            service_name="settings-service",
            actor_type="user",
            metadata={"changed_fields": ["timeout"]},
        )


class TestSecurityIntegration:
    """Cross-cutting integration scenarios."""

    def test_secure_service_startup(self):
        identity = init_spiffe("integration-test-service")
        assert identity is not None

        audit_log(
            event_type=AuditEventType.CONFIG_CHANGE,
            actor_id="integration-test-service",
            resource_type="service",
            resource_id="integration-test-service",
            action="startup",
            outcome="success",
            service_name="integration-test-service",
            actor_type="service",
            metadata={"spiffe_id": identity.spiffe_id},
        )

    def test_secret_access_audit_trail(self, audit_logger):
        service_name = "test-service"

        audit_logger.log_event(
            AuditEvent(
                timestamp=datetime.now(UTC),
                event_type=AuditEventType.SECRET_READ,
                severity=AuditSeverity.INFO,
                actor_id=service_name,
                actor_type="service",
                resource_type="secret",
                resource_id="database/credentials",
                action="read",
                outcome="success",
                service_name=service_name,
            )
        )

        events = audit_logger.query_events(
            actor_id=service_name,
            event_type=AuditEventType.SECRET_READ,
            limit=1,
        )

        assert len(events) >= 1
        assert events[0]["resource_id"] == "database/credentials"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
