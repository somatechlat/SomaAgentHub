# Simple, explicit Makefile to orchestrate build, deploy, and tests
# Usage: `make <target>`

# Registry configuration
REGISTRY ?= somaagent
TAG ?= latest
NAMESPACE ?= somaagent
OBS_NS ?= observability

# Image names
IMG_GATEWAY := $(REGISTRY)/gateway-api:$(TAG)
IMG_ORCH := $(REGISTRY)/orchestrator:$(TAG)
IMG_ID := $(REGISTRY)/identity-service:$(TAG)

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make images            Build all service images"
	@echo "  make push              Push all service images"
	@echo "  make deploy            Deploy infra + services to k8s"
	@echo "  make status            Show pods and services"
	@echo "  make pf-gateway        Port-forward gateway 8080"
	@echo "  make pf-prom           Port-forward Prometheus 9090"
	@echo "  make test-int          Run gateway integration test"
	@echo "  make test-e2e          Run gateway→orchestrator e2e test"
	@echo "  make logs-orch         Tail orchestrator logs"
	@echo "  make airflow-up        Build & launch local Airflow stack"
	@echo "  make airflow-down      Stop local Airflow stack"
	@echo "  make flink-up          Build & launch local Flink stack"
	@echo "  make flink-down        Stop local Flink stack"

# Developer convenience targets (local infra)
dev-network:
	@echo "Creating developer docker network 'somaagenthub-network' if missing..."
	@docker network create somaagenthub-network || true

dev-up:
	@echo "Bringing up Temporal (local) via docker-compose and a local Redis"
	@docker network create somaagenthub-network || true
	@bash ./scripts/select_free_ports.sh
	@docker compose -f infra/temporal/docker-compose.yml -f infra/temporal/docker-compose.override.ports.yml up -d
	@# Start redis using the mapped port suggested by the script (if not already running)
	@if [ -z "$(docker ps -q -f name=soma-redis)" ]; then \
	  # parse chosen redis port from override
	  REDIS_PORT=$(awk '/soma-redis/ {p=1} p && /ports:/ {getline; print; exit}' infra/temporal/docker-compose.override.ports.yml | sed -E 's/\s*- "?([0-9]+):.*"?/\1/' ); \
	  docker run -d --name soma-redis --network somaagenthub-network --restart unless-stopped -p $${REDIS_PORT}:6379 redis:7-alpine || true; \
	fi
	@echo "Local infra started: Temporal + Redis (use the override file for docker-compose)"
	@echo "Local infra started: Temporal + Redis"


.PHONY: dev-start-services
dev-start-services:
	@echo "Dev service start helper (prints example commands)."
	@echo "Start Orchestrator:"
	@echo "  export TEMPORAL_HOST=localhost:7237"
	@echo "  export PYTHONPATH=$(pwd)/services/orchestrator"
	@echo "  ./.venv/bin/python -m uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port 60002"
	@echo
	@echo "Start Gateway:"
	@echo "  export SOMAGENT_GATEWAY_JWT_SECRET=dev-secret"
	@echo "  export SOMAGENT_GATEWAY_REDIS_URL=redis://localhost:6380/0"
	@echo "  export SOMAGENT_GATEWAY_ORCHESTRATOR_URL=http://localhost:60002"
	@echo "  export PYTHONPATH=$(pwd)/services/gateway-api"
	@echo "  ./.venv/bin/python -m uvicorn --app-dir services/gateway-api app.main:app --host 0.0.0.0 --port 60010"

airflow-build:
	@docker build -t somagent/airflow-service:dev -f services/airflow-service/Dockerfile .

airflow-up: airflow-build dev-network
	@docker compose -f infra/airflow/docker-compose.yml up -d
	@echo "Airflow webserver available at http://localhost:8081"

airflow-down:
	@docker compose -f infra/airflow/docker-compose.yml down --remove-orphans

flink-build:
	@docker build -t somagent/flink-service:dev -f services/flink-service/Dockerfile services/flink-service

flink-up: flink-build dev-network
	@docker compose -f infra/flink/docker-compose.yml up -d
	@echo "Flink dashboard available at http://localhost:8082"

flink-down:
	@docker compose -f infra/flink/docker-compose.yml down --remove-orphans


# Build images
images: build-gateway build-orchestrator build-identity

build-gateway:
	@echo "Building gateway image: $(IMG_GATEWAY)"
	docker build -t $(IMG_GATEWAY) services/gateway-api

build-orchestrator:
	@echo "Building orchestrator image: $(IMG_ORCH)"
	docker build -t $(IMG_ORCH) services/orchestrator

build-identity:
	@echo "Building identity image: $(IMG_ID)"
	docker build -t $(IMG_ID) services/identity-service

# Push images
push:
	docker push $(IMG_GATEWAY)
	docker push $(IMG_ORCH)
	docker push $(IMG_ID)

# Kubernetes deploy
deploy:
	bash scripts/deploy.sh

status:
	kubectl get pods -n $(NAMESPACE)
	kubectl get svc -n $(NAMESPACE)

pf-gateway:
	kubectl -n $(NAMESPACE) port-forward svc/gateway-api 8080:8080

pf-prom:
	kubectl -n $(OBS_NS) port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090

logs-orch:
	kubectl logs -f -n $(NAMESPACE) -l app=orchestrator --tail=200

# Tests
# Ensure Gateway (and Orchestrator) are reachable for these

test-int:
	pytest -q tests/integration/test_workflows.py::test_start_session_via_gateway

# E2E test hits Gateway and polls Orchestrator
# Optionally override E2E_GATEWAY_URL and E2E_ORCHESTRATOR_URL

test-e2e:
	pytest -q tests/e2e/test_gateway_orchestrator_e2e.py
