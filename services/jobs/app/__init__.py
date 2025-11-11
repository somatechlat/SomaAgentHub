"""Jobs service package.

Ensure the repository root is at the front of ``sys.path`` before importing
the central path‑setup shim. This guarantees that the top‑level ``services``
namespace package (which contains ``_path_setup.py``) is resolved instead of
the service‑specific ``services`` subpackage added by the test harness.
"""

import pathlib
import sys

_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
# Insert at the beginning to give priority over the service‑specific path.
sys.path.insert(0, str(_repo_root))

import services._path_setup  # noqa: F401,E402
from services.common.config.base_settings import resolve_env
