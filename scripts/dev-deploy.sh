#!/usr/bin/env bash
set -euo pipefail

# Quick development deployment script
# Builds images, updates Helm values, and deploys to Kind cluster

REGISTRY="${1:-${REGISTRY:-ghcr.io/somatechlat}}"
TAG="${2:-${TAG:-$(git rev-parse --short HEAD)}}"

echo "🚀 SomaAgent Quick Deploy"
echo "   Registry: ${REGISTRY}"
echo "   Tag: ${TAG}"

# 1. Ensure Kind cluster exists before building images
if ! kind get clusters | grep -q "soma-agent-hub"; then
    echo "Creating Kind cluster..."
    kind create cluster --name soma-agent-hub
fi

# 2. Build and push images (if registry is available)
echo "📦 Building images..."
./scripts/build_and_push.sh "$REGISTRY" "$TAG"

# 3. Update Helm values with new tag
echo "📝 Updating Helm values..."
sed -i.bak "s|ghcr.io/somatechlat/soma-.*:latest|${REGISTRY}/soma-jobs:${TAG}|g" k8s/helm/soma-agent/values.yaml

# 4. Deploy to Kind cluster
echo "🎯 Deploying to Kubernetes..."
kubectl config use-context kind-soma-agent-hub

# Apply namespace (updated file already reflects new name)
kubectl apply -f k8s/namespace.yaml

# Deploy with Helm using new release name and namespace
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
    --namespace soma-agent-hub \
    --create-namespace \
    --set global.imageTag="$TAG" \
    --wait \
    --timeout=300s

# 5. Wait for pods
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=soma-agent-hub \
    -n soma-agent-hub --timeout=300s

# 6. Show status
echo "📊 Deployment Status:"
kubectl get pods -n soma-agent-hub
kubectl get svc -n soma-agent-hub

echo ""
echo "✅ Deployment complete!"
echo "🔗 Access services via port-forward:"
echo "  kubectl port-forward -n soma-agent-hub svc/jobs 8000:8000"
echo "  kubectl port-forward -n soma-agent-hub svc/memory-gateway 9696:9696"
echo "  kubectl port-forward -n soma-agent-hub svc/orchestrator 8002:8002"