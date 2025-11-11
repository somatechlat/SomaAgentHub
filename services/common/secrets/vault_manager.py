from services.common.config.base_settings import resolve_env

"""DEPRECATED: vault_manager has been removed.

Use `services.common.vault_client.VaultClient` and `resolve_env` instead.
Importing this module raises to prevent accidental usage.
"""

raise ImportError(
"services.common.secrets.vault_manager is deprecated. "
"Use services.common.vault_client.VaultClient and resolve_env."
)
