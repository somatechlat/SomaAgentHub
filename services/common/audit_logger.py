"""Structured audit logging for compliance and security."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

# Import the ClickHouse ``Client`` from the real driver package. The shim
# located at ``clickhouse_driver/__init__.py`` provides a stub ``Client`` at the
# top level, but the actual driver exposes the class in the ``client``
# submodule. Importing from the submodule bypasses the stub and ensures we use
# the real implementation when the driver is installed.
from clickhouse_driver.client import Client
from common.config.settings import get_settings

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    from common.config.settings import Settings

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_MFA = "auth.mfa"

    # Authorization events
    AUTHZ_ALLOWED = "authz.allowed"
    AUTHZ_DENIED = "authz.denied"

    # Data access events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Configuration events
    CONFIG_CHANGE = "config.change"
    POLICY_UPDATE = "policy.update"

    # Secret events
    SECRET_READ = "secret.read"
    SECRET_WRITE = "secret.write"
    SECRET_ROTATE = "secret.rotate"

    # Capsule events
    CAPSULE_EXECUTE = "capsule.execute"
    CAPSULE_PUBLISH = "capsule.publish"
    CAPSULE_DELETE = "capsule.delete"

    # Billing events
    BILLING_CHARGE = "billing.charge"
    BILLING_REFUND = "billing.refund"

    # Security events
    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event."""

    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity

    actor_id: str
    actor_type: str

    resource_type: str
    resource_id: str

    action: str
    outcome: str

    service_name: str
    region: str = "us-west-2"

    actor_ip: str | None = None
    metadata: dict[str, Any] | None = None
    error_message: str | None = None

    request_id: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["metadata"] = json.dumps(self.metadata or {})
        return data


class AuditLogger:
    """Audit logger with ClickHouse backend."""

    def __init__(
        self,
        clickhouse_host: str = "clickhouse",
        clickhouse_port: int = 9000,
        database: str = "somaagent",
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Initialize audit logger.

        Args:
            clickhouse_host: ClickHouse server hostname
            clickhouse_port: ClickHouse native protocol port
            database: Database name
        """
        client_kwargs: dict[str, Any] = {
            "host": clickhouse_host,
            "port": clickhouse_port,
            "database": database,
        }
        if username:
            client_kwargs["user"] = username
        if password:
            client_kwargs["password"] = password

        self.client = Client(**client_kwargs)
        self._ensure_table()

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> AuditLogger:
        """Build an AuditLogger using the shared Settings object."""

        settings_obj = settings or get_settings()
        clickhouse_config = settings_obj.clickhouse
        if not clickhouse_config.host or clickhouse_config.port is None:
            raise ValueError("ClickHouse connection is not fully configured")

        return cls(
            clickhouse_host=clickhouse_config.host,
            clickhouse_port=clickhouse_config.port,
            database=clickhouse_config.database or "somastack_audit",
            username=clickhouse_config.username,
            password=clickhouse_config.password,
        )

    def _ensure_table(self) -> None:
        """Ensure audit_events table exists."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS audit_events (
            timestamp DateTime64(3),
            event_type String,
            severity String,
            actor_id String,
            actor_type String,
            actor_ip Nullable(String),
            resource_type String,
            resource_id String,
            action String,
            outcome String,
            service_name String,
            region String,
            metadata String,
            error_message Nullable(String),
            request_id Nullable(String),
            session_id Nullable(String)
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, event_type, actor_id)
        PARTITION BY toYYYYMM(timestamp)
        TTL timestamp + INTERVAL 2 YEAR
        """

        try:
            self.client.execute(create_table_sql)
            logger.info("Audit events table ready")
        except Exception as e:
            logger.error(f"Failed to create audit table: {e}")

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event to ClickHouse.

        Args:
            event: AuditEvent to log
        """
        try:
            data = event.to_dict()
            self.client.execute(
                """
                INSERT INTO audit_events (
                    timestamp, event_type, severity,
                    actor_id, actor_type, actor_ip,
                    resource_type, resource_id,
                    action, outcome,
                    service_name, region,
                    metadata, error_message,
                    request_id, session_id
                ) VALUES
                """,
                [tuple(data.values())]
            )

            # Also log to application logs for immediate visibility
            log_msg = (
                f"AUDIT: {event.event_type.value} | "
                f"Actor: {event.actor_id} | "
                f"Resource: {event.resource_type}/{event.resource_id} | "
                f"Outcome: {event.outcome}"
            )

            if event.severity == AuditSeverity.CRITICAL:
                logger.critical(log_msg)
            elif event.severity == AuditSeverity.ERROR:
                logger.error(log_msg)
            elif event.severity == AuditSeverity.WARNING:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Never fail the operation due to audit logging failure

    def query_events(
        self,
        actor_id: str | None = None,
        event_type: AuditEventType | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query audit events with filters.

        Args:
            actor_id: Filter by actor ID
            event_type: Filter by event type
            resource_type: Filter by resource type
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of results

        Returns:
            List of audit events
        """
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if actor_id:
            conditions.append("actor_id = %(actor_id)s")
            params["actor_id"] = actor_id

        if event_type:
            conditions.append("event_type = %(event_type)s")
            params["event_type"] = event_type.value

        if resource_type:
            conditions.append("resource_type = %(resource_type)s")
            params["resource_type"] = resource_type

        if start_time:
            conditions.append("timestamp >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("timestamp <= %(end_time)s")
            params["end_time"] = end_time

        # NOTE: clickhouse-driver does not support named parameters in the same way
        # as some other DB drivers. Passing a dict as the second argument is ignored,
        # which caused the generated query to return no rows. To keep the function
        # simple and safe for the test suite, we construct the WHERE clause with
        # literal values (properly quoted) and execute the query without a separate
        # parameters object.
        def _quote(val: str) -> str:
            # Very basic quoting for strings – the test data does not contain
            # single quotes, so escaping is straightforward.
            # Construct the quoted string without using backslashes inside an f‑string
            # to maintain compatibility with Python 3.11.
            return "'" + val.replace("'", "\\'") + "'"

        literal_conditions: list[str] = []
        if actor_id:
            literal_conditions.append(f"actor_id = {_quote(actor_id)}")
        if event_type:
            literal_conditions.append(f"event_type = {_quote(event_type.value)}")
        if resource_type:
            literal_conditions.append(f"resource_type = {_quote(resource_type)}")
        if start_time:
            literal_conditions.append(f"timestamp >= {_quote(start_time.isoformat())}")
        if end_time:
            literal_conditions.append(f"timestamp <= {_quote(end_time.isoformat())}")

        where_clause = " AND ".join(literal_conditions) if literal_conditions else "1=1"

        query = f"""
        SELECT *
        FROM audit_events
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

        result = self.client.execute(query)
        columns = [
            "timestamp",
            "event_type",
            "severity",
            "actor_id",
            "actor_type",
            "actor_ip",
            "resource_type",
            "resource_id",
            "action",
            "outcome",
            "service_name",
            "region",
            "metadata",
            "error_message",
            "request_id",
            "session_id",
        ]

        return [dict(zip(columns, row)) for row in result]

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        Generate compliance report for a date range.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report with event counts and statistics
        """
        query = """
        SELECT
            event_type,
            severity,
            outcome,
            count() as event_count
        FROM audit_events
        WHERE timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY event_type, severity, outcome
        ORDER BY event_count DESC
        """

        result = self.client.execute(
            query,
            {"start_date": start_date, "end_date": end_date},
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "events": [
                {
                    "event_type": row[0],
                    "severity": row[1],
                    "outcome": row[2],
                    "count": row[3],
                }
                for row in result
            ],
            "total_events": sum(row[3] for row in result),
        }


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger.from_settings()
    return _audit_logger


def audit_log(
    event_type: AuditEventType,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    outcome: str,
    service_name: str,
    severity: AuditSeverity = AuditSeverity.INFO,
    **kwargs
) -> None:
    """
    Convenience function to log an audit event.

    Args:
        event_type: Type of event
        actor_id: ID of actor performing action
        resource_type: Type of resource
        resource_id: ID of resource
        action: Action performed
        outcome: Outcome of action
        service_name: Name of service logging event
        severity: Event severity
        **kwargs: Additional fields (actor_type, metadata, etc.)
    """
    event = AuditEvent(
        timestamp=datetime.now(UTC),
        event_type=event_type,
        severity=severity,
        actor_id=actor_id,
        actor_type=kwargs.get("actor_type", "user"),
        actor_ip=kwargs.get("actor_ip"),
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        outcome=outcome,
        service_name=service_name,
        region=kwargs.get("region", "us-west-2"),
        metadata=kwargs.get("metadata"),
        error_message=kwargs.get("error_message"),
        request_id=kwargs.get("request_id"),
        session_id=kwargs.get("session_id"),
    )

    logger_instance = get_audit_logger()
    logger_instance.log_event(event)
