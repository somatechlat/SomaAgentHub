"""Utilities for initializing OpenLLMetry tracing across SomaAgent services."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Mapping, MutableMapping, Optional

try:
    from traceloop.sdk import Traceloop
except ImportError as exc:  # pragma: no cover - dependency injected at runtime
    raise RuntimeError(
        "traceloop-sdk must be installed to use somatrace. Add `traceloop-sdk` to "
        "your dependencies."
    ) from exc

_DEFAULT_ENDPOINT = "http://langfuse-ingester.observability:4318"


def _bool_from_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _serialize_headers(headers: Mapping[str, str]) -> str:
    return ",".join(f"{key}={value}" for key, value in headers.items())


def _merge_headers(existing: str, overrides: Mapping[str, str]) -> str:
    if not existing:
        return _serialize_headers(overrides)
    result: MutableMapping[str, str] = {}
    for pair in existing.split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    for key, value in overrides.items():
        result[key] = value
    return _serialize_headers(result)


@lru_cache(maxsize=1)
def init_tracing(
    app_name: str,
    *,
    endpoint: Optional[str] = None,
    headers: Optional[Mapping[str, str]] = None,
    disable_batch: bool = True,
    trace_content: Optional[bool] = None,
) -> None:
    """Initialise Traceloop instrumentation.

    Parameters
    ----------
    app_name:
        Logical application / service name. Shows up in Langfuse dashboards.
    endpoint:
        Optional OTLP endpoint. Defaults to Langfuse ingester in the observability
        namespace.
    headers:
        Optional OTLP headers map (e.g. authentication tokens).
    disable_batch:
        Whether to disable the OpenTelemetry batch span processor. Defaults to
        ``True`` for low-latency ingestion; can be overridden via keyword args.
    trace_content:
        Overrides content capture (prompts/responses). ``None`` respects
        environment configuration.
    """

    if not app_name:
        raise ValueError("app_name must be a non-empty string")

    otlp_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", _DEFAULT_ENDPOINT)
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", otlp_endpoint)

    existing_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    if headers:
        merged = _merge_headers(existing_headers, headers)
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = merged
    elif not existing_headers:
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = ""

    env_disable_batch = _bool_from_env("TRACELOOP_DISABLE_BATCH", disable_batch)
    os.environ["TRACELOOP_DISABLE_BATCH"] = "true" if env_disable_batch else "false"

    if trace_content is None:
        trace_content = _bool_from_env("TRACE_CONTENT", False)
    os.environ["TRACELOOP_TRACE_CONTENT"] = "true" if trace_content else "false"

    Traceloop.init(app_name=app_name)


def is_tracing_configured() -> bool:
    """Return ``True`` if Traceloop has been initialised in this process."""

    return init_tracing.cache_info().hits > 0 or init_tracing.cache_info().currsize > 0
