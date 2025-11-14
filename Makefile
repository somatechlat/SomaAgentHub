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
VAULT_ADDR ?= http://localhost:10030
VAULT_NAMESPACE ?= somaagent

# Image names
IMG_GATEWAY := $(REGISTRY)/gateway-api:$(TAG)
IMG_ORCH := $(REGISTRY)/orchestrator:$(TAG)
IMG_ID := $(REGISTRY)/identity-service:$(TAG)

# Default target
.DEFAULT_GOAL := help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PYTEST ?= $(PY) -m pytest

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
	@echo "  make test-pricing       Run pricing service unit tests"
	@echo "  make test-gateway       Run gateway wizard gating test"
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
	@if [ -z "$$(docker ps -q -f name=soma-redis)" ]; then \
		REDIS_PORT=$$(awk '/soma-redis/ {p=1} p && /ports:/ {getline; print; exit}' infra/temporal/docker-compose.override.ports.yml | sed -E 's/\s*- "?([0-9]+):.*"?/\1/'); \
		docker run -d --name soma-redis --network somaagenthub-network --restart unless-stopped -p "$${REDIS_PORT:-10005}:6379" redis:7-alpine; \
	fi
	@echo "Local infra started: Temporal + Redis"

.PHONY: select-free-ports
select-free-ports:
	./scripts/select_free_ports.sh

.PHONY: dev-start-services
dev-start-services:
	@echo "Starting core services in the background. Logs will be in the .logs/ directory."
	@pkill -f uvicorn || true
	@ORCHESTRATOR_PORT=$${ORCHESTRATOR_PORT:-10001}; \
	echo "Starting Orchestrator on port $${ORCHESTRATOR_PORT}..."; \
	(PORT=$${ORCHESTRATOR_PORT} TEMPORAL_HOST=localhost:7233 PYTHONPATH=$(pwd)/services/orchestrator ./.venv/bin/python -m uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port $${ORCHESTRATOR_PORT} > .logs/orchestrator.log 2>&1 &)
	
	@GATEWAY_PORT=$${GATEWAY_PORT:-10000}; \
	ORCHESTRATOR_PORT=$${ORCHESTRATOR_PORT:-10001}; \
	echo "Starting Gateway API on port $${GATEWAY_PORT}..."; \
	(PORT=$${GATEWAY_PORT} IDENTITY_SERVICE_URL=http://localhost:$${IDENTITY_SERVICE_PORT:-10002} SOMAGENT_GATEWAY_REDIS_URL=redis://localhost:6379/0 SOMAGENT_GATEWAY_ORCHESTRATOR_URL=http://localhost:$${ORCHESTRATOR_PORT} PYTHONPATH=$(pwd)/services/gateway-api ./.venv/bin/python -m uvicorn --app-dir services/gateway-api app.main:app --host 0.0.0.0 --port $${GATEWAY_PORT} > .logs/gateway-api.log 2>&1 &)
	
	@echo "Core services started. Use 'tail -f .logs/service-name.log' to see output."

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


.PHONY: build-changed dev-deploy deploy-region backup-databases restore-databases init-clickhouse run-migrations k8s-smoke port-forward-gateway generate-sbom scan-vulns rotate-secrets verify-observability

build-changed:
	./scripts/build-changed.sh $(REGISTRY) $(TAG)

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

.PHONY: docker-cluster-up docker-cluster-down

## Sprint 1 Development Targets
sprint-1-up:
	@echo "🚀 Starting Sprint 1 development..."
	docker-compose -f docker-compose.sprint1.yml up -d
	@sleep 5
	@echo "✅ Sprint 1 environment ready!"
	@echo "   Capsule Registry: http://localhost:8000"
	@echo "   Agent Spawner: http://localhost:8001"

sprint-1-down:
	@echo "🛑 Stopping Sprint 1..."
	docker-compose -f docker-compose.sprint1.yml down

sprint-1-logs:
	docker-compose -f docker-compose.sprint1.yml logs -f

sprint-1-test-capsule:
	@curl -s -X POST "http://localhost:8000/v1/capsules" \
		-G -d "capsule_id=$$(uuidgen)" \
		-d "version=1.0.0" \
		-d "type=static" \
		-d "manifest_yaml=apiVersion: v1\\nkind: ConfigMap\\nmetadata:\\n  name: test-capsule" \
		| jq .

sprint-1-test-agent:
	@curl -s -X POST "http://localhost:8001/v1/spawn" \
		-H "Content-Type: application/json" \
		-d '{"agent_type": "code-generator", "tenant_id": "550e8400-e29b-41d4-a716-446655440000", "user_id": "550e8400-e29b-41d4-a716-446655440001", "image": "soma-agent:latest", "execution_mode": "batch"}' \
		| jq .

docker-cluster-up:
	./scripts/docker-cluster.sh

docker-cluster-down:
	@echo "--> Stopping the Docker-based application cluster..."
	docker compose down

# ---------------------------------------------------------------------------
# Helm convenience targets (continue roadmap Sprint 2 – full CI/CD and observability)
# ---------------------------------------------------------------------------

## Render the Helm chart locally (useful for debugging)
helm-template:
	@echo "Rendering Helm chart..."
	helm template soma-agent-hub ./k8s/helm/soma-agent --namespace $(NAMESPACE)

## Run Helm tests (requires test hooks in the chart)
helm-test:
	@echo "Running Helm tests..."
	helm test soma-agent-hub --namespace $(NAMESPACE) || true

## Uninstall the Helm release
helm-uninstall:
	@echo "Uninstalling SomaAgentHub Helm release..."
	helm uninstall soma-agent-hub --namespace $(NAMESPACE) || true

# ---------------------------------------------------------------------------
# Helm targets
# ---------------------------------------------------------------------------

## Lint the Helm chart for syntax errors and best‑practice warnings.
helm-lint:
	@echo "Running helm lint on soma-agent chart..."
	@helm lint ./k8s/helm/soma-agent

## Upgrade (or install) the SomaAgentHub Helm release.
## Use the NAMESPACE variable to target a specific namespace (default: soma-agent-hub).
helm-upgrade:
	@echo "Installing/upgrading SomaAgentHub Helm release..."
	@helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
		--namespace $(NAMESPACE) --create-namespace \
		--set global.imageTag=$(shell git rev-parse --short HEAD) \
		--set global.namespace=$(NAMESPACE)

# ---------------------------------------------------------------------------
# Test targets
# ---------------------------------------------------------------------------

## Run the full test suite across all services.
## Installs any service‑specific requirements and executes pytest for each test directory.
test-all:
	@echo "Installing core development dependencies..."
	@python -m pip install --quiet -r requirements-dev.txt
	@echo "Running tests for all services..."
	@for svc in services/*; do \
		if [ -d $$svc/tests ]; then \
			echo "Installing dependencies for $$svc..."; \
			if [ -f $$svc/requirements.txt ]; then \
				python -m pip install --quiet -r $$svc/requirements.txt; \
			fi; \
			pytest -q $$svc/tests; \
		fi; \
	 done

.PHONY: test-pricing test-gateway
test-pricing:
	@echo "Running pricing-service tests (isolated)";
	OTEL_SDK_DISABLED=true $(PYTEST) -q services/pricing-service/tests

test-gateway:
	@echo "Running gateway wizard gating test (isolated)";
	OTEL_SDK_DISABLED=true $(PYTEST) -q services/gateway-api/tests/test_wizard_budget_gating.py::test_wizard_budget_block

.PHONY: dev-env
dev-env:
	./scripts/manage-cluster.sh

.PHONY: helm-install start-cluster stop-cluster
helm-install:
	helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent --namespace $(NAMESPACE) --create-namespace --set global.imageTag=$(shell git rev-parse --short HEAD) --set global.namespace=$(NAMESPACE)

start-cluster: stop-cluster
	@echo "--> Creating persistent Kind cluster..."
	kind create cluster --name soma-agent-hub --config=kind-cluster-persistent.yaml
	@echo "--> Applying persistent volume..."
	kubectl apply -f k8s/local/persistence.yaml
	@echo "--> Creating namespaces..."
	kubectl create namespace $(NAMESPACE) || true
	kubectl create namespace $(OBS_NS) || true
	@echo "--> Building changed images..."
	make build-changed
	@echo "--> Deploying application with Helm..."
	helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
		--namespace $(NAMESPACE) \
		-f ./k8s/helm/soma-agent/values.yaml \
		-f ./k8s/helm/soma-agent/values-dev.yaml \
		--set global.imageTag=$(TAG)

stop-cluster:
	@echo "--> Deleting existing Kind cluster to ensure a clean start..."
	kind delete cluster --name soma-agent-hub || true


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
	OTEL_SDK_DISABLED=true $(PYTEST) -q tests/integration

# ---------------------------------------------------------------------------
# Static analysis & quality gates
# ---------------------------------------------------------------------------
.PHONY: lint lint-fix type quality
lint:
	@echo "Running ruff lint checks..."
	@$(PY) -m ruff check .

lint-fix:
	@echo "Applying ruff autofixes..."
	@$(PY) -m ruff check --fix .

type:
	@echo "Running mypy type checks (focused scope for green baseline)..."
	@(cd services/gateway-api && ../../$(PY) -m mypy --follow-imports=skip app/wizard_engine.py app/api/dashboard.py app/core/context.py app/core/auth.py)

.PHONY: check
check: ## Run lint + type + focused tests with OTEL disabled
	@echo "Installing dev dependencies..."
	@$(PY) -m pip install -r requirements-dev.txt >/dev/null
	@echo "Running code quality checks (ruff + mypy)..."
	@$(MAKE) lint
	@$(MAKE) type
	@echo "Running unit tests (pricing, gateway) and integration tests..."
	@OTEL_SDK_DISABLED=true $(PYTEST) -q services/pricing-service/tests
	@OTEL_SDK_DISABLED=true $(PYTEST) -q services/gateway-api/tests
	@OTEL_SDK_DISABLED=true $(PYTEST) -q tests/integration
	@echo "All checks passed."

quality: lint type
	@echo "Quality gate completed (lint + type)."

# ---------------------------------------------------------------------------
# Mandatory formatting after each sprint
# ---------------------------------------------------------------------------
.PHONY: format format-check
format:  ## Run black and ruff formatting (mandatory after each sprint)
	@echo "Running mandatory formatting with black and ruff..."
	@$(PY) -m black services/ tests/ --line-length 88
	@$(PY) -m ruff format services/ tests/
	@echo "Formatting complete!"

format-check:  ## Check formatting without applying changes
	@echo "Checking formatting compliance..."
	@$(PY) -m black services/ tests/ --line-length 88 --check
	@$(PY) -m ruff format services/ tests/ --check
	@echo "All files properly formatted."

# E2E test hits Gateway and polls Orchestrator
# Optionally override E2E_GATEWAY_URL and E2E_ORCHESTRATOR_URL

test-e2e:
	pytest -q tests/e2e/test_gateway_orchestrator_e2e.py
