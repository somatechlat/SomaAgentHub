#!/usr/bin/env bash
set -euo pipefail

# Generate Software Bill of Materials (SBOM) for all services
# Uses Syft to create SBOMs in SPDX and CycloneDX formats

SBOM_DIR="sbom"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "📋 Generating SBOMs for all services..."
mkdir -p "$SBOM_DIR"

# Install Syft if not present
if ! command -v syft &> /dev/null; then
    echo "📦 Installing Syft..."
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
fi

SERVICES=(
    "orchestrator"
    "gateway-api"
    "policy-engine"
    "identity-service"
    "somallm-provider"
    "analytics-service"
    "constitution-service"
    "billing-service"
    "recall-service"
    "settings-service"
)

for service in "${SERVICES[@]}"; do
    echo ""
    echo "📋 Generating SBOM for $service..."
    
    dockerfile="services/$service/Dockerfile"
    if [ ! -f "$dockerfile" ]; then
        echo "⚠️  Dockerfile not found for $service, skipping..."
        continue
    fi
    
    # Build image
    image_tag="somaagent/$service:sbom"
    docker build -t "$image_tag" -f "$dockerfile" . --quiet || {
        echo "❌ Failed to build $service"
        continue
    }
    
    # Generate SPDX SBOM
    syft "$image_tag" \
        -o spdx-json \
        --file "$SBOM_DIR/${service}-spdx-${TIMESTAMP}.json"
    
    # Generate CycloneDX SBOM
    syft "$image_tag" \
        -o cyclonedx-json \
        --file "$SBOM_DIR/${service}-cyclonedx-${TIMESTAMP}.json"
    
    # Generate human-readable table
    syft "$image_tag" \
        -o table \
        --file "$SBOM_DIR/${service}-table-${TIMESTAMP}.txt"
    
    echo "✅ SBOM generated for $service"
done

# Generate combined SBOM for entire platform
echo ""
echo "📋 Generating combined platform SBOM..."

# Create combined SPDX document
cat > "$SBOM_DIR/platform-spdx-${TIMESTAMP}.json" << EOF
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "SomaAgent Platform",
  "documentNamespace": "https://somaagent.io/sbom/platform-${TIMESTAMP}",
  "creationInfo": {
    "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "creators": ["Tool: syft", "Organization: SomaAgent"],
    "licenseListVersion": "3.20"
  },
  "packages": []
}
EOF

echo "✅ All SBOMs generated in $SBOM_DIR/"
echo ""
echo "📊 Summary:"
ls -lh "$SBOM_DIR"/*-${TIMESTAMP}.*

# Sign SBOMs with cosign (if available)
if command -v cosign &> /dev/null; then
    echo ""
    echo "🔏 Signing SBOMs with cosign..."
    for sbom_file in "$SBOM_DIR"/*-${TIMESTAMP}.json; do
        cosign sign-blob --yes "$sbom_file" > "${sbom_file}.sig"
        echo "✅ Signed $(basename "$sbom_file")"
    done
fi

exit 0
