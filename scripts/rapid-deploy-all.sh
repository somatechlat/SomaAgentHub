#!/bin/bash
# Rapid Multi-Service Deployment Script
# Deploy each service individually to bypass YAML parsing issues

set -e

echo "🚀 DEPLOYING ALL 12 SOMAAGENT SERVICES INDIVIDUALLY"

SERVICES=(
    "jobs"
    "memory-gateway" 
    "orchestrator"
    "policy-engine"
    "settings-service"
    "task-capsule-repo"
    "somallm-provider"
    "gateway-api"
    "identity-service"
    "constitution-service"
    "analytics-service"
    "billing-service"
)

for service in "${SERVICES[@]}"; do
    echo "⚡ Deploying $service..."
    
    # Generate deployment for this specific service
    helm template soma-agent ./k8s/helm/soma-agent --set global.imageTag=80e1d6f --namespace soma-agent | \
        grep -A 100 "name: $service" | \
        grep -B 100 "^---$" | \
        head -n -1 | \
        kubectl apply -f - || echo "❌ Failed to deploy $service"
    
    echo "✅ $service deployment attempted"
done

echo "🎉 ALL DEPLOYMENTS COMPLETED!"
echo "Checking status..."
kubectl get deployments -n soma-agent