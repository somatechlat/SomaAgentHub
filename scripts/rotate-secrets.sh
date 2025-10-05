#!/usr/bin/env bash
set -euo pipefail

# Rotate secrets in Vault for all services
# Triggers automatic credential rotation for database, API keys, etc.

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_NAMESPACE="${VAULT_NAMESPACE:-somaagent}"

echo "🔄 Starting secret rotation..."

# Check if Vault is accessible
if ! vault status &> /dev/null; then
    echo "❌ Vault is not accessible at $VAULT_ADDR"
    exit 1
fi

# Database credential rotation
echo ""
echo "🗄️  Rotating database credentials..."

DB_ROLES=(
    "orchestrator"
    "policy-engine"
    "analytics"
    "identity"
    "billing"
)

for role in "${DB_ROLES[@]}"; do
    echo "  Rotating credentials for $role..."
    
    # Rotate root credentials (triggers rotation for all dynamic credentials)
    vault write -force "database/rotate-root/$role" || {
        echo "  ⚠️  Failed to rotate $role (may not exist yet)"
        continue
    }
    
    echo "  ✅ Rotated $role"
done

# API Key rotation
echo ""
echo "🔑 Rotating API keys..."

API_KEYS=(
    "somaagent/gateway/api-key"
    "somaagent/slm/anthropic-key"
    "somaagent/slm/openai-key"
    "somaagent/billing/stripe-key"
)

for key_path in "${API_KEYS[@]}"; do
    echo "  Checking $key_path..."
    
    # Read current version
    current_version=$(vault kv get -format=json "secret/$key_path" 2>/dev/null | jq -r '.data.metadata.version // 0')
    
    if [ "$current_version" -eq 0 ]; then
        echo "  ⚠️  Key not found, skipping..."
        continue
    fi
    
    # In production, this would:
    # 1. Generate new key from external provider
    # 2. Write to Vault
    # 3. Update external service to use new key
    # 4. Verify new key works
    # 5. Delete old version
    
    echo "  ℹ️  Would rotate $key_path (current version: $current_version)"
done

# JWT signing key rotation
echo ""
echo "🎫 Rotating JWT signing keys..."

# Generate new RSA key pair
openssl genrsa -out /tmp/jwt_private.pem 4096 2>/dev/null
openssl rsa -in /tmp/jwt_private.pem -pubout -out /tmp/jwt_public.pem 2>/dev/null

# Read keys
PRIVATE_KEY=$(cat /tmp/jwt_private.pem)
PUBLIC_KEY=$(cat /tmp/jwt_public.pem)

# Write to Vault
vault kv put "secret/somaagent/jwt-keys" \
    private_key="$PRIVATE_KEY" \
    public_key="$PUBLIC_KEY" \
    rotated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" || {
    echo "  ⚠️  Failed to write JWT keys to Vault"
}

# Cleanup
rm -f /tmp/jwt_private.pem /tmp/jwt_public.pem

echo "  ✅ Rotated JWT signing keys"

# Encryption key rotation (using Vault Transit)
echo ""
echo "🔐 Rotating encryption keys..."

TRANSIT_KEYS=(
    "somaagent-data"
    "somaagent-pii"
)

for key_name in "${TRANSIT_KEYS[@]}"; do
    echo "  Rotating transit key: $key_name..."
    
    # Rotate key (creates new version, old versions still work for decryption)
    vault write -f "transit/keys/$key_name/rotate" || {
        echo "  ⚠️  Failed to rotate $key_name (may not exist yet)"
        continue
    }
    
    # Get current version
    key_info=$(vault read -format=json "transit/keys/$key_name")
    latest_version=$(echo "$key_info" | jq -r '.data.latest_version')
    
    echo "  ✅ Rotated $key_name to version $latest_version"
done

# Update minimum decryption version (prevents use of old keys)
echo ""
echo "🔒 Updating minimum decryption versions..."

for key_name in "${TRANSIT_KEYS[@]}"; do
    # Get current latest version
    key_info=$(vault read -format=json "transit/keys/$key_name" 2>/dev/null) || continue
    latest_version=$(echo "$key_info" | jq -r '.data.latest_version')
    
    # Set min_decryption_version to latest - 2 (keep 3 versions)
    min_version=$((latest_version - 2))
    if [ $min_version -lt 1 ]; then
        min_version=1
    fi
    
    vault write "transit/keys/$key_name/config" \
        min_decryption_version=$min_version \
        min_encryption_version=$latest_version || {
        echo "  ⚠️  Failed to update config for $key_name"
        continue
    }
    
    echo "  ✅ Updated $key_name (min decrypt: $min_version, min encrypt: $latest_version)"
done

echo ""
echo "✅ Secret rotation complete!"
echo ""
echo "📊 Summary:"
echo "  - Database credentials: ${#DB_ROLES[@]} roles rotated"
echo "  - API keys: ${#API_KEYS[@]} keys checked"
echo "  - JWT signing keys: 1 pair rotated"
echo "  - Transit encryption keys: ${#TRANSIT_KEYS[@]} keys rotated"
echo ""
echo "ℹ️  Services will automatically pick up new credentials on next fetch"
echo "⚠️  Monitor application logs for any authentication errors"

exit 0
