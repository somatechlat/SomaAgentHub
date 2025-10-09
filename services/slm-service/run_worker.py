#!/usr/bin/env python3
"""Entry point to run the SLM async worker (formerly SomaLLMProvider).

The worker consumes ``slm.requests`` (or legacy ``somallm_provider.requests``) from Kafka and publishes
``slm.responses`` (or legacy ``somallm_provider.responses``).
It expects the environment variable ``KAFKA_BOOTSTRAP_SERVERS`` to be set
(e.g., ``kafka:9092`` when running via Docker‑Compose).
"""
import asyncio
import os

try:
    # Preferred new import
    from slm.worker import start_worker  # type: ignore
except ImportError:  # Backward-compat for legacy package name
    from somallm_provider.worker import start_worker  # type: ignore

if __name__ == "__main__":
    # Ensure the required env var is present early for a clear error message.
    if not os.getenv("KAFKA_BOOTSTRAP_SERVERS"):
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS env var is required to run the worker")
    asyncio.run(start_worker())
