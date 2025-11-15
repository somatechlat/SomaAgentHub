"""Agent Spawner service package.

Provides a FastAPI application that creates Kubernetes Jobs/Deployments
representing agent instances and records them in the shared Postgres
database (the same `agent_instances` table used by the orchestrator).

The implementation follows the project's existing conventions:
* Uses the async FastAPI pattern already present in other services.
* Relies on the `kubernetes` Python client (installed via the service's
  `requirements.txt`).
* Uses the central `get_async_session` helper from
  `services.orchestrator.app.database` to obtain a SQLModel async session.
* Imports the `AgentInstance` model defined in
  `services.orchestrator.app.models.agent_instance`.
* All I/O that blocks (Kubernetes client calls) is executed in a thread
  via `asyncio.to_thread` to keep the FastAPI endpoint fully async.
"""

# The package does not expose any symbols at import time; the FastAPI app
# instance is defined in `main.py`.
