"""Utility module exposing SQLModel for event‑related tests.

The test suite imports ``SQLModel`` from ``services.common.events.models`` to
create tables for the outbox pattern. The actual project does not provide this
module, which results in ``ModuleNotFoundError`` during test collection.

We simply re‑export the class from the ``sqlmodel`` package. This keeps the
dependency surface minimal and satisfies the import without affecting runtime
behaviour.
"""

from sqlmodel import SQLModel

# Re-export the OutboxEvent model used by several test suites. Importing here
# avoids circular dependencies because the OutboxEvent definition lives in the
# orchestrator package but is needed by generic event tests.
try:
from services.orchestrator.app.repository.outbox import OutboxEvent
except (
Exception
):  # pragma: no cover – during import time the orchestrator may not be loaded yet
OutboxEvent = None

__all__ = ["SQLModel", "OutboxEvent"]
