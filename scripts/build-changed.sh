#!/bin/bash
#
# Smart build script for SomaAgentHub
# Builds only the Docker images for services that have changed.
#
set -e

REGISTRY=${1:-"somaagent"}
TAG_PREFIX=${2:-"dev"}
GIT_HASH=$(git rev-parse --short HEAD)
TAG="${TAG_PREFIX}-${GIT_HASH}"

echo "🚀 Starting smart build process..."
echo "   Registry: ${REGISTRY}"
echo "   Tag: ${TAG}"

# Find all service directories (those with a Dockerfile)
SERVICES=$(find services -maxdepth 2 -type f -name "Dockerfile" | xargs -n 1 dirname)

for SERVICE_PATH in $SERVICES; do
    SERVICE_NAME=$(basename "$SERVICE_PATH")
    IMAGE_NAME="${REGISTRY}/${SERVICE_NAME}:${TAG}"

    # Check if image already exists locally
    if docker image inspect "$IMAGE_NAME" &> /dev/null; then
        echo "✅ Image for ${SERVICE_NAME} already exists. Skipping build."
    else
        echo "🔨 Building image for ${SERVICE_NAME}..."
        docker build -t "$IMAGE_NAME" "$SERVICE_PATH"
        echo "   ✓ Built ${IMAGE_NAME}"
        
        # Load the newly built image into the Kind cluster
        echo "📥 Loading ${SERVICE_NAME} image into Kind cluster..."
        kind load docker-image "$IMAGE_NAME" --name soma-agent-hub
    fi
done

echo "🎉 Smart build process complete."
echo "   All necessary images are built and loaded with tag: ${TAG}"
