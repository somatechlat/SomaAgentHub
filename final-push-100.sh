#!/bin/bash

# SomaAgent Final Push to 100% Operational Status
# This script will systematically fix and deploy all 12 services

set -e

echo "🚀 SomaAgent Final Push to 100% Operational Status"
echo "=================================================="

cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaagent

# Step 1: Force rebuild all problematic services without cache
echo "📦 Step 1: Rebuilding all services without cache..."

services=("gateway-api" "constitution-service" "identity-service" "policy-engine" "settings-service" "slm-service" "task-capsule-repo" "billing-service")

for service in "${services[@]}"; do
    echo "Building $service..."
    docker build --no-cache -t somaagent/$service:latest -f services/$service/Dockerfile services/$service
done

# Step 2: Load all images into kind cluster
echo "📤 Step 2: Loading all images into kind cluster..."
images=""
for service in "${services[@]}"; do
    images="$images somaagent/$service:latest"
done

kind load docker-image --name soma-agent $images somaagent/jobs:latest

# Step 3: Restart all deployments
echo "🔄 Step 3: Restarting all deployments..."
deployments=""
for service in "${services[@]}"; do
    deployments="$deployments deployment/$service"
done

kubectl rollout restart $deployments deployment/jobs -n soma-agent

# Step 4: Wait for deployments to stabilize
echo "⏳ Step 4: Waiting for deployments to stabilize..."
sleep 90

# Step 5: Check final status
echo "✅ Step 5: Checking final status..."
kubectl get pods -n soma-agent

echo ""
echo "🎯 Running final health check..."
python3 comprehensive-health-check.py

echo ""
echo "🎉 SomaAgent Final Deployment Complete!"