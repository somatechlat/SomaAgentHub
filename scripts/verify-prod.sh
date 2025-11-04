#!/usr/bin/env bash
# -------------------------------------------------------------------------
# verify-prod.sh – end‑to‑end verification that the production‑grade stack
# deploys correctly with mTLS and ServiceMonitors enabled.
# -------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------
# 1. Optional Docker image build
# ---------------------------------------------------------------------
# Some environments (e.g., CI) may not have Docker available. In that case we
# fall back to using the latest images from the public registry. If Docker is
# running we build the images with the tag "dev" so the Helm chart can pick them
# up via `global.imageTag`.
if docker info > /dev/null 2>&1; then
  echo "🔧 Docker daemon detected – building local images (tag=dev)…"
  make images TAG=dev REGISTRY=somaagent
  IMAGE_TAG=dev
else
  echo "⚠️ Docker daemon not available – skipping image build and using public images."
  IMAGE_TAG=latest
fi

# ---------------------------------------------------------------------
# 2. Generate a self‑signed certificate for mTLS (creates a secret)
# ---------------------------------------------------------------------
kubectl delete secret soma-mtls -n soma-agent-hub --ignore-not-found
CERT_SUBJ="/CN=soma-agent.local"
DAYS_VALID=3650
KEY_SIZE=2048
TMPDIR=$(mktemp -d)
CRT_FILE="${TMPDIR}/tls.crt"
KEY_FILE="${TMPDIR}/tls.key"
openssl req -x509 -nodes -newkey rsa:${KEY_SIZE} \
  -days "${DAYS_VALID}" \
  -subj "${CERT_SUBJ}" \
  -keyout "${KEY_FILE}" \
  -out "${CRT_FILE}" \
  -sha256
TLS_CRT=$(cat "${CRT_FILE}" | base64 | tr -d '\n')
TLS_KEY=$(cat "${KEY_FILE}" | base64 | tr -d '\n')
rm -rf "${TMPDIR}"

# 2. Clean up any previous Helm release that used the old name "soma-agent"
# This removes all resources (NetworkPolicies, PDBs, ServiceMonitors, etc.)
helm uninstall soma-agent -n soma-agent-hub --ignore-not-found || true
# Ensure the namespace is clean of leftover resources that might not be tracked by Helm
kubectl delete all --all -n soma-agent-hub --ignore-not-found || true
kubectl delete pdb --all -n soma-agent-hub --ignore-not-found || true
kubectl delete servicemonitor --all -n soma-agent-hub --ignore-not-found || true
kubectl delete networkpolicy --all -n soma-agent-hub --ignore-not-found || true

# Deploy/upgrade the Helm chart with the correct release name
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub --create-namespace \
  --set mtls.enabled=true \
  --set mtls.tlsCrt="${TLS_CRT}" \
  --set mtls.tlsKey="${TLS_KEY}" \
  --set global.imageTag="${IMAGE_TAG}"

# 3. Wait for all pods to become ready (timeout 180 s)
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=soma-agent-hub \
  --namespace soma-agent-hub --timeout=180s

# 4. Verify health endpoints for core services
services=(gateway-api orchestrator identity-service policy-engine)
for svc in "${services[@]}"; do
  pod=$(kubectl get pod -l app=${svc} -n soma-agent-hub -o jsonpath='{.items[0].metadata.name}')
  echo "🔎 Checking ${svc} health …"
  # Map service name to port defined in values.yaml
  case "${svc}" in
    gateway-api)   port=10000 ;;
    orchestrator)  port=10001 ;;
    identity-service) port=10002 ;;
    policy-engine) port=10003 ;;
    *) port=0 ;;
  esac
  kubectl exec -n soma-agent-hub "${pod}" -- curl -s http://localhost:${port}/ready || exit 1
done

echo "✅ All services are healthy and mTLS is enabled."