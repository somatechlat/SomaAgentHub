#!/usr/bin/env bash
set -euo pipefail

IDENTITY_URL=${IDENTITY_URL:-http://localhost:10002}
TENANT=${TENANT:-demo}
USER_ID=${USER_ID:-airflow-service}
MFA_CODE=${MFA_CODE:-123456}

info() { echo "[smoke] $*"; }

check_ready() {
  if ! curl -fsS "$IDENTITY_URL/ready" >/dev/null; then
    info "Identity not responding at $IDENTITY_URL. Start it first, e.g.:"
    info "  PYTHONPATH=$PWD/services/identity-service $PWD/.venv/bin/python -m uvicorn --app-dir services/identity-service app.main:app --host 0.0.0.0 --port 10002"
    exit 1
  fi
}

issue_token() {
  local tenant=$1 user=$2 mfa=$3
  curl -fsS -X PUT "$IDENTITY_URL/v1/users/$user" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$user\",\"tenant_id\":\"$tenant\",\"capabilities\":[\"scheduler\",\"system\"],\"active\":true}" >/dev/null

  local enroll
  enroll=$(curl -fsS -X POST "$IDENTITY_URL/v1/users/$user/mfa/enroll")
  info "MFA enroll: $enroll"

  curl -fsS -X POST "$IDENTITY_URL/v1/users/$user/mfa/verify" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$user\",\"code\":\"$mfa\"}" >/dev/null

  local token_json
  token_json=$(curl -fsS -X POST "$IDENTITY_URL/v1/tokens/issue" \
    -H 'Content-Type: application/json' \
    -d "{\"tenant_id\":\"$tenant\",\"user_id\":\"$user\",\"mfa_code\":\"$mfa\",\"capabilities\":[\"scheduler\",\"system\"]}")
  echo "$token_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])'
}

verify_token() {
  local token=$1
  curl -fsS -X POST "$IDENTITY_URL/v1/tokens/verify" \
    -H 'Content-Type: application/json' \
    -d "{\"token\":\"$token\"}"
}

fetch_jwks() {
  curl -fsS "$IDENTITY_URL/.well-known/jwks.json"
}

main() {
  check_ready
  info "Issuing token for tenant=$TENANT user=$USER_ID"
  TOKEN=$(issue_token "$TENANT" "$USER_ID" "$MFA_CODE")
  info "Token issued (first 32 chars): ${TOKEN:0:32}..."
  info "Verifying token"
  verify_token "$TOKEN" | sed -E 's/\s+/ /g' | cut -c1-200; echo
  info "Fetching JWKS"
  fetch_jwks | sed -E 's/\s+/ /g' | cut -c1-200; echo
}

main "$@"
