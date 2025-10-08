#!/usr/bin/env bash
# Simple helper to expose the SomaAgentHub Gateway API on localhost.
# Usage: ./scripts/port_forward_gateway.sh [LOCAL_PORT] [REMOTE_PORT]
# Defaults: LOCAL_PORT=8080, REMOTE_PORT=10000 (gateway-api service port)

set -euo pipefail

LOCAL_PORT=${1:-8080}
REMOTE_PORT=${2:-10000}
NAMESPACE="soma-agent-hub"
SERVICE="gateway-api"

echo "Port‑forwarding $SERVICE (port $REMOTE_PORT) to localhost:$LOCAL_PORT in namespace $NAMESPACE..."
# Run in background and print the PID so the user can kill it later.
kubectl port-forward svc/$SERVICE $LOCAL_PORT:$REMOTE_PORT -n $NAMESPACE &
PID=$!

echo "Port‑forward started (PID $PID). Press Ctrl+C to stop."
wait $PID
