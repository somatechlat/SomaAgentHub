"""
Shared OpenTelemetry instrumentation for SomaAgent services.

Provides a unified setup for metrics and tracing with Prometheus and optional OTLP.
"""

from __future__ import annotations

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
except ImportError:  # pragma: no cover - optional dependency
    PrometheusMetricReader = None  # type: ignore[assignment]
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


class OpenTelemetryConfig:
    """OpenTelemetry configuration for SomaAgent services."""

    def __init__(
        self,
        service_name: str,
        service_version: str = "0.1.0",
        environment: str = "development",
        enable_prometheus: bool = True,
        enable_otlp: bool = False,
        prometheus_port: int = 8000,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.enable_prometheus = enable_prometheus
        self.enable_otlp = enable_otlp
        self.prometheus_port = prometheus_port

        self.resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
            }
        )

    def setup_tracing(self) -> None:
        provider = TracerProvider(resource=self.resource)
        if self.enable_otlp:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OTLP trace exporter enabled: {otlp_endpoint}")
        trace.set_tracer_provider(provider)
        logger.info(f"Tracing initialized for service: {self.service_name}")

    def setup_metrics(self) -> None:
        readers = []
        if self.enable_prometheus:
            if PrometheusMetricReader is None:
                logger.warning(
                    "Prometheus exporter not installed; metrics endpoint will be disabled."
                )
            else:
                readers.append(PrometheusMetricReader())
                logger.info(f"Prometheus metrics reader enabled on port {self.prometheus_port}")
        meter_provider = MeterProvider(resource=self.resource, metric_readers=readers)
        metrics.set_meter_provider(meter_provider)
        logger.info(f"Metrics initialized for service: {self.service_name}")

    def instrument_fastapi(self, app) -> None:
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"FastAPI instrumentation enabled for {self.service_name}")

    def setup_all(self, app=None) -> None:
        logger.info(f"Initializing OpenTelemetry for {self.service_name}...")
        self.setup_tracing()
        self.setup_metrics()
        if app is not None:
            self.instrument_fastapi(app)
        logger.info(f"OpenTelemetry initialization complete for {self.service_name}")


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def setup_observability(
    service_name: str,
    app=None,
    service_version: str = "0.1.0",
    environment: str | None = None,
) -> OpenTelemetryConfig:
    env = environment or os.getenv("ENVIRONMENT", "development")
    # Enable OTLP by default in development, allow override via env var
    enable_otlp = os.getenv("ENABLE_OTLP", "true" if env == "development" else "false").lower() == "true"
    config = OpenTelemetryConfig(
        service_name=service_name,
        service_version=service_version,
        environment=env,
        enable_prometheus=True,
        enable_otlp=enable_otlp,
    )
    config.setup_all(app)
    return config
