#!/usr/bin/env bash
# -------------------------------------------------------------------------
# generate-mtls.sh – create a self‑signed certificate/key pair and a Kubernetes
# Secret (`soma-mtls`) that the Helm chart will mount into every pod at
# /etc/mtls.
#
# Usage:
#   ./scripts/generate-mtls.sh   # creates the secret in the current context
#
# Requirements:
#   - openssl (available on macOS/Linux)
#   - kubectl configured for the target cluster/namespace
# -------------------------------------------------------------------------

set -euo pipefail

# -------------------------------------------------------------------------
# Configuration (adjust if you need different values)
# -------------------------------------------------------------------------
NAMESPACE="${HELM_RELEASE_NAMESPACE:-soma-agent-hub}"   # Helm release namespace
SECRET_NAME="soma-mtls"
CERT_SUBJ="/CN=soma-agent.local"
DAYS_VALID=3650   # 10 years
KEY_SIZE=2048

# Temp files
TMPDIR=$(mktemp -d)
CRT_FILE="${TMPDIR}/tls.crt"
KEY_FILE="${TMPDIR}/tls.key"

echo "🔐 Generating a self‑signed certificate for mTLS..."
openssl req -x509 -nodes -newkey rsa:${KEY_SIZE} \
  -days "${DAYS_VALID}" \
  -subj "${CERT_SUBJ}" \
  -keyout "${KEY_FILE}" \
  -out "${CRT_FILE}" \
  -sha256

echo "📦 Creating/updating Kubernetes secret '${SECRET_NAME}' in namespace '${NAMESPACE}'..."
kubectl create secret generic "${SECRET_NAME}" \
  --namespace "${NAMESPACE}" \
  --from-file=tls.crt="${CRT_FILE}" \
  --from-file=tls.key="${KEY_FILE}" \
  --dry-run=client -o yaml | kubectl apply -f -

# Clean up
rm -rf "${TMPDIR}"

echo "✅ Secret '${SECRET_NAME}' is ready. Helm will mount it at /etc/mtls."
echo "   You can now run:"
echo "       helm upgrade soma-agent-hub ./k8s/helm/soma-agent --namespace ${NAMESPACE}"
echo "   (or reinstall the chart) and all pods will start with mTLS enabled."