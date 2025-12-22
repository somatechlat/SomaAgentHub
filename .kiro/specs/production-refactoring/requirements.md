# Requirements Document

## Introduction

This document specifies the requirements for refactoring SomaAgentHub to production-level quality. The refactoring addresses architectural flaws, overlapping services, Vibe Coding Rules violations, placeholder code, and code quality issues identified during a comprehensive codebase audit.

## Glossary

- **SomaAgentHub**: The agent orchestration platform being refactored
- **Vibe Coding Rules**: Development standards requiring no placeholders, stubs, mocks, or hardcoded values
- **Service Consolidation**: Merging overlapping services into unified implementations
- **Production-Ready**: Code that is fully functional, properly tested, and free of placeholder implementations
- **Orchestrator**: The core service coordinating multi-agent workflows via Temporal
- **Memory Gateway**: Service providing vector and key-value storage for agent memory
- **Policy Engine**: Service providing rule-based governance and compliance enforcement
- **EARS Pattern**: Easy Approach to Requirements Syntax - a structured format for writing requirements
- **resolve_env**: The common utility function for loading environment variables with defaults

## Requirements

### Requirement 1: Service Consolidation - Memory Services

**User Story:** As a platform architect, I want to consolidate overlapping memory services, so that the system has a single source of truth for agent memory operations.

#### Acceptance Criteria

1. WHEN the memory-gateway service is deployed THEN the Memory_Gateway SHALL provide both vector storage via Qdrant and key-value storage via Redis through a unified API
2. WHEN recall functionality is needed THEN the Memory_Gateway SHALL handle all recall operations without requiring a separate recall-service
3. IF the recall-service endpoints are accessed THEN the Recall_Service SHALL redirect requests to Memory_Gateway endpoints with HTTP 307 status
4. WHEN memory operations are performed THEN the Memory_Gateway SHALL use consistent Pydantic data models for RememberRequest and RecallResponse

### Requirement 2: Service Consolidation - Workflow Services

**User Story:** As a platform architect, I want to consolidate overlapping workflow orchestration services, so that workflow execution follows a single, well-defined path.

#### Acceptance Criteria

1. WHEN workflow orchestration is needed THEN the Orchestrator SHALL be the single entry point for all workflow types including capsule, graph, and MAO workflows
2. WHEN workflow-engine functionality is required THEN the Orchestrator SHALL incorporate workflow-engine capabilities as internal modules
3. WHEN MAO-engine functionality is required THEN the Orchestrator SHALL incorporate MAO capabilities through its existing MAO router
4. IF duplicate workflow endpoints exist THEN the Orchestrator SHALL consolidate them into unified endpoints
5. WHEN a workflow is started THEN the Orchestrator SHALL route the request regardless of workflow type

### Requirement 3: Remove Placeholder Code

**User Story:** As a developer, I want all placeholder code removed, so that the codebase contains only production-ready implementations.

#### Acceptance Criteria

1. WHEN code contains TODO comments THEN the Developer SHALL either implement the functionality or remove the comment with documented justification in git commit
2. WHEN code contains stub implementations THEN the Developer SHALL replace them with real implementations using actual service calls
3. WHEN code contains placeholder values THEN the Developer SHALL replace them with resolve_env calls loading from environment variables
4. WHEN code contains hardcoded test secrets THEN the Developer SHALL move them to environment variables loaded via resolve_env
5. IF a feature cannot be fully implemented THEN the Service SHALL disable the feature with a clear SERVICE_ENABLED flag and documentation

### Requirement 4: Standardize Health Check Implementations

**User Story:** As an operations engineer, I want consistent health check implementations across all services, so that monitoring and alerting work uniformly.

#### Acceptance Criteria

1. WHEN a service exposes health endpoints THEN the Service SHALL provide /health and /healthz endpoints
2. WHEN the /health endpoint is called THEN the Service SHALL return a JSON structure containing status field and service name
3. WHEN the /healthz endpoint is called THEN the Service SHALL check all critical dependencies and return their individual statuses
4. WHEN the /metrics endpoint is called THEN the Service SHALL expose Prometheus-compatible metrics using prometheus_client library
5. IF dependency checks fail THEN the Service SHALL return HTTP 503 with detailed dependency status in response body

### Requirement 5: Standardize Configuration Management

**User Story:** As a developer, I want consistent configuration management across all services, so that environment setup and deployment are predictable.

#### Acceptance Criteria

1. WHEN a service requires configuration THEN the Service SHALL use the resolve_env function from services.common.config.base_settings
2. WHEN environment variables are needed THEN the Service SHALL use descriptive variable names matching the configuration purpose
3. WHEN secrets are required THEN the Service SHALL load them through resolve_env with empty string defaults, not hardcoded values
4. IF configuration is missing and required THEN the Service SHALL log a warning and disable dependent functionality gracefully
5. WHEN default values are used THEN the Service SHALL use sensible defaults that allow the service to start in development mode

### Requirement 6: Remove or Complete Incomplete Services

**User Story:** As a platform maintainer, I want incomplete services either completed or removed, so that the codebase contains only functional components.

#### Acceptance Criteria

1. WHEN the data-layer service is deployed THEN the Data_Layer SHALL check DATA_LAYER_ENABLED environment variable and only initialize if set to true
2. WHEN the evolution-engine service is deployed THEN the Evolution_Engine SHALL check OPENAI_API_KEY and fall back to rule-based suggestions if unavailable
3. WHEN the self-provisioning service is deployed THEN the Self_Provisioning SHALL check TERRAFORM_ENABLED and return informative messages if disabled
4. WHEN the voice-interface service is deployed THEN the Voice_Interface SHALL check OPENAI_API_KEY and disable transcription endpoints if unavailable
5. IF a service is disabled THEN the Service SHALL return HTTP 503 with clear message explaining how to enable the service

### Requirement 7: Eliminate Code Duplication

**User Story:** As a developer, I want duplicated code patterns consolidated into shared modules, so that maintenance is simplified and consistency is ensured.

#### Acceptance Criteria

1. WHEN Redis client functionality is needed THEN the Service SHALL import from services.common.redis_client module
2. WHEN Qdrant client functionality is needed THEN the Service SHALL import from services.common.qdrant_client module
3. WHEN observability setup is needed THEN the Service SHALL use prometheus_client for metrics exposition
4. WHEN audit logging is needed THEN the Service SHALL import from services.common.audit_logger module
5. WHEN configuration is needed THEN the Service SHALL import resolve_env from services.common.config.base_settings

### Requirement 8: Fix Security Violations

**User Story:** As a security engineer, I want all hardcoded credentials and secrets removed, so that the system follows security best practices.

#### Acceptance Criteria

1. WHEN test secrets exist in production code THEN the Developer SHALL move them to test-specific configuration or environment variables
2. WHEN API keys are referenced THEN the Service SHALL load them from environment variables using resolve_env
3. WHEN database passwords are needed THEN the Service SHALL retrieve them from environment variables with empty string defaults
4. WHEN JWT secrets are used THEN the Service SHALL load them from SOMA_AGENT_HUB_JWT_SECRET environment variable
5. IF credentials are missing THEN the Service SHALL log a warning and disable dependent functionality rather than using placeholder values

### Requirement 9: Standardize Error Handling

**User Story:** As a developer, I want consistent error handling across all services, so that debugging and monitoring are effective.

#### Acceptance Criteria

1. WHEN an error occurs THEN the Service SHALL log it using Python logging module with appropriate level
2. WHEN an HTTP error is returned THEN the Service SHALL use FastAPI HTTPException with detail message
3. WHEN external service calls fail THEN the Service SHALL catch exceptions and return appropriate HTTP status codes (502 for upstream failures, 503 for unavailable)
4. WHEN validation errors occur THEN the Service SHALL let Pydantic handle validation and return HTTP 422 with field-level details
5. WHEN unexpected errors occur THEN the Service SHALL return HTTP 500 with generic message while logging full exception details

### Requirement 10: Update Documentation

**User Story:** As a new developer, I want accurate documentation reflecting the refactored architecture, so that onboarding is efficient.

#### Acceptance Criteria

1. WHEN services are consolidated THEN the Developer SHALL update architecture documentation to reflect the new service structure
2. WHEN services are disabled by default THEN the Service SHALL include docstring explaining how to enable the service
3. WHEN configuration changes THEN the Service SHALL document environment variables in module-level docstrings
4. WHEN API endpoints change THEN the Service SHALL use FastAPI tags and descriptions for automatic OpenAPI generation
5. WHEN the refactoring is complete THEN the Developer SHALL ensure all service main.py files have comprehensive module docstrings
