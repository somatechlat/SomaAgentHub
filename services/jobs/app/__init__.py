"""Jobs service package.

Import the central path‑setup shim so that the repository root is on ``sys.path``
and top‑level packages (e.g., ``common``) can be imported.
"""

"""Jobs service package.

Ensure the repository root is at the front of ``sys.path`` before importing
the central path‑setup shim.  This guarantees that the top‑level ``services``
namespace package (which contains ``_path_setup.py``) is resolved instead of
the service‑specific ``services`` subpackage that lives inside the service
directory and is added to ``sys.path`` by the test harness.
"""

import pathlib, sys
_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
	# Insert at the beginning to give priority over the service‑specific path.
	sys.path.insert(0, str(_repo_root))

import services._path_setup  # noqa: F401