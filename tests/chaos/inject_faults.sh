#!/usr/bin/env bash
set -euo pipefail

# Simple chaos helper for local docker-compose stack.
# Usage examples:
#   ./tests/chaos/inject_faults.sh stop slm
#   ./tests/chaos/inject_faults.sh delay kafka 5

SERVICE=${2:-}
case "$1" in
  stop)
    if [[ -z "$SERVICE" ]]; then
      echo "Usage: $0 stop <service-name>" >&2
      exit 1
    fi
    docker compose -f docker-compose.stack.yml stop "$SERVICE"
    ;;
  start)
    if [[ -z "$SERVICE" ]]; then
      echo "Usage: $0 start <service-name>" >&2
      exit 1
    fi
    docker compose -f docker-compose.stack.yml start "$SERVICE"
    ;;
  delay)
    if [[ -z "$SERVICE" || -z ${3:-} ]]; then
      echo "Usage: $0 delay <service-name> <seconds>" >&2
      exit 1
    fi
    docker compose -f docker-compose.stack.yml stop "$SERVICE"
    sleep "$3"
    docker compose -f docker-compose.stack.yml start "$SERVICE"
    ;;
  *)
    echo "Unknown action $1" >&2
    exit 1
    ;;
 esac
