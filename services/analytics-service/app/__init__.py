"""Analytics service package.

This ``__init__`` ensures that the repository root is on ``sys.path`` before
any other modules within the service are imported.  Tests prepend the service
directory to ``sys.path`` and then import ``app.main`` directly.  The service
code imports top‑level packages such as ``common.config``; without the repo
root on the import path those imports fail.  By inserting the repository root
here we guarantee the shared ``common`` namespace is discoverable for all
services.
"""

import pathlib
import sys

# Add the repository root (two levels up from this file) to ``sys.path`` if it
# is not already present.  ``append`` keeps the service directory as the first
# entry (the test harness inserts it at index 0), preserving the expected
# import order for service‑local modules.
repo_root = pathlib.Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
	sys.path.append(str(repo_root))
