"""
Circuit Breaker Pattern for External Service Calls.

Prevents cascading failures by failing fast when a service is degraded.
Implements the three-state circuit breaker pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from temporalio import activity


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60  # Time before trying half-open
    window_seconds: int = 60  # Rolling window for failure counting


@dataclass
class CircuitBreakerMetrics:
    """Metrics for a circuit breaker instance."""
    
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open (failing fast)."""
    
    def __init__(self, service_name: str, opened_at: datetime):
        self.service_name = service_name
        self.opened_at = opened_at
        super().__init__(
            f"Circuit breaker OPEN for {service_name} "
            f"(opened at {opened_at.isoformat()})"
        )


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Too many failures, fail fast without calling service
    - HALF_OPEN: Testing if service recovered (limited calls)
    
    State Transitions:
    
        CLOSED ──(failures >= threshold)──> OPEN
           ▲                                  │
           │                                  │
           │                          (timeout elapsed)
           │                                  │
           │                                  ▼
           └──(successes >= threshold)── HALF_OPEN
    
    Usage:
        breaker = CircuitBreaker("github-api")
        
        try:
            result = await breaker.call(make_github_api_call, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit is open, use fallback
            result = get_cached_data()
    
    Real-World Benefits:
    - Prevents wasting resources on failing services
    - Automatic recovery detection
    - Protects downstream from cascading failures
    - Reduces latency (fail fast vs waiting for timeouts)
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Service/endpoint name (for logging/metrics)
            config: Configuration (uses defaults if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.opened_at: Optional[datetime] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function fails (when circuit is closed/half-open)
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed (try half-open)
            if self._should_attempt_reset():
                activity.logger.info(
                    f"[CircuitBreaker:{self.name}] Transitioning to HALF_OPEN",
                )
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                # Still open - fail fast
                raise CircuitBreakerOpenError(self.name, self.opened_at)
        
        # Execute call
        self.metrics.total_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            
            # Success
            self._on_success()
            
            return result
            
        except Exception as e:
            # Failure
            self._on_failure(e)
            
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.metrics.total_successes += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.utcnow()
        
        activity.logger.debug(
            f"[CircuitBreaker:{self.name}] Success "
            f"(consecutive: {self.metrics.consecutive_successes})",
        )
        
        # State transitions on success
        if self.state == CircuitState.HALF_OPEN:
            # Enough successes to close circuit?
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                activity.logger.info(
                    f"[CircuitBreaker:{self.name}] Closing circuit "
                    f"({self.metrics.consecutive_successes} consecutive successes)",
                )
                self._transition_to(CircuitState.CLOSED)
                self.metrics.consecutive_successes = 0
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self.metrics.total_failures += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = datetime.utcnow()
        
        activity.logger.warning(
            f"[CircuitBreaker:{self.name}] Failure: {error} "
            f"(consecutive: {self.metrics.consecutive_failures})",
        )
        
        # State transitions on failure
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open → back to open
            activity.logger.warning(
                f"[CircuitBreaker:{self.name}] Re-opening circuit "
                f"(failure in HALF_OPEN state)",
            )
            self._transition_to(CircuitState.OPEN)
            self.opened_at = datetime.utcnow()
            
        elif self.state == CircuitState.CLOSED:
            # Too many failures → open circuit
            if self.metrics.consecutive_failures >= self.config.failure_threshold:
                activity.logger.error(
                    f"[CircuitBreaker:{self.name}] Opening circuit "
                    f"({self.metrics.consecutive_failures} consecutive failures)",
                )
                self._transition_to(CircuitState.OPEN)
                self.opened_at = datetime.utcnow()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try half-open."""
        if self.opened_at is None:
            return False
        
        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state and record metrics."""
        old_state = self.state
        self.state = new_state
        
        self.metrics.state_transitions.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "total_calls": self.metrics.total_calls,
            "consecutive_failures": self.metrics.consecutive_failures,
        })
        
        activity.logger.info(
            f"[CircuitBreaker:{self.name}] State transition: "
            f"{old_state.value} → {new_state.value}",
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status (for monitoring)."""
        return {
            "name": self.name,
            "state": self.state.value,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "total_successes": self.metrics.total_successes,
                "total_failures": self.metrics.total_failures,
                "success_rate": (
                    self.metrics.total_successes / self.metrics.total_calls
                    if self.metrics.total_calls > 0
                    else 0
                ),
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "last_failure": (
                    self.metrics.last_failure_time.isoformat()
                    if self.metrics.last_failure_time
                    else None
                ),
                "last_success": (
                    self.metrics.last_success_time.isoformat()
                    if self.metrics.last_success_time
                    else None
                ),
            },
            "state_history": self.metrics.state_transitions[-10:],  # Last 10
        }


# Global registry of circuit breakers (one per service)
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    service_name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """
    Get or create circuit breaker for a service.
    
    Args:
        service_name: Unique service identifier
        config: Optional custom configuration
        
    Returns:
        CircuitBreaker instance (reused across calls)
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(service_name, config)
    
    return _circuit_breakers[service_name]


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all circuit breakers (for monitoring endpoint)."""
    return _circuit_breakers.copy()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers (for testing or manual recovery)."""
    for breaker in _circuit_breakers.values():
        breaker.state = CircuitState.CLOSED
        breaker.metrics = CircuitBreakerMetrics()
        breaker.opened_at = None
    
    activity.logger.info(f"Reset {len(_circuit_breakers)} circuit breakers")
