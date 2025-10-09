#!/usr/bin/env bash
# Select free host ports for docker services and produce a docker-compose override
# Portable to macOS (avoid associative arrays)

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OVERRIDE_FILE="$ROOT_DIR/infra/temporal/docker-compose.override.ports.yml"

port_in_use() {
  port=$1
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1 && return 0 || return 1
  elif command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -E ":$port$" >/dev/null 2>&1 && return 0 || return 1
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltn | awk '{print $4}' | grep -E ":$port$" >/dev/null 2>&1 && return 0 || return 1
  else
    return 1
  fi
}

find_free_port() {
  start=$1
  port=$start
  while [ $port -le 65535 ]; do
    if ! port_in_use "$port"; then
      echo $port
      return 0
    fi
    port=$((port + 1))
  done
  return 1
}

echo "Selecting ports for Temporal services..."

# mappings are lines of: service|host1:container1,host2:container2
mappings=(
  "temporal-postgres|5434:5432"
  "temporal|7233:7233,7234:7234"
  "temporal-ui|8088:8080"
)

# We'll store assigned mappings in a temp file: svc|host1:container1,...
TMPASSIGN=$(mktemp)
trap 'rm -f "$TMPASSIGN"' EXIT

# Track assigned host ports to avoid duplicates
ASSIGNED_PORTS=$(mktemp)
trap 'rm -f "$TMPASSIGN" "$ASSIGNED_PORTS"' EXIT

for mapping in "${mappings[@]}"; do
  svc=${mapping%%|*}
  rest=${mapping#*|}
  assigned_str=""
  IFS=','; set -- $rest; unset IFS
  for part in "$@"; do
    desired_host=${part%%:*}
    container_port=${part##*:}
    # find a host port that is not in use and not already assigned by this script
    try_host=$desired_host
    while true; do
      # if already assigned in this run, pick next
      if grep -qx "$try_host" "$ASSIGNED_PORTS" 2>/dev/null; then
        try_host=$((try_host + 1))
        continue
      fi

      if port_in_use "$try_host"; then
        try_host=$((try_host + 1))
        continue
      fi

      chosen_host=$try_host
      # mark chosen host as assigned
      echo "$chosen_host" >> "$ASSIGNED_PORTS"
      if [ "$chosen_host" -ne "$desired_host" ]; then
        echo "Port $desired_host is in use or reserved; assigning free host port $chosen_host for $svc:$container_port"
      else
        echo "Port $desired_host is available; using it for $svc:$container_port"
      fi
      assigned_str="$assigned_str${chosen_host}:${container_port},"
      break
    done
  done
  # trim trailing comma
  assigned_str=${assigned_str%,}
  echo "$svc|$assigned_str" >> "$TMPASSIGN"
done

echo "Writing override file: $OVERRIDE_FILE"
cat > "$OVERRIDE_FILE" <<EOF
version: '3.8'
services:
EOF

while IFS='|' read -r svc assigned_ports; do
  echo "  $svc:" >> "$OVERRIDE_FILE"
  echo "    ports:" >> "$OVERRIDE_FILE"
  IFS=','; set -- $assigned_ports; unset IFS
  for p in "$@"; do
    echo "      - \"$p\"" >> "$OVERRIDE_FILE"
  done
done < "$TMPASSIGN"

echo "Override file generated. Review $OVERRIDE_FILE before running docker-compose."

# Provide recommended redis run command
redis_mapping="6379:6379"
redis_host_port=${redis_mapping%%:*}
if port_in_use "$redis_host_port"; then
  redis_host_port=$(find_free_port $((redis_host_port + 1))) || redis_host_port=$(find_free_port 20000)
fi
echo "To start Redis on the chosen host port run (or update Makefile):"
echo "  docker run -d --name soma-redis --network somaagenthub-network --restart unless-stopped -p ${redis_host_port}:6379 redis:7-alpine"

echo "Suggested docker-compose command (uses override):"
echo "  docker-compose -f infra/temporal/docker-compose.yml -f infra/temporal/docker-compose.override.ports.yml up -d"

exit 0
