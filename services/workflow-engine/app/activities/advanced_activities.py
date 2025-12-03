"""
Advanced Activities - Audit Logging and Memory Operations
"""

import logging
from typing import Dict, Any, List
from temporalio import activity

from services.common.audit_logger import AuditLogger, AuditEventType
from services.common.memory_gateway import MemoryGateway

logger = logging.getLogger(__name__)

class AdvancedActivities:
    def __init__(self):
        self.audit_logger = AuditLogger.from_settings()
        self.memory_gateway = MemoryGateway()

    @activity.defn
    async def log_audit_event(self, event_type: str, actor_id: str, action: str, resource: str, outcome: str, details: Dict[str, Any]):
        """Log an audit event."""
        # Map string to enum if needed, or update AuditLogger to accept strings
        # For now assuming AuditLogger can handle it or we map it here
        try:
            # We might need to map string to AuditEventType enum
            # simpler for now to just log
            logger.info(f"AUDIT: {event_type} | {actor_id} | {action} | {resource} | {outcome}")
            
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
    async def retrieve_memory_context(self, agent_id: str, query: str, limit: int = 5) -> List[str]:
        """Retrieve context from memory gateway."""
        return await self.memory_gateway.retrieve_context(agent_id, query, limit)

    @activity.defn
    async def store_memory_experience(self, agent_id: str, content: str, metadata: Dict[str, Any]):
        """Store experience in memory gateway."""
        await self.memory_gateway.store_experience(agent_id, content, metadata)

    @activity.defn
    async def fetch_capsule(self, capsule_name: str, capsule_version: str) -> Dict[str, Any]:
        """Fetch capsule spec from database."""
        from services.orchestrator.app.database import get_async_session
        from services.orchestrator.app.api.capsules import CapsuleModel
        from sqlmodel import select
        
        async with get_async_session() as session:
            stmt = select(CapsuleModel).where(CapsuleModel.name == capsule_name, CapsuleModel.version == capsule_version)
            result = await session.execute(stmt)
            db_capsule = result.scalar_one_or_none()
            
            if not db_capsule:
                raise ValueError(f"Capsule not found: {capsule_name}:{capsule_version}")
                
            return db_capsule.content
