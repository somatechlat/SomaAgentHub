import asyncio

from slm.adapters.selector import select_and_call


def test_select_and_call_primary_success():
    async def run():
        res = await select_and_call("hello", {"role": "dialogue_reasoning"})
        assert "primary:" in res["text"]

    asyncio.get_event_loop().run_until_complete(run())


def test_select_and_call_primary_timeout(monkeypatch):
    async def slow_primary(prompt, settings):
        await asyncio.sleep(2)
        return {"text": "slow", "tokens": 1, "latency_ms": 2000}

    import slm.adapters.primary_adapter as pa
    monkeypatch.setattr(pa, "call_primary_provider", slow_primary)

    async def run():
        res = await select_and_call("hello", {"role": "dialogue_reasoning"})
        assert "fallback:" in res["text"]

    asyncio.get_event_loop().run_until_complete(run())
