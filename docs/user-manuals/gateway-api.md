# Gateway API – User Manual

## Overview
The Gateway API is the primary entry point for all external traffic to the SomaAgentHub platform. It is responsible for authentication, request routing, and managing interactive user workflows.

## Endpoints

### System
- `GET /healthz`: Performs a health check of the service and its dependencies (Kafka, Auth, Redis).
- `GET /ready`: Indicates if the service is ready to accept traffic.
- `GET /metrics`: Exposes Prometheus metrics.

### Wizards
- `GET /v1/wizards`: Lists all available wizards.
- `POST /v1/wizards/start`: Starts a new wizard session.
    - **Request Body:** `{"wizard_id": "string", "user_id": "string", "metadata": {}}`
- `POST /v1/wizards/{session_id}/answer`: Submits an answer to a wizard prompt.
    - **Request Body:** `{"value": "any"}`
- `GET /v1/wizards/{session_id}`: Retrieves the current state of a wizard session.
- `POST /v1/wizards/{session_id}/approve`: Approves the execution of a wizard's actions.

## Authentication
The Gateway API uses JWT-based authentication. All requests to protected routes must include an `Authorization` header with a valid JWT bearer token.

## Error Handling
The Gateway API returns standard HTTP status codes to indicate the success or failure of a request. In the event of an error, the response body will contain a JSON object with a `detail` field that provides more information about the error.
