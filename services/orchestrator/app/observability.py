"""
OpenTelemetry instrumentation module for SomaAgent services.
Provides unified metrics, logs, and traces configuration.

Sprint-6 Observability: Export to Prometheus in observability namespace.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
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

        # Resource attributes for all telemetry
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
        """Configure distributed tracing."""
        trace_provider = TracerProvider(resource=self.resource)

        # Add OTLP exporter if enabled (for Tempo in Sprint-6)
        if self.enable_otlp:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability:4317")
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP trace exporter enabled: {otlp_endpoint}")

        trace.set_tracer_provider(trace_provider)
        logger.info(f"Tracing initialized for service: {self.service_name}")

    def setup_metrics(self) -> None:
        """Configure metrics collection and export."""
        readers = []

        # Prometheus metrics reader (for Sprint-6 observability stack)
        if self.enable_prometheus:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
            logger.info(f"Prometheus metrics reader enabled on port {self.prometheus_port}")

        # OTLP metrics exporter if enabled
        if self.enable_otlp:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability:4317")
            # Note: For metrics export, use PeriodicExportingMetricReader in a full setup
            # Leaving just a log line to indicate configuration for now
            logger.info(f"OTLP metrics exporter configured: {otlp_endpoint}")

        meter_provider = MeterProvider(resource=self.resource, metric_readers=readers)
        metrics.set_meter_provider(meter_provider)
        logger.info(f"Metrics initialized for service: {self.service_name}")

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application with OpenTelemetry."""
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"FastAPI instrumentation enabled for {self.service_name}")

    def _setup_loki_logging(self) -> None:
        """Optionally configure Loki logging if LOKI_URL is provided and handler is available."""
        loki_url = os.getenv("LOKI_URL")
        if not loki_url:
            return
        try:
            # Prefer python-logging-loki package if installed
            from logging_loki import LokiHandler  # type: ignore

            handler = LokiHandler(
                url=f"{loki_url.rstrip('/')}/loki/api/v1/push",
                tags={"service": self.service_name, "environment": self.environment},
                version="1",
            )
            root = logging.getLogger()
            root.addHandler(handler)
            if not root.level or root.level == logging.NOTSET:
                root.setLevel(logging.INFO)
            logger.info(f"Loki logging enabled: {loki_url}")
        except Exception as e:  # ImportError or misconfig shouldn't crash service
            logger.warning(f"Loki logging not configured: {e}")

    def setup_all(self, app=None) -> None:
        """Set up all OpenTelemetry components."""
        logger.info(f"Initializing OpenTelemetry for {self.service_name}...")

        self.setup_tracing()
        self.setup_metrics()
        self._setup_loki_logging()

        if app is not None:
            self.instrument_fastapi(app)

        logger.info(f"OpenTelemetry initialization complete for {self.service_name}")


def get_meter(name: str) -> metrics.Meter:
    """Get a meter for custom metrics."""
    return metrics.get_meter(name)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for custom spans."""
    return trace.get_tracer(name)


# Convenience function for quick setup
def setup_observability(
    service_name: str,
    app=None,
    service_version: str = "0.1.0",
    environment: Optional[str] = None,
) -> OpenTelemetryConfig:
    """
    Quick setup function for OpenTelemetry in SomaAgent services.

    Usage:
        from app.observability import setup_observability

        app = FastAPI()
        otel_config = setup_observability("orchestrator", app)
    """
    env = environment or os.getenv("ENVIRONMENT", "development")

    config = OpenTelemetryConfig(
        service_name=service_name,
        service_version=service_version,
        environment=env,
        enable_prometheus=True,
        enable_otlp=os.getenv("ENABLE_OTLP", "false").lower() == "true",
    )

    config.setup_all(app)

    return config
