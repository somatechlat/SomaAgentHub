"""Top‑level entry point for the FastAPI application used in tests.

The test suite imports ``app.main`` directly (e.g. ``from app.main import app``).
In the multi‑service repository each service has its own ``app`` package, but
there is no single module at the repository root that provides the FastAPI
instance.  Creating this thin wrapper ensures that the import resolves to the
Memory‑Gateway implementation, which is the service exercised by the unit
tests.

If additional services need to be exposed in a similar way they can import the
relevant ``app`` object here.
"""

# Re‑export the FastAPI ``app`` defined in the memory‑gateway service.
from services.memory_gateway.app.main import app  # noqa: F401
