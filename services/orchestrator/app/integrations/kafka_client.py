"""
Production Kafka client configuration with security and resiliency.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from prometheus_client import Counter, Histogram

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# Kafka metrics
kafka_messages_sent = Counter("kafka_messages_sent_total", "Total Kafka messages sent", ["topic", "status"])
kafka_send_duration = Histogram("kafka_send_duration_seconds", "Time to send Kafka messages", ["topic"])
kafka_messages_received = Counter(
    "kafka_messages_received_total",
    "Total Kafka messages received",
    ["topic", "consumer_group"],
)


class KafkaClientConfig:
    """Production Kafka client configuration."""

    def __init__(self):
        self.settings = get_settings()
        self.bootstrap_servers = self.settings.kafka_bootstrap_servers or "localhost:9092"
        self.client_id = self.settings.kafka_client_id
        self.security_protocol = self.settings.kafka_security_protocol
        self.sasl_mechanism = self.settings.kafka_sasl_mechanism
        self.sasl_username = self.settings.kafka_sasl_username
        self.sasl_password = self.settings.kafka_sasl_password
        self.ssl_cafile = self.settings.kafka_ssl_cafile
        self.ssl_certfile = self.settings.kafka_ssl_certfile
        self.ssl_keyfile = self.settings.kafka_ssl_keyfile
        self.linger_ms = self.settings.kafka_producer_linger_ms
        self.batch_size = self.settings.kafka_producer_batch_size

    def get_producer_config(self) -> dict[str, Any]:
        """Get producer configuration with security."""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": f"{self.client_id}-producer",
            "value_serializer": lambda v: (v.encode() if isinstance(v, str) else str(v).encode()),
            "key_serializer": lambda k: k.encode() if k else None,
            "acks": "all",  # Wait for all replicas
            "retries": 3,
            "max_in_flight_requests_per_connection": 1,
            "compression_type": "gzip",
            "linger_ms": self.linger_ms,
            "batch_size": self.batch_size,
        }

        # Add security configuration
        if self.security_protocol != "PLAINTEXT":
            config["security_protocol"] = self.security_protocol

            if self.sasl_mechanism:
                config["sasl_mechanism"] = self.sasl_mechanism
                config["sasl_plain_username"] = self.sasl_username
                config["sasl_plain_password"] = self.sasl_password

            if self.ssl_cafile:
                config["ssl_cafile"] = self.ssl_cafile

            if self.ssl_certfile and self.ssl_keyfile:
                config["ssl_certfile"] = self.ssl_certfile
                config["ssl_keyfile"] = self.ssl_keyfile

        return config

    def get_consumer_config(self, consumer_group: str) -> dict[str, Any]:
        """Get consumer configuration with security."""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": f"{self.client_id}-consumer",
            "group_id": consumer_group,
            "value_deserializer": lambda v: v.decode(),
            "key_deserializer": lambda k: k.decode() if k else None,
            "enable_auto_commit": False,  # Manual commit for reliability
            "max_poll_records": 100,
            "session_timeout_ms": 30000,
        }

        # Add security configuration
        if self.security_protocol != "PLAINTEXT":
            config["security_protocol"] = self.security_protocol

            if self.sasl_mechanism:
                config["sasl_mechanism"] = self.sasl_mechanism
                config["sasl_plain_username"] = self.sasl_username
                config["sasl_plain_password"] = self.sasl_password

            if self.ssl_cafile:
                config["ssl_cafile"] = self.ssl_cafile

            if self.ssl_certfile and self.ssl_keyfile:
                config["ssl_certfile"] = self.ssl_certfile
                config["ssl_keyfile"] = self.ssl_keyfile

        return config


class KafkaProducer:
    """Production-ready Kafka producer with metrics and error handling."""

    def __init__(self, topic_prefix: str = "orchestration"):
        self.config = KafkaClientConfig()
        self.topic_prefix = topic_prefix
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        producer_config = self.config.get_producer_config()
        self._producer = AIOKafkaProducer(**producer_config)
        await self._producer.start()
        logger.info(
            f"Kafka producer started. Bootstrap: {self.config.bootstrap_servers}, "
            f"Security: {self.config.security_protocol}"
        )

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
        logger.info("Kafka producer stopped")

    async def send_event(
        self,
        topic: str,
        message: dict[str, Any],
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Send event to Kafka with metrics and error handling."""
        full_topic = f"{self.topic_prefix}.{topic}"

        try:
            with kafka_send_duration.labels(topic=full_topic).time():
                await self._producer.send(
                    full_topic,
                    value=json.dumps(message),
                    key=key,
                    headers=[(k, v.encode()) for k, v in (headers or {}).items()],
                )

            kafka_messages_sent.labels(topic=full_topic, status="success").inc()
            logger.debug(f"Sent message to topic {full_topic}")

        except KafkaError as e:
            kafka_messages_sent.labels(topic=full_topic, status="error").inc()
            logger.error(f"Failed to send message to {full_topic}: {e}")
            raise

    async def flush(self) -> None:
        """Flush producer buffer."""
        if self._producer:
            await self._producer.flush()


class KafkaConsumer:
    """Production-ready Kafka consumer with metrics and error handling."""

    def __init__(self, consumer_group: str, topic_prefix: str = "orchestration"):
        self.config = KafkaClientConfig()
        self.consumer_group = consumer_group
        self.topic_prefix = topic_prefix
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self, topics: list[str]) -> None:
        """Start the Kafka consumer."""
        full_topics = [f"{self.topic_prefix}.{topic}" for topic in topics]
        consumer_config = self.config.get_consumer_config(self.consumer_group)

        self._consumer = AIOKafkaConsumer(*full_topics, **consumer_config)
        await self._consumer.start()

        logger.info(
            f"Kafka consumer started. Topics: {full_topics}, "
            f"Group: {self.consumer_group}, Security: {self.config.security_protocol}"
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self._consumer:
            await self._consumer.stop()
        logger.info("Kafka consumer stopped")

    async def consume(self, callback):
        """Consume messages with error handling."""
        try:
            async for msg in self._consumer:
                try:
                    data = json.loads(msg.value)
                    kafka_messages_received.labels(topic=msg.topic, consumer_group=self.consumer_group).inc()

                    await callback(data, msg)

                    # Manual commit after successful processing
                    await self._consumer.commit()

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Don't commit - message will be retried

        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            raise


async def create_kafka_producer() -> KafkaProducer:
    """Factory function to create a configured Kafka producer."""
    producer = KafkaProducer()
    await producer.start()
    return producer


async def create_kafka_consumer(consumer_group: str) -> KafkaConsumer:
    """Factory function to create a configured Kafka consumer."""
    consumer = KafkaConsumer(consumer_group)
    return consumer
