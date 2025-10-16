#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Vault for local development
# Sets up KV v2, database auth, and Kubernetes auth

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_NAMESPACE="${VAULT_NAMESPACE:-somaagent}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

echo "🔐 Bootstrapping Vault at $VAULT_ADDR..."

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
for i in {1..30}; do
    if curl -sf "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
        echo "✅ Vault is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Vault did not become ready"
        exit 1
    fi
    sleep 1
done

export VAULT_ADDR
export VAULT_TOKEN
export VAULT_NAMESPACE

# Enable KV v2 secret engine if not already enabled
echo "📦 Setting up KV v2 secret engine..."
vault secrets list -format=json | jq -r '.[] | .type' | grep -q kv || \
    vault secrets enable -path=secret kv-v2 || true

# Create database credentials secret
echo "🔑 Creating database credentials secret..."
vault kv put secret/database/postgres \
    username="somaagent" \
    password="somaagent" \
    host="app-postgres" \
    port="5432" \
    database="somaagent"

vault kv put secret/database/temporal \
    username="temporal" \
    password="temporal" \
    host="temporal-postgres" \
    port="5432" \
    database="temporal"

# Create API credentials
echo "🔑 Creating API credentials..."
vault kv put secret/api/gateway \
    jwt_secret="dev-jwt-secret-change-in-production" \
    redis_url="redis://redis:6379/0"

vault kv put secret/api/identity \
    jwt_secret="dev-jwt-secret-change-in-production" \
    redis_url="redis://redis:6379/0"

# Create infrastructure credentials
echo "🔑 Creating infrastructure credentials..."
vault kv put secret/storage/minio \
    access_key="somaagent" \
    secret_key="local-developer" \
    endpoint="http://minio:9000"

vault kv put secret/storage/qdrant \
    api_url="http://qdrant:6333"

vault kv put secret/database/clickhouse \
    host="clickhouse" \
    port="8123" \
    username="default" \
    password=""

# Enable database secrets engine for dynamic credentials
echo "🔐 Setting up dynamic database credentials..."
vault secrets enable database || true

# Configure PostgreSQL dynamic credentials
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="read-only" \
    connection_url="postgresql://{{username}}:{{password}}@app-postgres:5432/somaagent?sslmode=disable" \
    username="somaagent" \
    password="somaagent"

vault write database/roles/read-only \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}' IN ROLE read_role;" \
    default_ttl="1h" \
    max_ttl="24h"

# List all stored secrets
echo ""
echo "✅ Vault bootstrap complete!"
echo ""
echo "📋 Stored secrets:"
vault kv list secret/database/ || true
vault kv list secret/api/ || true
vault kv list secret/storage/ || true

echo ""
echo "🔐 Access Vault UI at: http://localhost:8200"
echo "   Root token: $VAULT_TOKEN"
echo ""
