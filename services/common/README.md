# SomaAgent Common Libraries

Shared code for all SomaAgent services.

## Modules

### health.py
Health and readiness endpoints for Kubernetes probes.

**Usage:**
```python
from fastapi import FastAPI
from common.health import create_health_router, health_check

app = FastAPI()

# Add health endpoints
app.include_router(create_health_router(
    service_name="orchestrator",
    version="1.0.0"
))

# Mark service as ready after initialization
@app.on_event("startup")
async def startup():
    # Initialize dependencies...
    health_check.set_ready(True)
```

**Endpoints:**
- `GET /health` - Liveness probe (always returns 200)
- `GET /ready` - Readiness probe (checks dependencies)
- `GET /healthz` - Alternative liveness endpoint
- `GET /readyz` - Alternative readiness endpoint
- `GET /version` - Service version info

### observability.py
OpenTelemetry instrumentation for metrics and tracing.

See individual service `app/observability.py` for usage.
