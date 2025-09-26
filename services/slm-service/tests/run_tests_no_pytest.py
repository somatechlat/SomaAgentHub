#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure slm-service package is on sys.path (add the slm-service directory)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from slm.producer import make_slm_request_message, Producer
import json


def test_make_slm_request_message_minimal():
    msg = make_slm_request_message("s1", "dialogue_reasoning", "Hello", {"timestamp": "t"})
    assert msg["session_id"] == "s1"
    assert msg["role"] == "dialogue_reasoning"
    assert msg["prompt"] == "Hello"


def test_producer_returns_payload_when_no_kafka():
    p = Producer(aiokafka_producer=None)
    payload = p.send("s2", "code_generation", "Generate code", {"timestamp": "t2"})
    # p.send is async — run it
    import asyncio
    payload = asyncio.get_event_loop().run_until_complete(payload)
    data = json.loads(payload.decode("utf-8"))
    assert data["session_id"] == "s2"
    assert data["role"] == "code_generation"


if __name__ == "__main__":
    test_make_slm_request_message_minimal()
    test_producer_returns_payload_when_no_kafka()
    print("ALL TESTS PASSED")
