#!/usr/bin/env bash
set -euo pipefail

# Tier-0 compile gate: enforce import/compile cleanliness only for core services.
# Services in labs/experimental are intentionally excluded from this gate.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIER0_SERVICES=(
  "services/gateway-api"
  "services/orchestrator"
  "services/identity-service"
  "services/policy-engine"
)

cd "$ROOT_DIR"
echo "Compiling Tier-0 services..."
python3 -m compileall "${TIER0_SERVICES[@]}"
echo "Tier-0 compile complete."
