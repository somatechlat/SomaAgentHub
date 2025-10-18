#!/usr/bin/env bash
set -euo pipefail

# Remove resources created by run-sample-session.sh.

NAMESPACE=${VOLCANO_NAMESPACE:-soma-agent-hub}
DELETE_QUEUE=${DELETE_QUEUE:-false}

function delete_resource() {
  local kind=$1
  local name=$2
  kubectl delete "${kind}" "${name}" -n "${NAMESPACE}" --ignore-not-found >/dev/null 2>&1 || true
  echo "[volcano] Deleted ${kind}/${name} in namespace ${NAMESPACE} (if it existed)."
}

delete_resource job session-sample
delete_resource podgroup session-sample

if [[ "${DELETE_QUEUE}" == "true" ]]; then
  kubectl delete queue interactive --ignore-not-found >/dev/null 2>&1 || true
  echo "[volcano] Deleted queue/interactive (cluster-scoped)."
fi

echo "Cleanup complete."