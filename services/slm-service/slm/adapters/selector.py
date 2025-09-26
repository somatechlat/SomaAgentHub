import asyncio
from typing import Dict

# Import the submodules rather than the functions directly so that tests can monkeypatch
# the functions on the module objects.
from . import primary_adapter
from . import local_fallback
from slm.metrics import emit_metric

async def select_and_call(prompt: str, settings: Dict) -> Dict:
    """Try the primary provider, fall back to local adapter on error or timeout."""
    try:
        # enforce a short timeout for sprint-1
        res = await asyncio.wait_for(primary_adapter.call_primary_provider(prompt, settings), timeout=1.0)
        emit_metric("provider.used", "primary", {"role": settings.get("role")})
        return res
    except Exception as e:
        emit_metric("provider.fallback", "local", {"error": str(e)})
        return local_fallback.call_local_fallback(prompt, settings)
