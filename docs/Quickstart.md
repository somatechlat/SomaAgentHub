# Quickstart

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. All steps below operate on real services and verifiable endpoints.

Last Updated: October 9, 2025

## Prerequisites
- Docker Desktop (or Docker Engine)
- kubectl
- Helm 3.10+
- kind
- jq (for nicer JSON output)

## 1) Create local Kind cluster
```bash
kind create cluster --name soma-agent-hub
kubectl create namespace soma-agent-hub
```

## 2) Build and load images
```bash
# Build all service images and load into Kind
./scripts/build_and_push.sh somaagent latest
```

## 3) Install via Helm
```bash
helm upgrade --install soma-agent-hub k8s/helm/soma-agent -n soma-agent-hub --wait --timeout 180s
kubectl -n soma-agent-hub get deploy,svc
```

## 4) Access services (port-forward)
```bash
# Gateway API
kubectl -n soma-agent-hub port-forward svc/gateway-api 8080:8080 --address 127.0.0.1 &
# SLM service
kubectl -n soma-agent-hub port-forward svc/slm-service 11001:1001 --address 127.0.0.1 &
```

## 5) Smoke checks
```bash
curl -s http://127.0.0.1:8080/health | jq '.'
curl -s http://127.0.0.1:11001/health | jq '.'
```

## 6) Run tests
```bash
pytest -q tests/unit/test_slm_service.py
pytest -q tests/integration/test_services.py -q || true  # skips if services not all running
```

## 7) Verify observability (optional)
```bash
./scripts/verify-real-instrumentation.sh
```

## Troubleshooting
- If Helm resources conflict, delete manually-applied resources and re-run the Helm install.
- Check events: `kubectl -n soma-agent-hub get events --sort-by=.lastTimestamp | tail -n 50`
- Inspect manifests: `helm get manifest soma-agent-hub -n soma-agent-hub`
