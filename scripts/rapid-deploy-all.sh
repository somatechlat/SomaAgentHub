#!/bin/bash
# Simple deployment script for SomaAgent platform
# Uses Helm to install/upgrade the entire chart in one step.

set -e

CHART_DIR="./k8s/helm/soma-agent"
RELEASE_NAME="soma-agent-hub"   # renamed from soma-agent
NAMESPACE="soma-agent-hub"      # renamed from soma-agent
IMAGE_TAG="029a130"

# Create namespace if it does not exist
kubectl get namespace $NAMESPACE >/dev/null 2>&1 || kubectl create namespace $NAMESPACE

# Deploy or upgrade the release
helm upgrade --install $RELEASE_NAME $CHART_DIR \
    --namespace $NAMESPACE \
    --set global.imageTag=$IMAGE_TAG \
    --wait \
    --timeout 5m

echo "✅ Deployment completed. Checking pod status..."
kubectl get pods -n $NAMESPACE