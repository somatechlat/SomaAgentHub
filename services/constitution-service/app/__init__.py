"""Constitution service package.

Import the central path‑setup shim so that the repository root is added to
``sys.path`` and top‑level imports (e.g., ``common``) work correctly.
"""

# import services._path_setup  # noqa: F401  # removed for local setup
from services.common.config.base_settings import resolve_env
