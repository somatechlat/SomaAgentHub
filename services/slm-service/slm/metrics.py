def emit_metric(name: str, value, tags: dict = None):
    # For sprint-1 this is a no-op or print for local dev; production will ship to metrics backend
    print(f"METRIC {name}={value} tags={tags}")
