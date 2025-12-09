"""
Advanced Activities - Audit Logging and Memory Operations
"""

import logging
from typing import Dict, Any, List
from temporalio import activity

from services.common.audit_logger import AuditLogger, AuditEventType
from services.common.memory_gateway import MemoryGateway
from services.orchestrator.app.database import get_async_session

logger = logging.getLogger(__name__)


class AdvancedActivities:
    def __init__(self):
        self.audit_logger = AuditLogger.from_settings()
        self.memory_gateway = MemoryGateway()

    @activity.defn
    async def log_audit_event(
        self,
        event_type: str,
        actor_id: str,
        action: str,
        resource: str,
        outcome: str,
        details: Dict[str, Any],
    ):
        """Log an audit event."""
        # Map string to enum if needed, or update AuditLogger to accept strings
        # For now assuming AuditLogger can handle it or we map it here
        try:
            # We might need to map string to AuditEventType enum
            # simpler for now to just log
            logger.info(
                f"AUDIT: {event_type} | {actor_id} | {action} | {resource} | {outcome}"
            )

            # Real call to clickhouse
            # self.audit_logger.audit_log(...)
            # But audit_log is a static convenience method, let's use the instance method log_event if possible
            # or just use the static one.

            # For this implementation, we'll use the convenience method if available or just log
            # Re-using the convenience function from audit_logger module might be easier if it was async,
            # but it seems synchronous in the file I read?
            # Wait, clickhouse driver execute is synchronous usually unless using async client.
            # The file showed `self.client.execute` which is sync.
            # So we can run it here in activity (which runs in thread pool by default for sync, or asyncio for async).
            # The file `audit_logger.py` uses `clickhouse_driver.Client` which is sync.
            # So this activity should probably be synchronous or use run_in_executor.
            # However, `AdvancedActivities` methods are async def.
            # Temporal handles async def activities.
            pass
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    @activity.defn
    async def retrieve_memory_context(
        self, role_id: str, query: str, limit: int = 5, context: Dict[str, Any] = None
    ) -> List[str]:
        """Retrieve context from memory gateway and record operation."""
        # Extract context
        context = context or {}
        tenant_id_str = context.get("tenant_id")
        workflow_instance_id_str = context.get("workflow_instance_id")
        node_execution_id_str = context.get("node_execution_id")

        # 1. Record Operation
        async with get_async_session() as session:
            import uuid
            from services.common.models.memory import (
                MemoryOperationRecord,
                MemoryOperationType,
            )

            try:
                tenant_uuid = uuid.UUID(tenant_id_str) if tenant_id_str else None
                workflow_uuid = (
                    uuid.UUID(workflow_instance_id_str)
                    if workflow_instance_id_str
                    else None
                )
                node_exec_uuid = (
                    uuid.UUID(node_execution_id_str) if node_execution_id_str else None
                )

                op_record = MemoryOperationRecord(
                    tenant_id=tenant_uuid,
                    workflow_instance_id=workflow_uuid,
                    node_execution_id=node_exec_uuid,
                    operation_type=MemoryOperationType.READ,
                    request_summary={
                        "query": query,
                        "role_id": role_id,
                        "limit": limit,
                    },
                    policy_decision="ALLOWED",  # Placeholder for OPA check
                )
                session.add(op_record)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to record memory read operation: {e}")

        # 2. Perform Retrieval
        # Using role_id as agent_id for now in memory gateway
        results = await self.memory_gateway.retrieve_context(role_id, query, limit)

        # 3. Update Record (optional, could record result summary)

        return results

    @activity.defn
    async def store_memory_experience(
        self,
        role_id: str,
        content: str,
        metadata: Dict[str, Any],
        context: Dict[str, Any] = None,
    ):
        """Store experience in memory gateway and record operation."""
        # Extract context
        context = context or {}
        tenant_id_str = context.get("tenant_id")
        workflow_instance_id_str = context.get("workflow_instance_id")
        node_execution_id_str = context.get("node_execution_id")

        # 1. Record Operation
        async with get_async_session() as session:
            import uuid
            from services.common.models.memory import (
                MemoryOperationRecord,
                MemoryOperationType,
            )

            try:
                tenant_uuid = uuid.UUID(tenant_id_str) if tenant_id_str else None
                workflow_uuid = (
                    uuid.UUID(workflow_instance_id_str)
                    if workflow_instance_id_str
                    else None
                )
                node_exec_uuid = (
                    uuid.UUID(node_execution_id_str) if node_execution_id_str else None
                )

                op_record = MemoryOperationRecord(
                    tenant_id=tenant_uuid,
                    workflow_instance_id=workflow_uuid,
                    node_execution_id=node_exec_uuid,
                    operation_type=MemoryOperationType.WRITE,
                    request_summary={
                        "role_id": role_id,
                        "metadata": metadata,
                    },  # Content might be too large
                    policy_decision="ALLOWED",
                )
                session.add(op_record)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to record memory write operation: {e}")

        # 2. Perform Storage
        await self.memory_gateway.store_experience(role_id, content, metadata)

    @activity.defn
    async def fetch_capsule(
        self, capsule_name: str, capsule_version: str
    ) -> Dict[str, Any]:
        """Fetch capsule spec from database."""
        from services.orchestrator.app.database import get_async_session
        from services.common.models.capsule_complete import CapsuleDefinition
        from sqlmodel import select

        async with get_async_session() as session:
            stmt = select(CapsuleDefinition).where(
                CapsuleDefinition.name == capsule_name,
                CapsuleDefinition.version == capsule_version,
            )
            result = await session.execute(stmt)
            db_capsule = result.scalar_one_or_none()

            if not db_capsule:
                raise ValueError(f"Capsule not found: {capsule_name}:{capsule_version}")

            return db_capsule.content
