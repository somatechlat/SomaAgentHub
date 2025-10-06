#!/usr/bin/env python3
"""Entry point to run the SomaLLMProvider async worker.

The worker consumes ``somallm_provider.requests`` from Kafka and publishes ``somallm_provider.responses``.
It expects the environment variable ``KAFKA_BOOTSTRAP_SERVERS`` to be set
(e.g., ``kafka:9092`` when running via Docker‑Compose).
"""
import asyncio
import os

from somallm_provider.worker import start_worker

if __name__ == "__main__":
    # Ensure the required env var is present early for a clear error message.
    if not os.getenv("KAFKA_BOOTSTRAP_SERVERS"):
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS env var is required to run the worker")
    asyncio.run(start_worker())
