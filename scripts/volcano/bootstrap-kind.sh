#!/usr/bin/env bash
set -euo pipefail

# Create a local kind cluster and install Volcano scheduler components.
# This script prepares the sandbox environment referenced in the Volcano integration roadmap.

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is required but not installed." >&2
  exit 1
fi

if ! command -v helm >/dev/null 2>&1; then
  echo "helm is required but not installed." >&2
  exit 1
fi

CLUSTER_NAME=${CLUSTER_NAME:-soma-volcano}
K8S_VERSION=${K8S_VERSION:-v1.29.4}
NAMESPACE=${NAMESPACE:-volcano-system}
VOLCANO_VERSION=${VOLCANO_VERSION:-1.9.0}

KIND_CFG=$(mktemp)
cat >"${KIND_CFG}" <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    image: "kindest/node:${K8S_VERSION}"
  - role: worker
    image: "kindest/node:${K8S_VERSION}"
  - role: worker
    image: "kindest/node:${K8S_VERSION}"
EOF

if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Creating kind cluster ${CLUSTER_NAME}..."
  kind create cluster --name "${CLUSTER_NAME}" --config "${KIND_CFG}"
else
  echo "Cluster ${CLUSTER_NAME} already exists; skipping creation."
fi

rm -f "${KIND_CFG}"

kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

helm repo add volcano https://volcano-sh.github.io/helm-charts >/dev/null
helm repo update >/dev/null

helm upgrade --install volcano volcano/volcano \
  --namespace "${NAMESPACE}" \
  --version "${VOLCANO_VERSION}" \
  --set controller.image.tag="v${VOLCANO_VERSION}" \
  --set scheduler.image.tag="v${VOLCANO_VERSION}" \
  --set admission.image.tag="v${VOLCANO_VERSION}" \
  --wait

echo "Volcano components installed in namespace ${NAMESPACE}."

echo "Validating deployment..."
kubectl get pods -n "${NAMESPACE}"

cat <<'EOT'
Next steps:
  1. Apply queue and PodGroup manifests under infra/k8s/local/volcano/.
  2. Point orchestrator feature flag ENABLE_VOLCANO_SCHEDULER=true when ready to test.
  3. Deploy ServiceMonitors to scrape Volcano metrics.
EOT
