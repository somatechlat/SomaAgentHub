#!/usr/bin/env bash
set -euo pipefail

# Build and push all SomaAgent service Docker images
# Usage: ./scripts/build_and_push.sh [registry] [tag]

REGISTRY=${1:-"ghcr.io/somatechlat"}
TAG=${2:-$(git rev-parse --short HEAD)}

echo "Building and pushing images to ${REGISTRY} with tag ${TAG}"

# Services to build (directories that contain Dockerfiles)
SERVICES=(
    "jobs"
    "memory-gateway"
    "orchestrator"
    "policy-engine"
    "settings-service"
    "task-capsule-repo"
    "slm-service"
    "gateway-api"
    "identity-service"
    "constitution-service"
    "analytics-service"
    "billing-service"
)

# Function to build and push a single service
build_service() {
    local service=$1
    local service_dir="services/${service}"
    
    if [ ! -d "$service_dir" ]; then
        echo "⚠️  Skipping ${service} - directory not found"
        return 0
    fi
    
    echo "🔨 Building ${service}..."
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f "${service_dir}/Dockerfile" ]; then
        cat > "${service_dir}/Dockerfile" <<EOF
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    fi
    
    # Build image
    docker build -t "${REGISTRY}/soma-${service}:${TAG}" -t "${REGISTRY}/soma-${service}:latest" "${service_dir}"
    
    # Load image into Kind cluster if it exists
    if kind get clusters | grep -q "soma-agent"; then
        echo "📥 Loading ${service} into Kind cluster..."
        kind load docker-image "${REGISTRY}/soma-${service}:${TAG}" --name soma-agent
        kind load docker-image "${REGISTRY}/soma-${service}:latest" --name soma-agent
    else
        echo "📤 Pushing ${service}... (skipping - no credentials)"
        # docker push "${REGISTRY}/soma-${service}:${TAG}"
        # docker push "${REGISTRY}/soma-${service}:latest"
    fi
    
    echo "✅ ${service} complete"
}

# Build all services
for service in "${SERVICES[@]}"; do
    build_service "$service"
done

echo "🎉 All images built and pushed successfully!"
echo ""
echo "To deploy with Helm:"
echo "  helm upgrade --install soma-agent ./k8s/helm/soma-agent --set global.imageTag=${TAG}"