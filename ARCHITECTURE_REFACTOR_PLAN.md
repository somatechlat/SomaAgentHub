# 🏗️ SomaAgentHub Architecture Refactoring Plan

## Executive Summary

The current SomaAgentHub architecture suffers from significant architectural issues including service fragmentation, overlapping functionality, inconsistent patterns, and lack of centralized governance. This document outlines a comprehensive refactoring plan to transform the codebase into a production-ready, centralized, and maintainable architecture.

## Current State Analysis

### Critical Issues Identified

#### 1. Service Overlap and Fragmentation
- **Duplicate Services**: `gateway-api` vs `gateway_api`, `task-capsule-repo` vs `task_capsule_repo`
- **Similar Functionality**: Multiple services doing similar things (e.g., multiple LLM services, overlapping analytics)
- **Inconsistent Naming**: Mixed naming conventions across services

#### 2. Configuration Chaos
- **Multiple Config Systems**: At least 6 different configuration patterns identified:
  - `BaseServiceSettings` (common/config/base_settings.py)
  - `UnifiedConfigManager` (common/config/unified_config.py)  
  - Per-service Settings classes (GatewaySettings, Settings, etc.)
  - Direct `resolve_env` usage
  - Legacy configuration files
  - Service-specific config modules

#### 3. Client Management Problems
- **Duplicate Clients**: Multiple implementations of Redis, Vault, OPA, Kafka clients
- **Inconsistent Patterns**: Some services use common clients, others implement their own
- **Tight Coupling**: Direct client instantiation throughout codebase

#### 4. Architectural Pattern Inconsistencies
- **Mixed Frameworks**: FastAPI, Flask, and custom HTTP implementations
- **Inconsistent Middleware**: Different authentication, logging, and observability patterns
- **Database Access**: Multiple ORM patterns (SQLAlchemy, SQLModel, direct SQL)

#### 5. Dependency Hell
- **Circular Dependencies**: Services importing each other in complex patterns
- **Deep Coupling**: Services directly importing implementation details from other services
- **Common Library Confusion**: Unclear boundaries between shared and service-specific code

## Target Architecture

### Core Principles

1. **Single Source of Truth**: One configuration system, one client management system
2. **Clear Service Boundaries**: Well-defined APIs and contracts between services
3. **Centralized Common Functionality**: Shared utilities in a single, well-organized location
4. **Consistent Patterns**: Same architectural patterns across all services
5. **Loose Coupling**: Services communicate through defined interfaces, not implementation details

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SomaAgentHub Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                    API Gateway Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Gateway API   │  │   Load Balancer │  │   Ingress       │  │
│  │   (Unified)     │  │                 │  │   Controller    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Service Layer                               │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Orchestrator  │  │   Agent Manager │  │   Capsule       │  │
│  │   (Workflow)    │  │   (Runtime)     │  │   Registry      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Builder       │  │   Analytics     │  │   Identity &    │  │
│  │   Service       │  │   Engine        │  │   Auth Service  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                   Common Services Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Config        │  │   Client Factory│  │   Event Bus     │  │
│  │   Management    │  │   (Singletons)  │  │   System        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Security &    │  │   Observability │  │   Database      │  │
│  │   Auth          │  │   Framework     │  │   Abstraction   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL    │  │   Redis Cache   │  │   Message Queue │  │
│  │                 │  │                 │  │   (Kafka)       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Object Store  │  │   Secrets       │  │   Monitoring    │  │
│  │   (MinIO/S3)    │  │   (Vault)       │  │   Stack         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Service Consolidation Plan

#### Phase 1: Core Service Unification

**Remove Duplicate Services:**
- Merge `gateway-api` and `gateway_api` → `gateway-service`
- Merge `task-capsule-repo` and `task_capsule_repo` → `capsule-registry`
- Consolidate multiple LLM services → `llm-service`
- Merge analytics services → `analytics-service`

**Service Boundaries Redefined:**
1. **Gateway Service** (`gateway-service`)
   - Single entry point for all external APIs
   - Authentication, rate limiting, request routing
   - No business logic - pure API gateway

2. **Orchestrator Service** (`orchestrator-service`)
   - Workflow management and coordination
   - Agent lifecycle management
   - Business process execution

3. **Builder Service** (`builder-service`)
   - Template processing and static code generation
   - Build pipeline orchestration
   - Artifact management

4. **Capsule Registry** (`capsule-registry`)
   - Capsule manifest storage and versioning
   - Template repository
   - Metadata management

5. **Agent Manager** (`agent-manager`)
   - Agent runtime environment
   - Resource management and scaling
   - Agent health monitoring

#### Phase 2: Common Services Centralization

**Unified Configuration System:**
```
common/
├── config/
│   ├── __init__.py
│   ├── base_config.py           # Base configuration class
│   ├── service_config.py        # Service-specific configuration
│   └── env_resolver.py          # Environment variable resolution
├── clients/
│   ├── __init__.py
│   ├── client_factory.py       # Centralized client management
│   ├── redis_client.py         # Unified Redis client
│   ├── vault_client.py         # Unified Vault client
│   ├── kafka_client.py         # Unified Kafka client
│   └── opa_client.py           # Unified OPA client
├── security/
│   ├── __init__.py
│   ├── auth_middleware.py      # Authentication middleware
│   ├── authorization.py        # Authorization logic
│   └── crypto_utils.py         # Cryptographic utilities
├── observability/
│   ├── __init__.py
│   ├── logging.py              # Structured logging
│   ├── metrics.py              # Metrics collection
│   ├── tracing.py              # Distributed tracing
│   └── health_checks.py        # Health check framework
└── database/
    ├── __init__.py
    ├── base_models.py          # Base database models
    ├── connection.py           # Database connection management
    └── migrations.py           # Migration utilities
```

**Client Factory Pattern:**
```python
# common/clients/client_factory.py
class ClientFactory:
    _instances = {}
    
    @classmethod
    def get_redis_client(cls) -> RedisClient:
        if 'redis' not in cls._instances:
            cls._instances['redis'] = RedisClient()
        return cls._instances['redis']
    
    @classmethod
    def get_vault_client(cls) -> VaultClient:
        if 'vault' not in cls._instances:
            cls._instances['vault'] = VaultClient()
        return cls._instances['vault']
    
    # Similar methods for all clients
```

#### Phase 3: Service Communication Standardization

**Event-Driven Architecture:**
```python
# common/events/
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional

class EventType(Enum):
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    CAPSULE_REGISTERED = "capsule.registered"
    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"

@dataclass
class Event:
    event_type: EventType
    tenant_id: str
    user_id: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
```

**Service Contracts:**
```python
# common/contracts/
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class AgentRequest(BaseModel):
    agent_type: str = Field(..., description="Type of agent to create")
    capsule_id: Optional[str] = Field(None, description="Associated capsule")
    config: Dict[str, Any] = Field(default_factory=dict)
    
class AgentResponse(BaseModel):
    agent_id: str
    status: str
    endpoints: List[str]
    metadata: Dict[str, Any]
```

## Detailed Refactoring Roadmap

### Phase 1: Foundation Stabilization (Weeks 1-2)

**Priority 1: Configuration System Unification**
1. **Create Unified Config System**
   - Design single configuration hierarchy
   - Implement environment variable resolution
   - Create service-specific configuration extensions
   - Migrate all services to new config system

2. **Client Factory Implementation**
   - Implement centralized client factory
   - Migrate all client instantiations to use factory
   - Remove duplicate client implementations
   - Add client health checks and monitoring

3. **Service Consolidation**
   - Merge duplicate services
   - Update all inter-service references
   - Remove deprecated service implementations
   - Update deployment configurations

**Deliverables:**
- Unified configuration system
- Client factory with all common clients
- Consolidated service structure
- Updated deployment manifests

### Phase 2: Common Services Implementation (Weeks 3-4)

**Priority 1: Security & Auth Framework**
1. **Unified Authentication**
   - Implement JWT validation middleware
   - Create service-to-service authentication
   - Standardize permission checking
   - Implement SPIFFE integration

2. **Observability Framework**
   - Structured logging implementation
   - Distributed tracing setup
   - Metrics collection standardization
   - Health check framework

3. **Database Abstraction**
   - Unified ORM layer
   - Connection pooling management
   - Migration system
   - Query optimization utilities

**Priority 2: Event System Implementation**
1. **Event Bus Setup**
   - Kafka topic standardization
   - Event serialization format
   - Event publishing framework
   - Event consumption patterns

2. **Service Contract Definition**
   - API schema standardization
   - Request/response models
   - Error handling patterns
   - Versioning strategy

**Deliverables:**
- Security and authentication framework
- Observability and monitoring system
- Database abstraction layer
- Event bus and messaging system
- Service contracts and APIs

### Phase 3: Service Refactoring (Weeks 5-8)

**Priority 1: Core Services Refactoring**
1. **Gateway Service**
   - Pure API gateway implementation
   - Authentication and authorization
   - Rate limiting and throttling
   - Request routing and load balancing

2. **Orchestrator Service**
   - Workflow engine refactoring
   - Agent lifecycle management
   - Business logic separation
   - Event-driven communication

3. **Builder Service**
   - Template processing pipeline
   - Build orchestration
   - Artifact management
   - Integration with external systems

**Priority 2: Support Services Refactoring**
1. **Capsule Registry**
   - Manifest storage and versioning
   - Template management
   - Metadata indexing
   - Search and discovery

2. **Agent Manager**
   - Runtime environment management
   - Resource allocation
   - Health monitoring
   - Scaling and auto-healing

**Deliverables:**
- Refactored core services
- Updated service APIs
- Event-driven communication
- Comprehensive testing suite

### Phase 4: Production Readiness (Weeks 9-12)

**Priority 1: Security Hardening**
1. **Security Implementation**
   - mTLS for all service communication
   - Secret management with Vault
   - Security scanning and SBOM generation
   - Audit logging and compliance

2. **Performance Optimization**
   - Load testing and optimization
   - Caching strategies
   - Database query optimization
   - Resource usage monitoring

**Priority 2: Deployment and Operations**
1. **Infrastructure as Code**
   - Kubernetes manifests standardization
   - Helm chart development
   - Environment-specific configurations
   - Deployment automation

2. **Monitoring and Alerting**
   - Comprehensive dashboards
   - Alert rule definition
   - Incident response procedures
   - Performance baselines

**Deliverables:**
- Production-ready deployment
- Security certifications
- Performance benchmarks
- Operations documentation

## Non-Functional Requirements

### Security
- **Authentication**: JWT-based authentication with SPIFFE integration
- **Authorization**: OPA-based policy enforcement
- **Communication**: mTLS for all service-to-service communication
- **Secrets**: Vault-managed secrets with automatic rotation
- **Audit**: Comprehensive audit logging for all operations

### Observability
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Prometheus-based metrics with standardized labels
- **Tracing**: OpenTelemetry-based distributed tracing
- **Health**: Standardized health checks for all services
- **Alerting**: Intelligent alerting with escalation policies

### Performance
- **Latency**: <100ms for API operations, <5s for complex workflows
- **Throughput**: 1000+ concurrent requests, 10k+ events/second
- **Scalability**: Horizontal scaling for all services
- **Availability**: 99.9% uptime with graceful degradation
- **Resource Usage**: Optimized resource utilization with auto-scaling

### Maintainability
- **Code Quality**: Consistent code style, comprehensive testing
- **Documentation**: Auto-generated API documentation
- **Deployment**: Zero-downtime deployments with rollback capability
- **Monitoring**: Real-time monitoring with predictive alerting
- **Testing**: Automated testing at all levels (unit, integration, E2E)

## Risk Mitigation

### Technical Risks
1. **Service Disruption**
   - Mitigation: Phased rollout with canary deployments
   - Backup: Rollback procedures and blue-green deployments

2. **Performance Regression**
   - Mitigation: Performance testing at each phase
   - Backup: Performance baselines and monitoring

3. **Data Migration**
   - Mitigation: Careful migration planning with validation
   - Backup: Comprehensive backup and restore procedures

### Operational Risks
1. **Deployment Complexity**
   - Mitigation: Automation and deployment scripts
   - Backup: Manual deployment procedures

2. **Monitoring Gaps**
   - Mitigation: Incremental monitoring implementation
   - Backup: Manual monitoring procedures

3. **Skill Gaps**
   - Mitigation: Training and documentation
   - Backup: External expertise availability

## Success Criteria

### Phase 1 Success Criteria
- [ ] All services use unified configuration system
- [ ] Client factory implemented and used by all services
- [ ] Duplicate services consolidated and removed
- [ ] No configuration-related runtime errors

### Phase 2 Success Criteria
- [ ] Security framework implemented across all services
- [ ] Observability system collecting metrics and logs
- [ ] Event bus handling service communication
- [ ] Service contracts defined and implemented

### Phase 3 Success Criteria
- [ ] Core services refactored with clean architecture
- [ ] Event-driven communication established
- [ ] All APIs standardized and documented
- [ ] Comprehensive test coverage

### Phase 4 Success Criteria
- [ ] Production deployment successful
- [ ] Security requirements met
- [ ] Performance benchmarks achieved
- [ ] Operations documentation complete

## Conclusion

This refactoring plan provides a comprehensive approach to transforming SomaAgentHub from its current fragmented state into a production-ready, centralized architecture. The phased approach ensures minimal disruption while systematically addressing the architectural issues.

The key to success is strict adherence to the architectural principles and careful execution of each phase. The result will be a maintainable, scalable, and secure platform that can support the advanced capabilities envisioned for SomaAgentHub.

## Next Steps

1. **Immediate Action**: Begin Phase 1 with configuration system unification
2. **Team Preparation**: Assign ownership for each service and component
3. **Environment Setup**: Prepare development, staging, and production environments
4. **Monitoring Setup**: Implement basic monitoring to track refactoring progress
5. **Communication**: Establish regular status meetings and progress reporting

This plan represents a significant investment in the future of SomaAgentHub and will position the platform for long-term success and scalability.