"""Settings service package.

``sys.path`` for top‑level imports such as ``common``.
"""

import services._path_setup  # noqa: F401
from services.common.config.base_settings import resolve_env
