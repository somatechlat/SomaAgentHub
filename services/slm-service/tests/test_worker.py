import asyncio
import json

from slm.worker import process_request_message, consume_and_process


def test_process_request_message():
    msg = {"session_id": "s1", "role": "dialogue_reasoning", "prompt": "hello"}
    resp = process_request_message(msg)
    assert resp["session_id"] == "s1"
    assert "[echo]" in resp["result"]


async def async_get_messages(messages):
    # async generator replacement: returns one message then None
    if not messages:
        return None
    return messages.pop(0)


def test_consume_and_process():
    # prepare a single message
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

    asyncio.get_event_loop().run_until_complete(consume_and_process(get_message, publish))
    assert len(published) == 1
    topic, payload = published[0]
    assert topic == "slm.responses"
    data = json.loads(payload.decode("utf-8"))
    assert data["session_id"] == "s2"
