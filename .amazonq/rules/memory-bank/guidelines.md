# SomaAgentHub Development Guidelines

## Code Quality Standards

### Documentation Patterns
- **Comprehensive docstrings** - All modules start with detailed docstrings explaining purpose, features, and usage
- **Type annotations** - Extensive use of typing hints with `from typing import Dict, List, Any, Optional`
- **Inline comments** - Strategic comments explaining complex logic and business decisions
- **API documentation** - Clear parameter descriptions and return value specifications

### Code Structure Standards
- **Line length**: 120 characters (configured in pyproject.toml)
- **Import organization**: Standard library, third-party, local imports with clear separation
- **Class organization**: Dataclasses for data structures, clear method grouping with separator comments
- **Error handling**: Comprehensive exception handling with logging and meaningful error messages

### Naming Conventions
- **Snake_case** for variables, functions, and module names
- **PascalCase** for classes and exceptions
- **UPPER_CASE** for constants and configuration values
- **Descriptive names** - `campaign_id`, `experiment_status`, `provision_request` over abbreviations

## Architectural Patterns

### Service Design Patterns
- **FastAPI applications** - Standard pattern for HTTP services with Pydantic models
- **Dataclass models** - Extensive use of `@dataclass` for structured data with type hints
- **Enum classes** - String enums for status values and configuration options
- **Dependency injection** - Services accept clients/dependencies in constructors

### Workflow Patterns (Temporal)
- **Saga pattern** - Automatic compensation for failed workflow steps
- **Signal/Query pattern** - Real-time workflow interaction and progress tracking
- **Activity isolation** - Clear separation between workflow logic and external operations
- **Timeout management** - Explicit timeouts for all activities and workflows

### Error Handling Patterns
- **Structured logging** - Consistent use of `logger.info/error` with contextual data
- **Exception chaining** - Preserve original exceptions while adding context
- **Graceful degradation** - Fallback mechanisms for external service failures
- **Circuit breaker pattern** - Protection against cascading failures

## Internal API Usage Patterns

### HTTP Service Patterns
```python
# Standard FastAPI service structure
app = FastAPI(
    title="Service Name",
    description="Service description",
    version="1.0.0"
)

@app.post("/endpoint", response_model=ResponseModel)
async def endpoint_handler(request: RequestModel):
    # Implementation with proper error handling
```

### Database Integration Patterns
```python
# ClickHouse query pattern
def _store_result(self, data):
    query = """
    INSERT INTO table_name
    (column1, column2, timestamp)
    VALUES
    """
    values = (data.field1, data.field2, datetime.utcnow().isoformat())
    self.client.execute(query, [values])
```

### Configuration Management
```python
# Environment-based configuration
class Config:
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    organization_id: str = Field(..., env="ORGANIZATION_ID")
```

## Frequently Used Code Idioms

### Async/Await Patterns
- **Parallel execution** - `asyncio.gather()` for concurrent operations
- **Timeout handling** - `asyncio.wait_for()` with explicit timeouts
- **Conditional waiting** - `workflow.wait_condition()` for human-in-the-loop workflows

### Data Processing Patterns
- **Running averages** - Mathematical pattern for updating metrics incrementally
- **Weighted selection** - Random selection based on percentage allocations
- **Template rendering** - String formatting for configuration generation

### Logging Patterns
```python
# Structured logging with context
logger.info(
    f"Operation completed: {operation_name}",
    extra={
        "operation_id": operation_id,
        "duration_seconds": duration,
        "items_processed": count
    }
)
```

## Popular Annotations and Decorators

### Temporal Workflow Decorators
- `@workflow.defn` - Workflow class definition
- `@workflow.run` - Main workflow execution method
- `@workflow.signal` - Signal handlers for external events
- `@workflow.query` - Query handlers for real-time status

### FastAPI Decorators
- `@app.post("/path", response_model=Model)` - HTTP endpoint definition
- `@app.get("/health")` - Health check endpoints
- Pydantic `Field(..., description="...")` for API documentation

### Data Structure Annotations
- `@dataclass` - Structured data with automatic methods
- `Optional[Type]` - Nullable fields with clear typing
- `List[Dict[str, Any]]` - Complex nested data structures

## Testing and Quality Patterns

### Test Organization
- **Pytest fixtures** - Reusable test setup with `conftest.py`
- **Integration tests** - Cross-service validation in `tests/integration/`
- **Smoke tests** - Deployment verification with health checks
- **Chaos engineering** - Resilience testing with Chaos Mesh

### Code Quality Tools
- **Ruff** - Linting and formatting with specific rule selection
- **MyPy** - Type checking with ignore_missing_imports
- **Pre-commit hooks** - Automated quality checks before commits

## Infrastructure as Code Patterns

### Terraform Templates
- **String templating** - Dynamic infrastructure generation
- **Tier-based configuration** - Environment-specific resource sizing
- **Output extraction** - JSON parsing for resource endpoints

### Kubernetes Manifests
- **Namespace isolation** - Service separation with dedicated namespaces
- **ConfigMap/Secret management** - Environment-specific configuration
- **Health probe configuration** - Readiness and liveness checks

## Observability Patterns

### Metrics and Monitoring
- **Prometheus integration** - Custom metrics with proper labeling
- **Grafana dashboards** - Visualization for operational metrics
- **Alert configuration** - Proactive monitoring with threshold-based alerts

### Distributed Tracing
- **OpenTelemetry** - Standardized tracing across services
- **Correlation IDs** - Request tracking across service boundaries
- **Performance monitoring** - Latency and throughput measurement