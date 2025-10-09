# OpenTelemetry Integration Guide for SomaAgent Services

**Sprint-6 Observability Initiative**  
**Updated:** October 5, 2025

---

## 🎯 Overview

This guide helps all squads add OpenTelemetry instrumentation to their services for Sprint-6 production observability. The goal is to export metrics and logs to Prometheus and Loki in the `observability` namespace. Traces are optional and can be added later.

---

## 📋 Quick Start

### For Python/FastAPI Services

#### 1. Add Dependencies

Already included in most services' `requirements.txt`:
```txt
opentelemetry-sdk>=1.25.0
opentelemetry-exporter-otlp>=1.25.0
opentelemetry-instrumentation-fastapi>=0.46b0
prometheus-client>=0.20.0
```

#### 2. Add Observability Module

Copy the `observability.py` module to your service:
```bash
cp services/orchestrator/app/observability.py services/YOUR_SERVICE/app/
```

#### 3. Update main.py

```python
from .observability import setup_observability

def create_app() -> FastAPI:
    app = FastAPI(title="Your Service", version="0.1.0")
    
    # Add this line - Sprint-6 OpenTelemetry
    setup_observability("your-service", app, service_version="0.1.0")
    
    # ... rest of your app setup
    
    return app
```

#### 4. Add Health and Metrics Endpoints

```python
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi.responses import Response

@app.get("/health")
async def health():
    return {"status": "ok", "service": "your-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

#### 5. Ensure Service Exposes Metrics Port

In your Kubernetes deployment:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: your-service
  labels:
    app: your-service
    monitoring: enabled  # Important for ServiceMonitor!
spec:
  ports:
## 📊 Verify Metrics and Logs

### Prometheus
```bash
kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090
```
Open http://localhost:9090 and run a query like: `up{namespace="somaagent"}`.

### Loki
```bash
kubectl port-forward -n observability svc/loki 3100:3100
```
Query via API: `http://localhost:3100/loki/api/v1/query?query={app="orchestrator"}`

### Add Custom Metrics to Your Service

```python
from app.observability import get_meter

# Get a meter for your service
meter = get_meter("your-service")

# Create counters
request_counter = meter.create_counter(
    name="requests_total",
    description="Total number of requests",
    unit="1"
)

# Create histograms
response_time = meter.create_histogram(
    name="response_duration_seconds",
    description="Response time in seconds",
    unit="s"
)

# Create gauges (via UpDownCounter)
active_sessions = meter.create_up_down_counter(
    name="active_sessions",
    description="Number of active sessions",
    unit="1"
)

# Use in your code
@app.get("/api/endpoint")
async def endpoint():
    request_counter.add(1, {"endpoint": "/api/endpoint", "method": "GET"})
    
    start_time = time.time()
    # ... your logic ...
    duration = time.time() - start_time
    
    response_time.record(duration, {"endpoint": "/api/endpoint"})
    
    return result
```

---

## 🎯 Distributed Tracing

### Add Custom Spans

```python
from app.observability import get_tracer

tracer = get_tracer("your-service")

@app.get("/api/complex-operation")
async def complex_operation():
    with tracer.start_as_current_span("complex_operation") as span:
        span.set_attribute("operation.type", "data_processing")
        
        # Child span for sub-operation
        with tracer.start_as_current_span("database_query"):
            result = await db.query(...)
        
        with tracer.start_as_current_span("external_api_call"):
            response = await external_api.call(...)
        
        return process(result, response)
```

---

## 📊 Service-Specific Metrics

### Orchestrator Service
```python
# KAMACHIQ workflow metrics
workflow_executions = meter.create_counter("kamachiq_workflow_executions_total")
workflow_duration = meter.create_histogram("kamachiq_workflow_duration_seconds")
workflow_failures = meter.create_counter("kamachiq_workflow_failures_total")
```

### Gateway API
```python
# Request metrics
http_requests = meter.create_counter("http_requests_total")
http_request_duration = meter.create_histogram("http_request_duration_seconds")
active_connections = meter.create_up_down_counter("active_connections")
```

### Policy Engine
```python
# Policy evaluation metrics
policy_evaluations = meter.create_counter("policy_evaluations_total")
policy_decisions = meter.create_counter("policy_decisions_total")
policy_eval_duration = meter.create_histogram("policy_evaluation_duration_seconds")
```

### SLM Service
```python
# SLM request metrics
slm_requests = meter.create_counter("slm_requests_total")
slm_tokens_used = meter.create_counter("slm_tokens_used_total")
slm_latency = meter.create_histogram("slm_latency_seconds")
slm_queue_depth = meter.create_up_down_counter("slm_queue_depth")
```

### Identity Service
```python
# Authentication metrics
auth_attempts = meter.create_counter("auth_attempts_total")
token_issuances = meter.create_counter("token_issuances_total")
active_sessions = meter.create_up_down_counter("active_sessions")
```

---

## 🚀 Verification

### 1. Check Metrics Endpoint Locally

```bash
# Start your service
uvicorn app.main:app --reload

# Check metrics endpoint
curl http://localhost:8000/metrics

# Should see output like:
# HELP python_gc_objects_collected_total ...
# TYPE python_gc_objects_collected_total counter
# ...
```

### 2. Verify Prometheus Scraping

```bash
# Port forward Prometheus
kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090
# Query: up{job="your-service"}
# Should show: up{job="your-service"} 1
```

### 3. Check ServiceMonitor

```bash
# Verify ServiceMonitor exists
kubectl get servicemonitor -n observability

# Check if your service is being scraped
kubectl get servicemonitor all-somaagent-services -n observability -o yaml
```

---

<!-- Grafana section removed: we rely on Prometheus + Loki only -->

---

## 🔧 Troubleshooting

### Metrics Not Appearing

1. **Check service has monitoring label:**
   ```bash
   kubectl get svc your-service -o yaml | grep monitoring
   ```

2. **Verify metrics endpoint works:**
   ```bash
   kubectl port-forward svc/your-service 8000:8000
   curl localhost:8000/metrics
   ```

3. **Check Prometheus targets:**
   - Open Prometheus UI: http://localhost:9090/targets
   - Look for your service in the targets list
   - Check if state is "UP"

4. **Check ServiceMonitor:**
   ```bash
   kubectl describe servicemonitor all-somaagent-services -n observability
   ```

### Traces Not Appearing

If using OTLP for traces (Sprint-6 Tempo integration):

```bash
# Check Tempo is running
kubectl get pods -n observability -l app=tempo

# Verify OTLP endpoint
echo $OTEL_EXPORTER_OTLP_ENDPOINT
```

---

## 📝 Sprint-6 Checklist

For each service, complete:

- [ ] Add `observability.py` module
- [ ] Import and call `setup_observability()` in main.py
- [ ] Add `/health` endpoint
- [ ] Add `/metrics` endpoint  
- [ ] Add `monitoring: enabled` label to Kubernetes Service
- [ ] Define service-specific custom metrics
- [ ] Add distributed tracing spans for key operations
- [ ] Verify metrics in Prometheus
- [ ] Create Grafana dashboard
- [ ] Document custom metrics in service README

---

## 🎯 Squad Assignments

| Squad | Services | Lead | Status |
|-------|----------|------|--------|
| Policy & Orchestration | orchestrator, policy-engine | Ada | ✅ Orchestrator done |
| Memory & Constitution | memory-gateway, constitution-service | Ravi | 🟡 Pending |
| SLM Execution | slm-service, model-proxy | Kai | 🟡 Pending |
| Identity & Settings | identity-service, settings-service | Leah | 🟡 Pending |
| UI & Experience | gateway-api, marketplace UI | Mira | 🟡 Pending |
| Infra & Ops | All infrastructure monitoring | Team | ✅ Infrastructure ready |

---

## 📚 References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Documentation](https://grafana.com/docs/)
- Sprint-6 Plan: `docs/sprints/Sprint-6.md`
- Wave C Progress: `docs/sprints/Wave_C_Progress_Oct5.md`

---

## 💡 Tips

1. **Start simple:** Basic instrumentation is better than perfect instrumentation delayed
2. **Use semantic naming:** `service_operation_unit_total` (e.g., `http_requests_total`)
3. **Add labels sparingly:** High cardinality labels (user IDs, session IDs) can overwhelm Prometheus
4. **Test locally first:** Use `curl localhost:8000/metrics` before deploying
5. **Copy patterns:** Look at orchestrator service for reference implementation

---

**Questions?** Ask in #sprint-6-observability Slack channel  
**Blockers?** Escalate to Infra & Ops squad lead

**Target:** All services instrumented by Oct 11 for Integration Day Oct 16! 🚀
