import asyncio
import json

from slm.producer import make_slm_request_message, Producer


def test_make_slm_request_message_minimal():
    msg = make_slm_request_message("s1", "dialogue_reasoning", "Hello", {"timestamp": "t"})
    assert msg["session_id"] == "s1"
    assert msg["role"] == "dialogue_reasoning"
    assert msg["prompt"] == "Hello"


def test_producer_returns_payload_when_no_kafka():
    p = Producer(aiokafka_producer=None)
    payload = asyncio.get_event_loop().run_until_complete(
        p.send("s2", "code_generation", "Generate code", {"timestamp": "t2"})
    )
    data = json.loads(payload.decode("utf-8"))
    assert data["session_id"] == "s2"
    assert data["role"] == "code_generation"
