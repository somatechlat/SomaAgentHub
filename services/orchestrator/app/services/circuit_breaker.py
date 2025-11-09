"""
Production circuit breaker implementation for resilient service communication.

Supports multiple backends: database, kafka, external services with configurable thresholds,
fallback mechanisms, and automatic recovery.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Circuit breaker metrics
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
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type[Exception] = Exception
    fallback_function: Optional[Callable[..., Any]] = None
    success_threshold: int = 2
    name: str = "circuit_breaker"


class CircuitBreaker:
    """Production circuit breaker with metrics and recovery."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def __call__(
        self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute function with circuit breaker protection."""
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
                    if self.config.fallback_function:
                        return await self._execute_fallback(*args, **kwargs)
                    raise ServiceUnavailableError(
                        f"Circuit breaker {self.config.name} is OPEN"
                    )

        # Execute the actual function
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

            if self.config.fallback_function:
                return await self._execute_fallback(*args, **kwargs)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful execution."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                circuit_breaker_state.labels(
                    service=self.config.name, state="closed"
                ).inc()
                logger.info(f"Circuit breaker {self.config.name} reset to CLOSED")
        elif self.state == CircuitState.CLOSED:
            pass  # Normal operation

    async def _on_failure(self) -> None:
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            circuit_breaker_state.labels(service=self.config.name, state="open").inc()
            logger.warning(
                f"Circuit breaker {self.config.name} OPENED after {self.failure_count} failures"
            )

    async def _execute_fallback(self, *args: Any, **kwargs: Any) -> Any:
        """Execute fallback function."""
        if self.config.fallback_function:
            logger.info(f"Executing fallback for circuit breaker {self.config.name}")
            return await self.config.fallback_function(*args, **kwargs)
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state for monitoring."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }


class ServiceUnavailableError(Exception):
    """Raised when circuit breaker is open."""

    pass


# Pre-configured circuit breakers for common services
DATABASE_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
        name="database",
        failure_threshold=3,
        recovery_timeout=30,
        fallback_function=lambda: {"healthy": False, "message": "Database unavailable"},
    )
)

KAFKA_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
        name="kafka",
        failure_threshold=5,
        recovery_timeout=60,
        fallback_function=lambda: {"healthy": False, "message": "Kafka unavailable"},
    )
)

EXTERNAL_SERVICE_CIRCUIT_BREAKER = CircuitBreaker(
    CircuitBreakerConfig(
        name="external_service",
        failure_threshold=3,
        recovery_timeout=45,
        fallback_function=lambda: {
            "healthy": False,
            "message": "External service unavailable",
        },
    )
)


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register(self, name: str, circuit_breaker: CircuitBreaker) -> None:
        """Register a circuit breaker."""
        self.circuit_breakers[name] = circuit_breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {name: cb.get_state() for name, cb in self.circuit_breakers.items()}


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Register default circuit breakers
circuit_breaker_manager.register("database", DATABASE_CIRCUIT_BREAKER)
circuit_breaker_manager.register("kafka", KAFKA_CIRCUIT_BREAKER)
circuit_breaker_manager.register("external_service", EXTERNAL_SERVICE_CIRCUIT_BREAKER)
