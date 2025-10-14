# Identity Service – User Manual

## Overview
The Identity Service is responsible for managing user identities and issuing JWTs for authentication.

## Endpoints

### System
- `GET /health`: Performs a health check of the service.
- `GET /ready`: Indicates if the service is ready to accept traffic.
- `GET /metrics`: Exposes Prometheus metrics.

### Authentication
- `POST /v1/tokens/issue`: Issues a new JWT.
    - **Request Body:** `{"username": "string", "password": "string"}`
- `POST /v1/tokens/introspect`: Introspects a JWT.
    - **Request Body:** `{"token": "string"}`

## Key Rotation
The Identity Service automatically rotates its JWT signing keys at a regular interval to enhance security.

## Storage
The Identity Service uses Redis to store identity information.
