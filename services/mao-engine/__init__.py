"""
MAO Engine - Unified Multi-Agent Orchestrator.

Central orchestration engine that consolidates all proven patterns
and eliminates service fragmentation.

TRUTH: Single orchestrator eliminates complexity and provides enterprise-grade orchestration.
"""

from .core import (
UnifiedMAOEngine,
mao_engine,
Saga,
SagaBuilder,
CompensationPair,
CircuitBreaker,
CircuitBreakerConfig,
CircuitBreakerOpenError,
get_circuit_breaker,
get_all_circuit_breakers,
reset_all_circuit_breakers,
WorkflowRegistry,
WorkflowType,
WorkflowStatus,
WorkflowDefinition,
WorkflowInstance,
workflow_registry,
ActivityRegistry,
ActivityType,
ActivityStatus,
ActivityDefinition,
ActivityInstance,
activity_registry,
)

__version__ = "1.0.0"
__description__ = "Unified Multi-Agent Orchestrator Engine"

__all__ = [
# Core engine
"UnifiedMAOEngine",
"mao_engine",
# Saga pattern
"Saga",
"SagaBuilder",
"CompensationPair",
# Circuit breaker
"CircuitBreaker",
"CircuitBreakerConfig",
"CircuitBreakerOpenError",
"get_circuit_breaker",
"get_all_circuit_breakers",
"reset_all_circuit_breakers",
# Workflow registry
"WorkflowRegistry",
"WorkflowType",
"WorkflowStatus",
"WorkflowDefinition",
"WorkflowInstance",
"workflow_registry",
# Activity registry
"ActivityRegistry",
"ActivityType",
"ActivityStatus",
"ActivityDefinition",
"ActivityInstance",
"activity_registry",
]