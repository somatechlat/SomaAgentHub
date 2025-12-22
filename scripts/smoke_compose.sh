#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SERVICES=(
  app-postgres
  temporal-postgres
  temporal-server
  redis
  policy-engine
  identity-service
  orchestrator
  worker
  gateway-api
)

cleanup() {
  echo "[stop] Shutting down Tier-0 services"
  docker compose down >/dev/null 2>&1 || true
}

trap cleanup EXIT

wait_http() {
  local name="$1" url="$2" attempts="${3:-30}"
  for i in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[ok] $name ready at $url"
      return 0
    fi
    sleep 2
  done
  echo "[fail] $name not ready: $url" >&2
  return 1
}

wait_port() {
  local name="$1" host="$2" port="$3" attempts="${4:-30}"
  python - <<'PY'
import socket, sys, time

name, host, port, attempts = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
for i in range(attempts):
    try:
        with socket.create_connection((host, port), timeout=1):
            print(f"[ok] {name} port {port} reachable on {host}")
            sys.exit(0)
    except OSError:
        time.sleep(2)
print(f"[fail] {name} port {port} unreachable on {host}", file=sys.stderr)
sys.exit(1)
PY "$name" "$host" "$port" "$attempts"
}

cd "$ROOT_DIR"

echo "[start] Bringing up Tier-0 services: ${SERVICES[*]}"
docker compose up -d "${SERVICES[@]}"

echo "[wait] Health checks"
wait_http "gateway-api" "http://127.0.0.1:${GATEWAY_API_PORT:-10000}/ready"
wait_http "orchestrator" "http://127.0.0.1:${ORCHESTRATOR_PORT:-10001}/ready"
wait_http "identity-service" "http://127.0.0.1:${IDENTITY_SERVICE_PORT:-10002}/health"
wait_http "policy-engine" "http://127.0.0.1:${POLICY_ENGINE_PORT:-10020}/health"
wait_port "temporal-server" "127.0.0.1" "${TEMPORAL_PORT:-7233}"

# Minimal session flow (start -> status)
echo "[run] Starting session via orchestrator"
SESSION_PAYLOAD='{"tenant":"dev-tenant","user":"smoke-user","prompt":"hello","model":"somagent-demo"}'
SESSION_RESPONSE="$(curl -fsS -X POST "http://127.0.0.1:${ORCHESTRATOR_PORT:-10001}/v1/sessions/start" \
  -H "Content-Type: application/json" \
  -d "$SESSION_PAYLOAD")"
WORKFLOW_ID="$(python - <<'PY'
import json, sys
resp = json.loads(sys.stdin.read())
print(resp.get("workflow_id",""))
PY <<<"$SESSION_RESPONSE")"

if [ -z "$WORKFLOW_ID" ]; then
  echo "[fail] session start did not return workflow_id"
  exit 1
fi

echo "[run] Checking session status for $WORKFLOW_ID"
curl -fsS "http://127.0.0.1:${ORCHESTRATOR_PORT:-10001}/v1/sessions/${WORKFLOW_ID}" >/dev/null

echo "[done] Smoke stack is healthy."
