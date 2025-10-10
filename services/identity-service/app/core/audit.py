"""Identity service audit logging backed by the shared ClickHouse pipeline."""

from __future__ import annotations

from datetime import datetime
import asyncio
from typing import Any

from services.common.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditLogger as SharedAuditLogger,
    AuditSeverity,
)
from .config import IdentitySettings


class AuditLogger:
    """Asynchronous wrapper over the shared ClickHouse-backed audit logger."""

    def __init__(self, settings: IdentitySettings) -> None:
        clickhouse = settings.clickhouse
        if not clickhouse.host or clickhouse.port is None:
            raise ValueError("ClickHouse host and port must be configured for audit logging")

        self._logger = SharedAuditLogger(
            clickhouse_host=clickhouse.host,
            clickhouse_port=clickhouse.port,
            database=clickhouse.database or "somastack_audit",
            username=clickhouse.username,
            password=clickhouse.password,
        )
        self._service_name = settings.service_name
        self._region = settings.environment

    async def start(self) -> None:
        await asyncio.to_thread(self._logger.client.execute, "SELECT 1")

    async def stop(self) -> None:
        await asyncio.to_thread(self._logger.client.disconnect)

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        await asyncio.to_thread(self._emit_sync, event_type, payload)

    def _emit_sync(self, event_type: str, payload: dict[str, Any]) -> None:
        audit_type, action, severity = self._map_event(event_type)
        actor_id = str(payload.get("user_id") or payload.get("actor_id") or "unknown")
        actor_type = payload.get("actor_type", "user")
        resource_id = str(payload.get("jti") or payload.get("resource_id") or "unknown")
        resource_type = payload.get("resource_type", "token")

        metadata = dict(payload)
        metadata.setdefault("event", event_type)

        event = AuditEvent(
            timestamp=datetime.now(datetime.UTC),
            event_type=audit_type,
            severity=severity,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=metadata.get("actor_ip"),
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=metadata.get("outcome", "success"),
            service_name=self._service_name,
            region=metadata.get("region", self._region),
            metadata=metadata,
            error_message=metadata.get("error_message"),
            request_id=metadata.get("request_id"),
            session_id=metadata.get("session_id"),
        )
        self._logger.log_event(event)

    @staticmethod
    def _map_event(event_type: str) -> tuple[AuditEventType, str, AuditSeverity]:
        if event_type == "token.issued":
            return AuditEventType.AUTH_LOGIN, "issue", AuditSeverity.INFO
        if event_type == "token.revoked":
            return AuditEventType.AUTH_LOGOUT, "revoke", AuditSeverity.INFO
        return AuditEventType.SECURITY_ALERT, event_type.replace("token.", ""), AuditSeverity.WARNING
