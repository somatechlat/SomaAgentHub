"""
Pattern library for enterprise workflow orchestration.

Contains production-ready patterns:
- Saga: Distributed transaction compensation
- Circuit Breaker: Fail-fast protection for external services
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    get_all_circuit_breakers,
    get_circuit_breaker,
    reset_all_circuit_breakers,
)
from .saga import Saga, SagaBuilder

__all__ = [
    # Saga pattern
    "Saga",
    "SagaBuilder",
    # Circuit breaker pattern
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_all_circuit_breakers",
]
