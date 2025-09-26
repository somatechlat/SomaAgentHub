"""FastAPI application entry point for the Orchestrator service.

This module creates the FastAPI `app` instance and includes the routes defined in
`services.orchestrator.app.api.routes`. It is used by the CI workflow (uvicorn
`services.orchestrator.app.main:app`) and by the test suite.
"""

from fastapi import FastAPI

from .api import routes

app = FastAPI(title="SomaGent Orchestrator", version="0.1.0")

# Register the router that contains all endpoints (session, turn, marketplace, jobs, …)
app.include_router(routes.router)
