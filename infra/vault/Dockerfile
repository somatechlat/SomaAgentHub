FROM hashicorp/vault:1.15.0

# Copy custom Vault configuration
COPY infra/vault/config.hcl /vault/config/

# Set Vault data directory
ENV VAULT_CONFIG_DIR=/vault/config

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD curl -f http://127.0.0.1:8200/v1/sys/health || exit 1

# Use default entrypoint from base image
