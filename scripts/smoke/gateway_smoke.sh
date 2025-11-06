#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL=${GATEWAY_URL:-http://localhost:10000}
IDENTITY_URL=${IDENTITY_URL:-http://localhost:10002}
TENANT=${TENANT:-demo}
USER_ID=${USER_ID:-airflow-service}
MFA_CODE=${MFA_CODE:-123456}
TOKEN=${TOKEN:-}

info() { echo "[gateway-smoke] $*"; }

need_service() {
  local url=$1 name=$2 endpoint=${3:-/ready}
  if ! curl -fsS "$url$endpoint" >/dev/null; then
    info "$name not responding at $url$endpoint"
    exit 1
  fi
}

issue_token() {
  local tenant=$1 user=$2 mfa=$3
  # Upsert user
  curl -fsS -X PUT "$IDENTITY_URL/v1/users/$user" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$user\",\"tenant_id\":\"$tenant\",\"capabilities\":[\"scheduler\",\"system\"],\"active\":true}" >/dev/null
  # Enroll + verify MFA (simple code flow for local smoke)
  curl -fsS -X POST "$IDENTITY_URL/v1/users/$user/mfa/enroll" >/dev/null
  curl -fsS -X POST "$IDENTITY_URL/v1/users/$user/mfa/verify" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$user\",\"code\":\"$mfa\"}" >/dev/null
  # Issue token
  curl -fsS -X POST "$IDENTITY_URL/v1/tokens/issue" \
    -H 'Content-Type: application/json' \
    -d "{\"tenant_id\":\"$tenant\",\"user_id\":\"$user\",\"mfa_code\":\"$mfa\",\"capabilities\":[\"scheduler\",\"system\"]}" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])'
}

call_gateway_status() {
  local token=$1
  curl -fsS -H "Authorization: Bearer $token" "$GATEWAY_URL/v1/status"
}

main() {
  need_service "$IDENTITY_URL" "Identity" "/ready"
  need_service "$GATEWAY_URL" "Gateway" "/ready"

  if [ -z "$TOKEN" ]; then
    info "Issuing token from Identity"
    TOKEN=$(issue_token "$TENANT" "$USER_ID" "$MFA_CODE")
  fi
  info "Calling Gateway /v1/status with bearer token"
  call_gateway_status "$TOKEN" | sed -E 's/\s+/ /g'
}

main "$@"
