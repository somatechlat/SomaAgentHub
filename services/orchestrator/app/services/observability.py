"""
Comprehensive observability stack with OpenTelemetry, structured logging, and metrics.

This module provides:
    - OpenTelemetry tracing for distributed tracing
    - Structured JSON logging with context propagation
    - Comprehensive metrics collection with Prometheus
    - Request/response correlation IDs
    - Performance monitoring and alerting
"""

from __future__ import annotations

import json
import logging
import time
from contextvars import ContextVar
from typing import Any
from uuid import uuid4

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)

# Context variables for distributed tracing
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
session_id_var: ContextVar[str] = ContextVar("session_id", default="")

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code", "service"],
)

active_connections = Gauge(
    "active_connections_total",
    "Number of active connections",
    ["service"],
)

business_metric_total = Counter(
    "business_events_total",
    "Total business events processed",
    ["event_type", "status", "service"],
)

database_query_duration = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["operation", "table", "service"],
)

external_service_duration = Histogram(
    "external_service_duration_seconds",
    "External service call duration",
    ["service_name", "endpoint", "status", "service"],
)


# OpenTelemetry setup
def setup_opentelemetry(service_name: str, service_version: str) -> None:
    """Initialize OpenTelemetry with OTLP exporter."""
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": service_version,
            "service.namespace": "soma-agent-hub",
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # OTLP exporter
    otlp_endpoint = resolve_env("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    tracer = trace.get_tracer(__name__)
    return tracer


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with context."""
        log_data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": correlation_id_var.get(),
            "user_id": user_id_var.get(),
            "session_id": session_id_var.get(),
            "service": "orchestrator-service",
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = str(value)

        return json.dumps(log_data)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for observability: tracing, metrics, logging."""

    def __init__(self, app):
        super().__init__(app)
        self.service_name = "orchestrator-service"

    async def dispatch(self, request: Request, call_next):
        """Process request with observability."""
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        correlation_id_token = correlation_id_var.set(correlation_id)

        # Extract user context from headers
        user_id = request.headers.get("X-User-ID", "")
        session_id = request.headers.get("X-Session-ID", "")

        if user_id:
            user_id_var.set(user_id)
        if session_id:
            session_id_var.set(session_id)

        # Track active connections
        active_connections.labels(service=self.service_name).inc()

        start_time = time.time()

        # Log incoming request
        logger.info(
            "HTTP request started",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent"),
            },
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=str(response.status_code),
                service=self.service_name,
            ).inc()

            http_request_duration.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=str(response.status_code),
                service=self.service_name,
            ).observe(duration)

            # Add correlation ID to response
            response.headers["X-Correlation-ID"] = correlation_id

            # Log response
            logger.info(
                "HTTP request completed",
                extra={
                    "status_code": response.status_code,
                    "duration": duration,
                    "method": request.method,
                    "path": str(request.url.path),
                },
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code="500",
                service=self.service_name,
            ).inc()

            logger.error(
                "HTTP request failed",
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration": duration,
                    "error": str(e),
                },
            )
            raise

        finally:
            active_connections.labels(service=self.service_name).dec()
            correlation_id_var.reset(correlation_id_token)


class BusinessMetrics:
    """Helper class for business-level metrics."""

    @staticmethod
    def record_event(
        event_type: str, status: str, metadata: dict[str, Any] | None = None
    ):
        """Record a business event."""
        business_metric_total.labels(
            event_type=event_type,
            status=status,
            service="orchestrator-service",
        ).inc()

        logger.info(
            f"Business event: {event_type}",
            extra={
                "event_type": event_type,
                "status": status,
                **(metadata or {}),
            },
        )

    @staticmethod
    def record_database_operation(operation: str, table: str, duration: float):
        """Record database operation metrics."""
        database_query_duration.labels(
            operation=operation,
            table=table,
            service="orchestrator-service",
        ).observe(duration)

    @staticmethod
    def record_external_service_call(
        service_name: str, endpoint: str, status: str, duration: float
    ):
        """Record external service call metrics."""
        external_service_duration.labels(
            service_name=service_name,
            endpoint=endpoint,
            status=status,
            service="orchestrator-service",
        ).observe(duration)


class Tracer:
    """Tracer wrapper for consistent tracing across the service."""

    def __init__(self, name: str):
        self.tracer = trace.get_tracer(name)

    def span(self, name: str, attributes: dict[str, Any] | None = None):
        """Create a span with context."""
        trace.get_current_span()

        # Add context attributes
        span_attributes = {
            "correlation.id": correlation_id_var.get(),
            "user.id": user_id_var.get(),
            "session.id": session_id_var.get(),
        }

        if attributes:
            span_attributes.update(attributes)

        return self.tracer.start_as_current_span(name, attributes=span_attributes)


def setup_logging():
    """Setup structured JSON logging."""
    log_level = resolve_env("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add structured JSON handler
    handler = logging.StreamHandler()
    formatter = StructuredJSONFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def setup_observability(app):
    """Complete observability setup for FastAPI app."""
    main_app = app

    # Setup OpenTelemetry
    tracer = setup_opentelemetry(
        service_name="orchestrator-service", service_version="0.1.0"
    )

    # Setup logging
    setup_logging()

    # Add middleware
    main_app.add_middleware(ObservabilityMiddleware)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(main_app)

    # Instrument SQLAlchemy
    from ..database import async_engine

    SQLAlchemyInstrumentor().instrument(engine=async_engine.sync_engine)

    logger.info("Observability stack initialized successfully")

    return tracer


# Global tracer instance
orchestrator_tracer = Tracer("orchestrator-service")
