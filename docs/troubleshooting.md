# Troubleshooting Guide

This guide collects the most common problems encountered when developing, deploying, or operating **SomaAgentHub** and provides quick steps to resolve them.

---

## Table of Contents

1. [Local Development Issues](#local-development-issues)
2. [Kubernetes / Helm Deployment Problems](#kubernetes--helm-deployment-problems)
3. [Observability & Metrics](#observability--metrics)
4. [Authentication & Identity](#authentication--identity)
5. [Policy Engine Errors](#policy-engine-errors)
6. [Memory Service (Qdrant/Redis) Issues](#memory-service-qdrantredis-issues)
7. [CI/CD Pipeline Failures](#cicd-pipeline-failures)
8. [General Tips & Resources](#general-tips--resources)

---

## Local Development Issues

### 1. `docker compose up` fails with *file not found* errors
* **Cause**: Docker build context was set incorrectly after recent refactoring of service Dockerfiles.
* **Fix**: Ensure you are running the command from the repository root. The `scripts/build‑changed.sh` script now builds with `docker build -f services/<svc>/Dockerfile -t <image> .` which expects the current directory to be the repo root.
* **Verification**: Re‑run `make dev-up` and confirm all services start without `COPY` errors.

### 2. Python virtual environment not picking up dependencies
* **Cause**: The workspace uses a *pyproject.toml* with Poetry, but the developer may have activated a plain `venv`.
* **Fix**: Run `poetry install` to create the environment, then `poetry shell` before executing any Python scripts.
* **Verification**: `python -c "import somabrain"` should succeed without ImportError.

---

## Kubernetes / Helm Deployment Problems

### 1. Helm install fails with *validation error: duplicate key* in `values.yaml`
* **Cause**: Recently merged changes introduced duplicate keys in the Helm values file (e.g., two `memoryBackend` entries).
* **Fix**: Open `k8s/helm/soma-agent/values.yaml` and ensure each top‑level key appears only once. Use `helm lint` locally to catch such issues before PR merge.

### 2. Pods crash‑looping immediately after deployment
* **Common Reasons**:
  * Missing environment variables (e.g., `QDRANT_PORT`).
  * Image tag mismatch – the chart may reference `latest` while the local registry only has a SHA‑tagged image.
* **Fix**:
  1. Run `kubectl describe pod <pod>` to view events and logs.
  2. Verify the image tag in `values.yaml` matches the tag pushed to GHCR (`${{ github.sha }}`).
  3. Ensure required secrets (e.g., `MTLS_CERT`) are created: `make generate-mtls`.

---

## Observability & Metrics

### 1. `/metrics` endpoint returns 404
* **Cause**: The service may not have started the HTTP server exposing metrics, often due to a missing `PROMETHEUS_MULTIPROC_DIR` env var.
* **Fix**: Add the env var to the Helm values under `gateway.metrics.enabled: true` and redeploy.

### 2. Grafana dashboards show no data
* **Cause**: Prometheus scrape configuration does not include the namespace where SomaAgentHub is deployed.
* **Fix**: Edit `infra/monitoring/prometheus.yaml` to add `kubernetes_sd_configs` for the `soma-agent-hub` namespace and reload Prometheus (`kubectl rollout restart deployment/prometheus`).

---

## Authentication & Identity

### 1. 401 Unauthorized on Gateway API requests
* **Cause**: Identity Service is not running or the JWT token is expired.
* **Fix**:
  1. Ensure the `identity-service` pod is healthy (`kubectl get pod -l app=identity-service`).
  2. Regenerate a token using the provided script `scripts/generate-token.sh`.
  3. Pass the token in the `Authorization: Bearer <token>` header.

---

## Policy Engine Errors

### 1. Policy evaluation returns *undefined variable*
* **Cause**: The OPA policy references a variable that is not provided by the request context.
* **Fix**: Update the policy file under `services/policy-engine/policy.rego` to match the request schema, then redeploy the policy engine.

---

## Memory Service (Qdrant/Redis) Issues

### 1. Qdrant connection refused
* **Cause**: Qdrant container not started or port mapping changed.
* **Fix**: Verify the pod status (`kubectl get pod -l app=qdrant`). Ensure `QDRANT_PORT` env var matches the service port (default 10005). If using Kind, run `make port-forward-qdrant`.

### 2. Redis reports *maxmemory exceeded*
* **Cause**: Redis memory limit is too low for the current workload.
* **Fix**: Increase the memory limit in the Helm values (`redis.resources.limits.memory`).

---

## CI/CD Pipeline Failures

### 1. Lint step fails with *hadolint: command not found*
* **Cause**: The runner image does not have `hadolint` installed.
* **Fix**: Add an installation step before linting, e.g. `sudo apt-get update && sudo apt-get install -y hadolint` (already present in the workflow). Ensure the workflow uses `ubuntu-latest`.

### 2. Image scan step fails due to *Trivy not found*
* **Fix**: The workflow includes a step to download Trivy; verify the URL is reachable and the version is still available.

---

## General Tips & Resources

* Use `make lint` locally to catch formatting and lint errors before committing.
* Run `helm lint k8s/helm/soma-agent` to validate Helm templates.
* Consult the **Glossary** (`docs/glossary.md`) for terminology.
* For deeper debugging, enable debug logging in services by setting `LOG_LEVEL=DEBUG` in the Helm values.

---

*Last updated*: 2025‑11‑04
