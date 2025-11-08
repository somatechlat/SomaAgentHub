import logging


def emit_metric(name: str, value, tags: dict = None):
    # For sprint-1 this logs for local dev; production will ship to metrics backend
    logging.getLogger(__name__).info("METRIC %s=%s tags=%s", name, value, tags)
