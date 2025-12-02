"""
MAO Engine - Unified Multi-Agent Orchestrator.

Central orchestration engine that consolidates all proven patterns
and eliminates service fragmentation.

TRUTH: Single orchestrator eliminates complexity and provides enterprise-grade orchestration.
"""

from .core import (
    ActivityDefinition,
    ActivityInstance,
    ActivityRegistry,
    ActivityStatus,
    ActivityType,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CompensationPair,
    Saga,
    SagaBuilder,
    UnifiedMAOEngine,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowRegistry,
    WorkflowStatus,
    WorkflowType,
    activity_registry,
    get_all_circuit_breakers,
    get_circuit_breaker,
    mao_engine,
    reset_all_circuit_breakers,
    workflow_registry,
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
