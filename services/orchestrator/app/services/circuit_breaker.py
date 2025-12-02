"""Production circuit breaker implementation for resilient service communication.

Supports multiple back‑ends (database, Kafka, external services) with configurable
thresholds and automatic recovery. All state changes are exported to Prometheus
metrics for observability.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

from prometheus_client import Counter, Histogram
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
circuit_breaker_state = Counter(
    "circuit_breaker_state_changes_total",
    "Total circuit breaker state changes",
    ["service", "state"],
    )
    circuit_breaker_failures = Counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service", "type"],
    )
    circuit_breaker_duration = Histogram(
    "circuit_breaker_response_duration_seconds",
    "Circuit breaker response duration",
    ["service", "status"],
    )


    class CircuitState(Enum):
    """Possible states of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


    @dataclass
    class CircuitBreakerConfig:
    """Configuration values for a circuit breaker instance."""

    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: type[Exception] = Exception
    success_threshold: int = 2
    name: str = "circuit_breaker"


    class CircuitBreaker:
    """Production circuit breaker with metrics and automatic recovery."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def __call__(
    self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute *func* under circuit‑breaker protection.

        If the breaker is **OPEN** we either raise :class:`ServiceUnavailableError`
        or, after the recovery timeout, transition to **HALF_OPEN** to test the
        downstream service.
        """
        async with self._lock:
    if self.state == CircuitState.OPEN:
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            circuit_breaker_state.labels(
                service=self.config.name, state="half_open"
            ).inc()
            logger.info(
                f"Circuit breaker {self.config.name} entering HALF_OPEN state"
            )
        else:
            raise ServiceUnavailableError(
                f"Circuit breaker {self.config.name} is OPEN"
            )

    # Execute the protected function
    start_time = time.time()
    try:
        result = await func(*args, **kwargs)
        await self._on_success()
        circuit_breaker_duration.labels(
            service=self.config.name, status="success"
        ).observe(time.time() - start_time)
        return result
    except self.config.expected_exception as e:
        await self._on_failure()
        circuit_breaker_failures.labels(
            service=self.config.name, type=type(e).__name__
        ).inc()
        circuit_breaker_duration.labels(
            service=self.config.name, status="failure"
        ).observe(time.time() - start_time)
        raise

    def _should_attempt_reset(self) -> bool:
        """Return ``True`` if the recovery timeout has elapsed."""
        if self.last_failure_time is None:
    return True
    return (time.time() - self.last_failure_time) >= self.config.recovery_timeout

    async def _on_success(self) -> None:
        """Reset failure counters and possibly close the breaker."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
    self.success_count += 1
    if self.success_count >= self.config.success_threshold:
        self.state = CircuitState.CLOSED
        circuit_breaker_state.labels(
            service=self.config.name, state="closed"
        ).inc()
        logger.info(
            f"Circuit breaker {self.config.name} reset to CLOSED"
        )
# When CLOSED we simply keep operating; no action needed.

    async def _on_failure(self) -> None:
        """Record a failure and open the breaker if the threshold is hit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        if self.failure_count >= self.config.failure_threshold:
    self.state = CircuitState.OPEN
    circuit_breaker_state.labels(
        service=self.config.name, state="open"
    ).inc()
    logger.warning(
        f"Circuit breaker {self.config.name} OPENED after {self.failure_count} failures"
    )

    def get_state(self) -> Dict[str, Any]:
        """Return a dictionary describing the current breaker state."""
        return {
    "name": self.config.name,
    "state": self.state.value,
    "failure_count": self.failure_count,
    "success_count": self.success_count,
    "last_failure_time": self.last_failure_time,
    }


    class ServiceUnavailableError(Exception):
    """Raised when a circuit breaker is in the **OPEN** state."""

    pass


# ---------------------------------------------------------------------------
# Pre‑configured circuit breakers for common services
# ---------------------------------------------------------------------------
    DATABASE_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
    name="database",
    failure_threshold=3,
    recovery_timeout=30,
    )
    )

    KAFKA_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
    name="kafka",
    failure_threshold=5,
    recovery_timeout=60,
    )
    )

    EXTERNAL_SERVICE_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
    name="external_service",
    failure_threshold=3,
    recovery_timeout=45,
    )
    )


    class CircuitBreakerManager:
    """Container for multiple circuit‑breaker instances."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register(self, name: str, circuit_breaker: CircuitBreaker) -> None:
        """Register *circuit_breaker* under *name*."""
        self.circuit_breakers[name] = circuit_breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Retrieve a circuit breaker by *name* or ``None`` if missing."""
        return self.circuit_breakers.get(name)

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Return the state of every registered breaker."""
        return {name: cb.get_state() for name, cb in self.circuit_breakers.items()}


# Global manager instance and default registrations
        circuit_breaker_manager = CircuitBreakerManager()
        circuit_breaker_manager.register("database", DATABASE_CIRCUIT_BREAKER)
        circuit_breaker_manager.register("kafka", KAFKA_CIRCUIT_BREAKER)
        circuit_breaker_manager.register("external_service", EXTERNAL_SERVICE_CIRCUIT_BREAKER)
