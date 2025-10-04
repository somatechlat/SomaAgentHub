"""Async worker for consuming ``slm.requests`` and emitting ``slm.responses``."""
import json
import os
from typing import Any, Dict

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .local_models import get_text_generator


def process_request_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Process a request using the deterministic Markov generator."""

    prompt = msg.get("prompt", "")
    session_id = msg.get("session_id")
    role = msg.get("role")

    generator = get_text_generator()
    result = generator.generate(prompt, max_tokens=64, temperature=0.8)

    response = {
        "version": "v1",
        "session_id": session_id,
        "role": role,
        "result": result.text.strip(),
        "metrics": {
            "model": "somasuite-markov-v1",
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
        },
    }
    return response


async def consume_and_process(get_message_callable, publish_callable):
    """Consume messages via get_message_callable() until it returns None.

    get_message_callable should be an async callable returning bytes or None.
    publish_callable should accept (topic, bytes) and return when published.
    """
    while True:
        raw = await get_message_callable()
        if raw is None:
            break
        msg = json.loads(raw.decode("utf-8"))
        resp = process_request_message(msg)
        payload = json.dumps(resp).encode("utf-8")
        await publish_callable("slm.responses", payload)


async def run_worker():
    """Start the async Kafka worker.

    Consumes messages from the ``slm.requests`` topic, processes them via
    ``process_request_message`` and publishes the response to ``slm.responses``.
    The Kafka bootstrap servers are taken from the ``KAFKA_BOOTSTRAP_SERVERS``
    environment variable (comma‑separated list). The worker runs until cancelled.
    """
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap:
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS env var required for worker")

    consumer = AIOKafkaConsumer(
        "slm.requests",
        bootstrap_servers=bootstrap.split(","),
        group_id="slm_worker_group",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap.split(","))

    # Start both consumer and producer
    await consumer.start()
    await producer.start()
    try:
        async for raw in consumer:
            # raw is bytes
            msg = json.loads(raw.decode("utf-8"))
            resp = process_request_message(msg)
            payload = json.dumps(resp).encode("utf-8")
            await producer.send_and_wait("slm.responses", payload)
    finally:
        # Graceful shutdown
        await consumer.stop()
        await producer.stop()


# Helper for external callers (e.g., entrypoint script)
async def start_worker():
    await run_worker()
