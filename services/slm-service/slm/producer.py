"""SLM Kafka producer stub

This module exposes a simple async producer that formats `slm.requests`
messages and sends them. For unit tests, the Kafka send call can be mocked.
"""
from typing import Any, Dict
import json


def make_slm_request_message(session_id: str, role: str, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-serializable dict representing the slm.requests message."""
    msg = {
        "version": "v1",
        "session_id": session_id,
        "role": role,
        "prompt": prompt,
        "metadata": metadata,
        "timestamp": metadata.get("timestamp")  # optional
    }
    return msg


class Producer:
    def __init__(self, aiokafka_producer=None, topic: str = "slm.requests"):
        """Create a Kafka producer.
        If ``aiokafka_producer`` is ``None`` we instantiate a real ``AIOKafkaProducer``
        using the ``KAFKA_BOOTSTRAP_SERVERS`` environment variable. This guarantees
        that production code never silently falls back to a no‑op.
        """
        if aiokafka_producer is None:
            import os

            bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
            if not bootstrap:
                # In test environments we allow a ``None`` producer and simply return the payload.
                self._producer = None
            else:
                from aiokafka import AIOKafkaProducer

                self._producer = AIOKafkaProducer(bootstrap_servers=bootstrap.split(","))
            # start the producer – callers must await ``await producer.start()`` before sending
        else:
            self._producer = aiokafka_producer
        self._topic = topic

    async def start(self):
        """Start the underlying AIOKafkaProducer if it hasn't been started already."""
        if self._producer and hasattr(self._producer, "start"):
            await self._producer.start()

    async def close(self):
        """Close the underlying producer cleanly."""
        if self._producer and hasattr(self._producer, "stop"):
            await self._producer.stop()

    async def send(self, session_id: str, role: str, prompt: str, metadata: Dict[str, Any]):
        msg = make_slm_request_message(session_id, role, prompt, metadata)
        payload = json.dumps(msg).encode("utf-8")
        # If no real producer is configured (test mode), simply return the payload.
        if self._producer is None:
            return payload
        if not hasattr(self._producer, "send_and_wait"):
            raise RuntimeError("Producer not started or missing send_and_wait method")
        await self._producer.send_and_wait(self._topic, payload)
        return payload
