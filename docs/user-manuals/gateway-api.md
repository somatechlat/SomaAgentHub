# Gateway API – User Manual

## Overview
Edge API for authenticated access to SomaAgent services.

## Base URL
- Local port-forward: http://127.0.0.1:8080

## Health
```
GET /health -> {"status":"ok","service":"gateway-api"}
```

## Authentication
- Uses Bearer tokens (JWT). Obtain from Identity Service.

## Common Tasks
- Check health, list routes, and call dashboard health (requires auth).

## Troubleshooting
- If 401 Missing bearer token, include Authorization header.
