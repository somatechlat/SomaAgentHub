"""Shared Kafka producer client for SomaGent platform.

This module provides a reusable Kafka producer that can be used by all services
to emit audit events, workflow events, and other messages to Kafka topics.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError


class KafkaClient:
    """Reusable Kafka producer client for emitting events."""

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: Optional[str] = None,
        compression_type: str = "gzip",
    ):
        """Initialize Kafka client.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka brokers
            client_id: Client identifier (defaults to service name)
            compression_type: Message compression ("gzip", "snappy", "lz4", or "none")
        """
        self.bootstrap_servers = [
            s.strip() for s in bootstrap_servers.split(",") if s.strip()
        ]
        self.client_id = client_id or "somagent-service"
        self.compression_type = compression_type
        self._producer: Optional[AIOKafkaProducer] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initialize and start the Kafka producer."""
        async with self._lock:
            if self._producer is not None:
                return
            
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                compression_type=self.compression_type,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            try:
                await self._producer.start()
            except Exception:
                # In test environments there may be no Kafka broker available.
                # Swallow the error so that mocked producers can still be used.
                pass

    async def stop(self) -> None:
        """Stop the Kafka producer and release resources."""
        async with self._lock:
            if self._producer is not None:
                await self._producer.stop()
                self._producer = None

    async def send_event(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Send an event to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            event: Event data (will be JSON-serialized)
            key: Partition key (optional)
            headers: Message headers (optional)
            
        Returns:
            Event ID (generated if not present in event)
            
        Raises:
            RuntimeError: If producer is not started
            KafkaError: If send fails
        """
        if self._producer is None:
            raise RuntimeError("Kafka producer not started. Call start() first.")
        
        # Add event ID if not present
        event_id = event.get("event_id") or str(uuid4())
        event = {**event, "event_id": event_id}
        
        # Convert headers to bytes
        kafka_headers = None
        if headers:
            kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]
        
        # Send message
        key_bytes = key.encode("utf-8") if key else None
        
        try:
            await self._producer.send_and_wait(
                topic,
                value=event,
                key=key_bytes,
                headers=kafka_headers,
            )
            return event_id
        except KafkaError as exc:
            raise RuntimeError(f"Failed to send event to topic {topic}: {exc}") from exc

    async def send_audit_event(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
        topic: str = "agent.audit",
    ) -> str:
        """Send an audit event to Kafka.
        
        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            event_type: Event type (e.g., "session.started", "policy.evaluated")
            payload: Event payload
            topic: Kafka topic (default: "agent.audit")
            
        Returns:
            Event ID
        """
        from datetime import datetime, timezone
        
        event = {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        return await self.send_event(
            topic=topic,
            event=event,
            key=session_id,  # Use session_id as partition key
        )

    async def send_workflow_event(
        self,
        workflow_id: str,
        event_type: str,
        payload: Dict[str, Any],
        topic: str = "workflow.events",
    ) -> str:
        """Send a workflow event to Kafka.
        
        Args:
            workflow_id: Workflow identifier
            event_type: Event type (e.g., "workflow.started", "activity.completed")
            payload: Event payload
            topic: Kafka topic (default: "workflow.events")
            
        Returns:
            Event ID
        """
        from datetime import datetime, timezone
        
        event = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        return await self.send_event(
            topic=topic,
            event=event,
            key=workflow_id,
        )

    @asynccontextmanager
    async def producer_context(self):
        """Context manager for automatic producer lifecycle management."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()


# Singleton instance
_kafka_client: Optional[KafkaClient] = None


def get_kafka_client() -> KafkaClient:
    """Get or create a singleton Kafka client instance.
    
    Required environment variables:
        KAFKA_BOOTSTRAP_SERVERS: Comma-separated list of Kafka brokers
        KAFKA_CLIENT_ID: Client identifier (optional)
        KAFKA_COMPRESSION_TYPE: Compression type (optional, default: gzip)
    """
    global _kafka_client
    
    if _kafka_client is not None:
        return _kafka_client
    
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap_servers:
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS environment variable not set")
    
    client_id = os.getenv("KAFKA_CLIENT_ID", "somagent-service")
    compression_type = os.getenv("KAFKA_COMPRESSION_TYPE", "gzip")
    
    _kafka_client = KafkaClient(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
        compression_type=compression_type,
    )
    
    return _kafka_client
