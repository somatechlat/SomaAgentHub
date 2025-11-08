#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio  # noqa: E402
import json  # noqa: E402

from slm.worker import consume_and_process, process_request_message  # noqa: E402


def test_process_request_message():
    msg = {"session_id": "s1", "role": "dialogue_reasoning", "prompt": "hello"}
    resp = process_request_message(msg)
    assert resp["session_id"] == "s1"
    assert "[echo]" in resp["result"]


def test_consume_and_process():
    msg = {"session_id": "s2", "role": "code_generation", "prompt": "gen"}
    raw = json.dumps(msg).encode("utf-8")
    published = []

    async def get_message():
        nonlocal raw
        if raw is None:
            return None
        r = raw
        raw = None
        return r

    async def publish(topic, payload):
        published.append((topic, payload))

    asyncio.get_event_loop().run_until_complete(
        consume_and_process(get_message, publish)
    )
    assert len(published) == 1
    topic, payload = published[0]
    assert topic == "slm.responses"
    data = json.loads(payload.decode("utf-8"))
    assert data["session_id"] == "s2"


if __name__ == "__main__":
    test_process_request_message()
    test_consume_and_process()
    print("WORKER TESTS PASSED")
