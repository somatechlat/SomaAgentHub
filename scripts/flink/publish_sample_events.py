#!/usr/bin/env python3
"""Publish synthetic SomaAgentHub events to Kafka for Flink smoke testing."""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer


def build_event(index: int) -> dict:
    now = datetime.now(tz=timezone.utc)
    return {
        "id": f"evt-{index}-{int(now.timestamp())}",
        "ts": now.isoformat(),
        "payload": {
            "tenant": random.choice(["demo", "enterprise"]),
            "event_type": random.choice(["message", "task", "tool_call"]),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", default="localhost:9093", help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="soma.events")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--sleep", type=float, default=0.1, help="Delay between publishes in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    producer = KafkaProducer(bootstrap_servers=args.bootstrap, value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    for idx in range(args.count):
        event = build_event(idx)
        producer.send(args.topic, event)
        producer.flush()
        time.sleep(args.sleep)
    producer.close()


if __name__ == "__main__":
    main()
