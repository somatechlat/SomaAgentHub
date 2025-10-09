# Flink Service

This service hosts Apache Flink jobs that perform real‑time stream processing for SomaAgentHub. It is intended to ingest events from the ClickHouse analytics pipeline, enrich them, and push metrics to Prometheus.

## Components
- **PyFlink job** (`job.py`) – defines the data pipeline.
- **Dockerfile** – builds a container with Flink runtime and Python dependencies.
- **Kubernetes deployment** – `k8s/flink-deployment.yaml`.

## Build & Run
```bash
# Build the Docker image
docker build -t somatechlat/soma-flink-service:latest ./services/flink-service

# Deploy to k8s (requires the manifest)
kubectl apply -f k8s/flink-deployment.yaml
```
