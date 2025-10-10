# Simple, explicit Makefile to orchestrate build, deploy, and tests
# Usage: `make <target>`

# Registry configuration
REGISTRY ?= somaagent
TAG ?= latest
NAMESPACE ?= soma-agent-hub
OBS_NS ?= observability

# Canonical tool parameters
DEV_DEPLOY_REGISTRY ?= ghcr.io/somatechlat
DEV_DEPLOY_TAG ?= $(shell git rev-parse --short HEAD)
REGION ?= us-west-2
ACTION ?= plan
WORKSPACE ?= production
BACKUP_DIR ?= /tmp/somaagent-backups
S3_BUCKET ?= s3://somaagent-backups
RESTORE_TIMESTAMP ?=
CLICKHOUSE_HOST ?= localhost
CLICKHOUSE_NATIVE_PORT ?= 9000
CLICKHOUSE_HTTP_PORT ?= 8123
CLICKHOUSE_USER ?= default
CLICKHOUSE_PASSWORD ?=
LOAD_SAMPLE_DATA ?= false
POSTGRES_HOST ?= localhost
POSTGRES_PORT ?= 5432
POSTGRES_DB ?= somaagent
POSTGRES_USER ?= postgres
POSTGRES_PASSWORD ?=
TEST_NAMESPACE ?= soma-agent-hub
TEST_TIMEOUT ?= 300
LOCAL_PORT ?= 8080
REMOTE_PORT ?= 8080
SBOM_DIR ?= sbom
SCAN_DIR ?= security-scans
SEVERITY ?= --severity CRITICAL,HIGH,MEDIUM
TRIVY_FORMAT ?= table
VAULT_ADDR ?= http://localhost:8200
VAULT_NAMESPACE ?= somaagent

# Image names
IMG_GATEWAY := $(REGISTRY)/gateway-api:$(TAG)
IMG_ORCH := $(REGISTRY)/orchestrator:$(TAG)
IMG_ID := $(REGISTRY)/identity-service:$(TAG)

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make images            Build gateway/orch/identity images"
	@echo "  make push              Push gateway/orch/identity images"
	@echo "  make build-all         Build & load all service images"
	@echo "  make dev-deploy        Build + deploy to local Kind"
	@echo "  make deploy            Alias for dev-deploy"
	@echo "  make deploy-region     Terraform apply/plan/destroy"
	@echo "  make backup-databases  Snapshot ClickHouse/Postgres/Redis"
	@echo "  make restore-databases RESTORE_TIMESTAMP=..."
	@echo "  make init-clickhouse   Apply ClickHouse schema & seeds"
	@echo "  make run-migrations    Run ClickHouse & Postgres migrations"
	@echo "  make select-free-ports Generate Temporal port overrides"
	@echo "  make status            Show pods and services"
	@echo "  make pf-gateway        Port-forward gateway 8080"
	@echo "  make pf-prom           Port-forward Prometheus 9090"
	@echo "  make test-int          Run gateway integration test"
	@echo "  make test-e2e          Run gateway→orchestrator e2e test"
	@echo "  make k8s-smoke         Run Kubernetes smoke tests"
	@echo "  make logs-orch         Tail orchestrator logs"
	@echo "  make airflow-up        Build & launch local Airflow stack"
	@echo "  make airflow-down      Stop local Airflow stack"
	@echo "  make flink-up          Build & launch local Flink stack"
	@echo "  make flink-down        Stop local Flink stack"
	@echo "  make port-forward-gateway LOCAL=8080 REMOTE=8080"
	@echo "  make generate-sbom     Produce Syft SBOMs"
	@echo "  make scan-vulns        Run Trivy image scans"
	@echo "  make rotate-secrets    Rotate Vault-managed secrets"
	@echo "  make verify-observability Validate OpenTelemetry wiring"
	@echo "  make helm-install       Helm upgrade/install soma-agent-hub"
	@echo "  make start-cluster      Kind + Helm deploy + smoke"

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

.PHONY: select-free-ports
select-free-ports:
	./scripts/select_free_ports.sh

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


.PHONY: build-all dev-deploy deploy-region backup-databases restore-databases init-clickhouse run-migrations k8s-smoke port-forward-gateway generate-sbom scan-vulns rotate-secrets verify-observability

build-all:
	REGISTRY=$(REGISTRY) TAG=$(TAG) ./scripts/build_and_push.sh $(REGISTRY) $(TAG)

dev-deploy:
	REGISTRY=$(DEV_DEPLOY_REGISTRY) TAG=$(DEV_DEPLOY_TAG) ./scripts/dev-deploy.sh

deploy-region:
	WORKSPACE=$(WORKSPACE) ./scripts/deploy-region.sh $(REGION) $(ACTION)

backup-databases:
	BACKUP_DIR=$(BACKUP_DIR) S3_BUCKET=$(S3_BUCKET) CLICKHOUSE_HOST=$(CLICKHOUSE_HOST) CLICKHOUSE_NATIVE_PORT=$(CLICKHOUSE_NATIVE_PORT) CLICKHOUSE_HTTP_PORT=$(CLICKHOUSE_HTTP_PORT) CLICKHOUSE_USER=$(CLICKHOUSE_USER) CLICKHOUSE_PASSWORD=$(CLICKHOUSE_PASSWORD) POSTGRES_HOST=$(POSTGRES_HOST) POSTGRES_PORT=$(POSTGRES_PORT) POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) ./scripts/backup-databases.sh

restore-databases:
	@if [ -z "$(RESTORE_TIMESTAMP)" ]; then echo "RESTORE_TIMESTAMP is required"; exit 1; fi
	S3_BUCKET=$(S3_BUCKET) CLICKHOUSE_HOST=$(CLICKHOUSE_HOST) CLICKHOUSE_NATIVE_PORT=$(CLICKHOUSE_NATIVE_PORT) CLICKHOUSE_HTTP_PORT=$(CLICKHOUSE_HTTP_PORT) CLICKHOUSE_USER=$(CLICKHOUSE_USER) CLICKHOUSE_PASSWORD=$(CLICKHOUSE_PASSWORD) POSTGRES_HOST=$(POSTGRES_HOST) POSTGRES_PORT=$(POSTGRES_PORT) POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) ./scripts/restore-databases.sh $(RESTORE_TIMESTAMP)

init-clickhouse:
	CLICKHOUSE_HOST=$(CLICKHOUSE_HOST) CLICKHOUSE_PORT=$(CLICKHOUSE_NATIVE_PORT) CLICKHOUSE_USER=$(CLICKHOUSE_USER) CLICKHOUSE_PASSWORD=$(CLICKHOUSE_PASSWORD) LOAD_SAMPLE_DATA=$(LOAD_SAMPLE_DATA) ./scripts/init-clickhouse.sh

run-migrations:
	CLICKHOUSE_HOST=$(CLICKHOUSE_HOST) CLICKHOUSE_PORT=$(CLICKHOUSE_HTTP_PORT) POSTGRES_HOST=$(POSTGRES_HOST) POSTGRES_PORT=$(POSTGRES_PORT) POSTGRES_DB=$(POSTGRES_DB) POSTGRES_USER=$(POSTGRES_USER) POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) ./scripts/run-migrations.sh

k8s-smoke:
	./scripts/integration-test.sh $(TEST_NAMESPACE) $(TEST_TIMEOUT)

port-forward-gateway:
	kubectl -n $(NAMESPACE) port-forward svc/gateway-api $(LOCAL_PORT):$(REMOTE_PORT)

generate-sbom:
	./scripts/generate-sbom.sh

scan-vulns:
	./scripts/scan-vulnerabilities.sh $(SEVERITY) $(TRIVY_FORMAT)

rotate-secrets:
	VAULT_ADDR=$(VAULT_ADDR) VAULT_NAMESPACE=$(VAULT_NAMESPACE) ./scripts/rotate-secrets.sh

verify-observability:
	./scripts/verify-instrumentation.sh

.PHONY: helm-install start-cluster
helm-install:
	helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent --namespace $(NAMESPACE) --create-namespace --set global.imageTag=$(TAG) --set global.namespace=$(NAMESPACE)

start-cluster:
	kind create cluster --name soma-agent-hub || true
	kubectl create namespace $(NAMESPACE) || true
	kubectl create namespace $(OBS_NS) || true
	make build-all
	make helm-install


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
	docker push $(IMG_GATEWAY)
	docker push $(IMG_ORCH)
	docker push $(IMG_ID)

# Kubernetes deploy
deploy: dev-deploy

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
