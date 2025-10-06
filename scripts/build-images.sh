#!/bin/bash
# Build all Docker images for SomaAgent services
# Sprint-6: Container build automation

set -e

REGISTRY="${DOCKER_REGISTRY:-somaagent}"
TAG="${IMAGE_TAG:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICES_DIR="$(cd "$SCRIPT_DIR/../services" && pwd)"

echo "🐳 Building SomaAgent Docker Images"
echo "==================================="
echo "Registry: $REGISTRY"
echo "Tag: $TAG"
echo ""

SERVICES=(
    "orchestrator"
    "gateway-api"
    "policy-engine"
    "identity-service"
    "somallm-provider"
    "analytics-service"
)

for service in "${SERVICES[@]}"; do
    echo "📦 Building $service..."

    build_dir="$service"
    if [[ "$service" == "somallm-provider" ]]; then
        build_dir="somallm-provider"
    fi
    
    docker build \
        -t "$REGISTRY/$service:$TAG" \
        -f "$SERVICES_DIR/$build_dir/Dockerfile" \
        "$SERVICES_DIR/$build_dir/"
    
    echo "   ✓ $REGISTRY/$service:$TAG"
    echo ""
done

echo "✅ All images built successfully!"
echo ""
echo "Images:"
docker images | grep "$REGISTRY" | head -6
echo ""
echo "To push to registry:"
echo "  docker push $REGISTRY/orchestrator:$TAG"
echo "  docker push $REGISTRY/gateway-api:$TAG"
echo "  docker push $REGISTRY/policy-engine:$TAG"
echo "  docker push $REGISTRY/identity-service:$TAG"
echo "  docker push $REGISTRY/somallm-provider:$TAG"
echo "  docker push $REGISTRY/analytics-service:$TAG"
echo ""
echo "Or run:"
echo "  ./scripts/push-images.sh"
echo ""
