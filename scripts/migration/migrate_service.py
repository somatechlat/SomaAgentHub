#!/usr/bin/env python3
"""
Deprecated migration script.

The unified settings/registry/vault_manager workflow has been removed.
Configuration is centralized via:
 - services.common.config.base_settings.resolve_env
 - services.common.vault_client for secrets (DEV uses env/in-memory fallbacks)

This script is no longer supported and will not run.
"""

import sys
from services.common.config.base_settings import resolve_env


def main() -> int:
raise RuntimeError(
"scripts/migration/migrate_service.py is deprecated. Use resolve_env in service configs "
"and VaultClient where needed."
)


if __name__ == "__main__":
try:
main()
except Exception as e:
print(f"❌ {e}")
sys.exit(1)
