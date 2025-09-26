def call_local_fallback(prompt: str, settings: dict) -> dict:
    """Local fallback returns a deterministic response quickly."""
    return {"text": f"fallback: {prompt}", "tokens": 8, "latency_ms": 5}
