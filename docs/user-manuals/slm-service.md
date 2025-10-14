# SLM Service – User Manual

## Overview
The SLM Service provides deterministic, local language capabilities for the SomaAgentHub platform.

## Endpoints

### System
- `GET /health`: Performs a health check of the service.
- `GET /metrics`: Exposes Prometheus metrics.

### Language
- `POST /v1/infer/sync`: Generates text using a local model.
    - **Request Body:** `{"prompt": "string", "max_tokens": "integer", "temperature": "float"}`
- `POST /v1/embeddings`: Creates vector embeddings for text.
    - **Request Body:** `{"input": ["string"]}`
- `POST /v1/chat/completions`: A backward-compatible endpoint that mirrors the sync inference capability.
- `GET /models`: Lists the available models.
- `POST /models/load`: Loads a model into memory.

## Models
The SLM Service uses a local Markov chain-based model for text generation and a pre-trained model for embeddings.
