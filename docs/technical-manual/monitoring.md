# SomaAgentHub Monitoring & Health

**A guide to the observability, metrics, logging, and alerting for SomaAgentHub.**

This document provides a complete reference for monitoring the health and performance of a SomaAgentHub deployment. It is intended for SREs, DevOps Engineers, and System Administrators.

---

## 🎯 Observability Stack

SomaAgentHub is designed for high observability, shipping with a pre-configured stack that integrates seamlessly with the platform.

| Component | Tool | Purpose |
|---|---|---|
| **Metrics** | Prometheus | Collects and stores time-series data from all services. |
| **Dashboards** | Grafana | Visualizes metrics with pre-built, customizable dashboards. |
| **Logging** | Loki | Aggregates logs from all pods in the cluster. |
| **Alerting** | Alertmanager | Manages and routes alerts based on Prometheus rules. |
| **Tracing** | OpenTelemetry | (Optional) Provides distributed tracing for request lifecycles. |

### How to Access
After deployment, you can access the monitoring tools via `kubectl port-forward`:

```bash
# Port-forward Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n observability

# Port-forward Prometheus
kubectl port-forward svc/prometheus-prometheus 9090:9090 -n observability

# Port-forward Alertmanager
kubectl port-forward svc/prometheus-alertmanager 9093:9093 -n observability
```
- **Grafana**: `http://localhost:3000` (default login: `admin`/`prom-operator`)
- **Prometheus**: `http://localhost:9090`
- **Alertmanager**: `http://localhost:9093`

---

## 📊 Key Metrics (Prometheus)

All services expose a `/metrics` endpoint that Prometheus scrapes. Below are the most critical metrics to monitor.

### 1. Global Platform Health
- `up{job="soma-agent-hub"}`: Service availability. A value of `1` is healthy.
- `http_requests_total`: Total number of HTTP requests, useful for tracking overall traffic.
- `http_request_duration_seconds`: Latency of requests. Monitor the 95th and 99th percentiles.

### 2. Gateway API
- `gateway_api_request_latency_seconds`: End-to-end request latency.
- `gateway_api_active_connections`: Number of active connections.
- `gateway_api_http_status_codes_total`: Breakdown of HTTP response codes (e.g., 2xx, 4xx, 5xx).

### 3. Orchestrator Service
- `orchestrator_workflow_executions_total`: Counter for started, completed, and failed workflows.
- `orchestrator_workflow_duration_seconds`: Histogram of workflow execution times.
- `temporal_activity_execution_latency`: Latency for individual workflow tasks.

### 4. Database & Infrastructure
- `postgres_up`: PostgreSQL database health.
- `redis_up`: Redis cache health.
- `qdrant_health`: Qdrant vector database health.
- `kube_pod_status_phase`: Kubernetes pod health (e.g., Running, Pending, Failed).

---

## 📈 Grafana Dashboards

The Helm chart includes several pre-built Grafana dashboards for immediate visibility.

- **SomaAgentHub - Platform Overview**: A high-level view of system health, including request rates, error rates, and service availability.
- **SomaAgentHub - Service Detail**: A drill-down dashboard to inspect the performance of a specific microservice (e.g., Gateway API, Orchestrator).
- **SomaAgentHub - Workflow Performance**: Metrics focused on Temporal workflow execution, including durations, failure rates, and activity latency.
- **Infrastructure Health**: Health and performance of underlying dependencies like PostgreSQL, Redis, and the Kubernetes cluster itself.

---

## 📝 Logging

### Log Aggregation
Logs from all services are automatically collected by Loki. You can query logs in Grafana using **LogQL**.

### How to Query Logs
1.  Navigate to the **Explore** tab in Grafana.
2.  Select the **Loki** data source.
3.  Use LogQL queries to filter logs:

    ```logql
    # Show all logs from the orchestrator service
    {app="orchestrator", namespace="soma-agent-hub"}

    # Show all error logs from any service
    {namespace="soma-agent-hub"} |= "error"

    # Show logs for a specific workflow run
    {app="orchestrator"} |= "workflow_id=wf_abc123"
    ```

### Log Levels
The log level for services can be configured in the `values.yaml` file.
- `INFO`: Default for production.
- `DEBUG`: Verbose logging for troubleshooting.
- `WARN`: For potential issues.
- `ERROR`: For critical errors.

---

## 🚨 Alerting

The platform includes a set of default alerting rules managed by Alertmanager.

### Critical Alerts
- **ServiceDown**: A core service is unavailable.
- **HighHttp5xxRate**: High rate of server-side errors (HTTP 5xx).
- **HighRequestLatency**: Request latency exceeds the defined SLO.
- **DatabaseDown**: A required database (PostgreSQL, Redis) is down.
- **KubernetesPodCrashLooping**: A pod is repeatedly crashing.

### Configuration
Alerting rules are defined in the Helm chart under `prometheus.additionalPrometheusRules`. You can customize these rules and configure Alertmanager to route notifications to your preferred channels (e.g., Slack, PagerDuty, email).

Example `values.yaml` configuration for Slack alerts:
```yaml
alertmanager:
  config:
    global:
      resolve_timeout: 5m
    route:
      receiver: 'slack-notifications'
    receivers:
    - name: 'slack-notifications'
      slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#soma-alerts'
```

---

## 🩺 Health Endpoints

Every core service exposes a `/health` endpoint that provides a simple health status. This is used by Kubernetes liveness and readiness probes.

```bash
# Check the health of the Gateway API
kubectl exec -n soma-agent-hub <gateway-api-pod-name> -- curl -s http://localhost:10000/health

# Expected Response
{"status": "healthy"}
```

A service may report as unhealthy if it cannot connect to a critical dependency like a database.

---

## 🔗 Related Documentation
- **[Deployment Guide](deployment.md)**: For setting up the monitoring stack.
- **[Operational Runbooks](runbooks/)**: For procedures on how to respond to alerts.
- **[System Architecture](architecture.md)**: To understand the services you are monitoring.
