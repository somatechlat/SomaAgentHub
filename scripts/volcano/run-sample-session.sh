#!/usr/bin/env bash
set -euo pipefail

# Launch the sample session PodGroup/Job manifest and capture runtime artifacts.
# Required: kubectl access to the target cluster and the Volcano CRDs installed.

NAMESPACE=${VOLCANO_NAMESPACE:-soma-agent-hub}
ARTIFACTS_DIR=${ARTIFACTS_DIR:-$(pwd)/artifacts}
TIMEOUT_SECONDS=${VOLCANO_SAMPLE_TIMEOUT_SECONDS:-300}

mkdir -p "${ARTIFACTS_DIR}"

if ! kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
  echo "[volcano] Creating namespace ${NAMESPACE}..."
  kubectl create namespace "${NAMESPACE}" >/dev/null
fi

echo "[volcano] Applying queue definitions..."
kubectl apply -f infra/k8s/local/volcano/queues.yaml >/dev/null

echo "[volcano] Resetting prior sample resources (if any)..."
kubectl delete job session-sample -n "${NAMESPACE}" --ignore-not-found >/dev/null 2>&1 || true
kubectl delete podgroup session-sample -n "${NAMESPACE}" --ignore-not-found >/dev/null 2>&1 || true

echo "[volcano] Submitting sample session PodGroup + Job..."
kubectl apply -f infra/k8s/local/volcano/sample-session-job.yaml -n "${NAMESPACE}"

echo "[volcano] Waiting for job completion (timeout: ${TIMEOUT_SECONDS}s)..."
kubectl wait --for=condition=complete job/session-sample -n "${NAMESPACE}" --timeout="${TIMEOUT_SECONDS}s"

PG_OUTPUT="${ARTIFACTS_DIR}/session-podgroup.yaml"
JOB_OUTPUT="${ARTIFACTS_DIR}/session-job.yaml"
LOG_OUTPUT="${ARTIFACTS_DIR}/session-job.log"

kubectl get podgroup session-sample -n "${NAMESPACE}" -o yaml > "${PG_OUTPUT}"
kubectl get job session-sample -n "${NAMESPACE}" -o yaml > "${JOB_OUTPUT}"
kubectl logs job/session-sample -n "${NAMESPACE}" > "${LOG_OUTPUT}"

echo "[volcano] Artifacts stored in ${ARTIFACTS_DIR}:"
ls -1 "${ARTIFACTS_DIR}" | sed 's/^/  - /'

echo "[volcano] Sample session job completed successfully."
