"""Logging helpers for SomaGent services."""

import logging
from typing import Literal

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_SUPPORTED_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def configure_logging(level: Literal["debug", "info", "warning", "error", "critical"] = "info") -> None:
    """Configure root logging with a consistent format across services."""

    logging.basicConfig(level=_SUPPORTED_LEVELS[level], format=_LOG_FORMAT)
