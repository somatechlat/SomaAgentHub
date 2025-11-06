"""Top‑level ``common`` namespace package.

The repository relies on ``import common.xxx`` from many services (e.g.
``common.config.runtime``).  Adding this ``__init__`` file makes ``common`` a
proper Python package and merges any sub‑packages that might exist in separate
locations via ``pkgutil.extend_path``.
"""

import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)
