# Policy Engine – User Manual

## Overview
Authorization decisions over prompts and actions.

## Endpoint
- POST /v1/evaluate { session_id, tenant, user, prompt, role, metadata }

## Responses
- { allowed: bool, reasons: [], score: number }
