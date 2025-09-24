#!/usr/bin/env bash
set -euo pipefail

# Bootstrap local virtual environment for SomaGent services.
# Usage: ./scripts/dev/bootstrap_local_env.sh services/gateway-api

SERVICE_PATH=${1:-}
if [[ -z "$SERVICE_PATH" ]]; then
  echo "Usage: $0 <service-path>" >&2
  exit 1
fi

python -m venv "$SERVICE_PATH/.venv"
source "$SERVICE_PATH/.venv/bin/activate"
pip install --upgrade pip
if [[ -f "$SERVICE_PATH/requirements.txt" ]]; then
  pip install -r "$SERVICE_PATH/requirements.txt"
fi

echo "Environment ready. Activate with: source $SERVICE_PATH/.venv/bin/activate"
