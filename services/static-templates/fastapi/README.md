# {{APP_NAME}} FastAPI Service Template

This is a static scaffold used by the Taxi builder.

## Endpoints
- GET /health/live → {"status": "ok"}
- GET /health/ready → {"status": "ready"}

## Local Run
uvicorn app.main:app --host 0.0.0.0 --port {{SERVICE_PORT}}

## Docker
docker build -t {{IMAGE}} .
docker run -p {{SERVICE_PORT}}:{{SERVICE_PORT}} {{IMAGE}}
