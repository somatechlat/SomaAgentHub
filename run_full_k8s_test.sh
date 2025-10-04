#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Full Kubernetes deployment + test run for Soma Agent (one‑shot)
# ------------------------------------------------------------

# 0. Re‑create Kind cluster (clean start)
echo "Deleting any existing Kind cluster..."
kind delete cluster --name soma-agent || true

echo "Creating Kind cluster..."
kind create cluster --name soma-agent

# Export kubeconfig for this cluster
export KUBECONFIG="$HOME/.kube/config"
# Save the generated config (kind writes to stdout)
kind get kubeconfig --name soma-agent > "$KUBECONFIG"

# 1. (Kind provides its own CNI – no need for Flannel)
# echo "Applying Flannel CNI..."
# kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml --validate=false

# 2. Apply Kind hostPath StorageClass (required for Kafka PVCs)
echo "Applying Kind hostPath StorageClass..."
kubectl apply -f ./k8s/kind-storageclass.yaml

# 3. Deploy the Helm chart (includes Kafka KRaft via Bitnami dependency)
echo "Deploying Soma‑Agent Helm chart..."
helm upgrade --install soma-agent ./k8s/helm/soma-agent \
  --namespace soma-agent \
  --create-namespace

# 4. Wait for the control‑plane node to become Ready (max 180s)
echo "Waiting for node to be Ready..."
kubectl wait --for=condition=Ready node/soma-agent-control-plane --timeout=180s

# 5. Wait for all pods in the namespace to be Ready (max 5m)
# Use a broader label selector – all pods created by the chart have the part‑of label
echo "Waiting for all pods in namespace 'soma-agent' to be Ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=soma-agent \
  -n soma-agent --timeout=300s

# 6. Install combined Python requirements (CI already does this, but ensure locally)
if [ -f requirements-dev.txt ]; then
  echo "Installing dev requirements..."
  python -m pip install -q -r requirements-dev.txt
fi
# Combine all service requirements into one file and install
find services -name requirements.txt -exec cat {} + > combined-requirements.txt
python -m pip install -q -r combined-requirements.txt

# 7. Run the test suite
echo "Running pytest..."
pytest || { echo "Tests failed – see above for details"; exit 1; }

echo "All steps completed successfully!"
