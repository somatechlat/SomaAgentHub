import asyncio


async def call_primary_provider(prompt: str, settings: dict) -> dict:
    """Simulate calling the primary remote provider; return a dict with text and metrics."""
    # For sprint-1 we simulate latency and return a synthetic response
    await asyncio.sleep(0.01)
    return {"text": f"primary: {prompt}", "tokens": 15, "latency_ms": 12}
