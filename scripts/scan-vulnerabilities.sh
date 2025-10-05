#!/usr/bin/env bash
set -euo pipefail

# Scan all Docker images for vulnerabilities using Trivy
# Usage: ./scan-vulnerabilities.sh [--severity LEVEL] [--output-format FORMAT]

SEVERITY="${1:---severity CRITICAL,HIGH,MEDIUM}"
OUTPUT_FORMAT="${2:-table}"
SCAN_DIR="security-scans"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "🔍 Starting vulnerability scan..."
mkdir -p "$SCAN_DIR"

# List of services to scan
SERVICES=(
    "orchestrator"
    "gateway-api"
    "policy-engine"
    "identity-service"
    "slm-service"
    "analytics-service"
    "constitution-service"
    "billing-service"
    "recall-service"
    "settings-service"
)

# Install Trivy if not present
if ! command -v trivy &> /dev/null; then
    echo "📦 Installing Trivy..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
fi

# Scan each service image
for service in "${SERVICES[@]}"; do
    echo ""
    echo "🔍 Scanning $service..."
    
    dockerfile="services/$service/Dockerfile"
    if [ ! -f "$dockerfile" ]; then
        echo "⚠️  Dockerfile not found for $service, skipping..."
        continue
    fi
    
    # Build image for scanning
    image_tag="somaagent/$service:scan"
    docker build -t "$image_tag" -f "$dockerfile" . --quiet || {
        echo "❌ Failed to build $service"
        continue
    }
    
    # Run Trivy scan
    trivy image \
        $SEVERITY \
        --format "$OUTPUT_FORMAT" \
        --output "$SCAN_DIR/${service}-${TIMESTAMP}.txt" \
        "$image_tag"
    
    # Also generate JSON for CI/CD integration
    trivy image \
        $SEVERITY \
        --format json \
        --output "$SCAN_DIR/${service}-${TIMESTAMP}.json" \
        "$image_tag"
    
    # Check for critical vulnerabilities
    CRITICAL_COUNT=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$SCAN_DIR/${service}-${TIMESTAMP}.json")
    HIGH_COUNT=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$SCAN_DIR/${service}-${TIMESTAMP}.json")
    
    if [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
        echo "⚠️  Found $CRITICAL_COUNT critical and $HIGH_COUNT high vulnerabilities in $service"
    else
        echo "✅ No critical or high vulnerabilities found in $service"
    fi
done

# Generate summary report
echo ""
echo "📊 Generating summary report..."
cat > "$SCAN_DIR/summary-${TIMESTAMP}.md" << EOF
# Vulnerability Scan Summary
**Date**: $(date)
**Scan Type**: Container Image Vulnerabilities

## Services Scanned
EOF

for service in "${SERVICES[@]}"; do
    if [ -f "$SCAN_DIR/${service}-${TIMESTAMP}.json" ]; then
        CRITICAL=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$SCAN_DIR/${service}-${TIMESTAMP}.json")
        HIGH=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$SCAN_DIR/${service}-${TIMESTAMP}.json")
        MEDIUM=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="MEDIUM")] | length' "$SCAN_DIR/${service}-${TIMESTAMP}.json")
        
        echo "- **$service**: 🔴 $CRITICAL critical, 🟠 $HIGH high, 🟡 $MEDIUM medium" >> "$SCAN_DIR/summary-${TIMESTAMP}.md"
    fi
done

echo ""
echo "✅ Scan complete! Results saved to $SCAN_DIR/"
echo "📄 Summary: $SCAN_DIR/summary-${TIMESTAMP}.md"

# Exit with error if any critical vulnerabilities found
TOTAL_CRITICAL=$(cat "$SCAN_DIR"/*-${TIMESTAMP}.json | jq -s '[.[]?.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
if [ "$TOTAL_CRITICAL" -gt 0 ]; then
    echo ""
    echo "❌ Found $TOTAL_CRITICAL total critical vulnerabilities. Please remediate before deployment."
    exit 1
fi

exit 0
