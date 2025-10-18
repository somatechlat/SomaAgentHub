#!/usr/bin/env bash
set -euo pipefail

# Lightweight integration smoke for local Volcano validation.
# Steps:
# 1. Bootstrap kind + Volcano (if not present)
# 2. Apply queues and sample job
# 3. Wait for Job completion and fetch logs
# 4. Cleanup artifacts

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
QUEUE_MANIFEST="$ROOT/infra/k8s/local/volcano/queues.yaml"
SAMPLE_JOB="$ROOT/infra/k8s/local/volcano/sample-session-job.yaml"
BOOTSTRAP="$ROOT/scripts/volcano/bootstrap-kind.sh"
CLEANUP="$ROOT/scripts/volcano/cleanup-sample.sh"

NAMESPACE=${NAMESPACE:-soma-agent-hub}
CLUSTER_NAME=${CLUSTER_NAME:-soma-volcano}

if ! command -v kind >/dev/null 2>&1; then
  echo "kind CLI not found; please install kind to run this smoke test." >&2
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl not found; ensure kubectl is available in PATH." >&2
  exit 1
fi

# Bootstrap cluster + volcano if needed
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Bootstrapping kind cluster and installing Volcano via helm..."
  bash "$BOOTSTRAP"
else
  echo "Using existing kind cluster ${CLUSTER_NAME}."
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

# Create namespace
kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || kubectl create ns "$NAMESPACE"

# Apply queues
kubectl apply -f "$QUEUE_MANIFEST"

# Submit sample job
kubectl apply -f "$SAMPLE_JOB"

# Wait for job to start and then complete
JOB_NAME=$(yq e '.metadata.name' "$SAMPLE_JOB")

echo "Waiting for job $JOB_NAME to complete..."
kubectl wait --for=condition=complete --timeout=120s job/$JOB_NAME -n $NAMESPACE || true

# Collect logs
echo "Collecting job logs..."
kubectl logs job/$JOB_NAME -n $NAMESPACE || true

# Cleanup
if [ "${KEEP_ARTIFACTS:-false}" != "true" ]; then
  bash "$CLEANUP"
fi

echo "Integration smoke finished."
