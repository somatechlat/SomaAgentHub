#!/usr/bin/env bash
set -euo pipefail

# Quick development deployment script
# Builds images, updates Helm values, and deploys to Kind cluster

REGISTRY="ghcr.io/somatechlat"
TAG=$(git rev-parse --short HEAD)

echo "🚀 SomaAgent Quick Deploy - Tag: ${TAG}"

# 1. Build and push images (if registry is available)
echo "📦 Building images..."
./scripts/build_and_push.sh "$REGISTRY" "$TAG"

# 2. Update Helm values with new tag
echo "📝 Updating Helm values..."
sed -i.bak "s|ghcr.io/somatechlat/soma-.*:latest|ghcr.io/somatechlat/soma-jobs:${TAG}|g" k8s/helm/soma-agent/values.yaml

# 3. Deploy to Kind cluster
echo "🎯 Deploying to Kubernetes..."
if ! kind get clusters | grep -q soma-agent; then
    echo "Creating Kind cluster..."
    kind create cluster --name soma-agent
fi

# Set kubectl context
kubectl config use-context kind-soma-agent

# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Deploy with Helm
helm upgrade --install soma-agent ./k8s/helm/soma-agent \
    --namespace soma-agent \
    --create-namespace \
    --set global.imageTag="$TAG" \
    --wait \
    --timeout=300s

# 4. Wait for deployment
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=soma-agent \
    -n soma-agent --timeout=300s

# 5. Show status
echo "📊 Deployment Status:"
kubectl get pods -n soma-agent
kubectl get svc -n soma-agent

echo ""
echo "✅ Deployment complete!"
echo "🔗 Access services via port-forward:"
echo "  kubectl port-forward -n soma-agent svc/jobs 8000:8000"
echo "  kubectl port-forward -n soma-agent svc/memory-gateway 9696:9696"
echo "  kubectl port-forward -n soma-agent svc/orchestrator 8002:8002"