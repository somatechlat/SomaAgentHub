# Tool Service – User Manual

## Overview
Executes actions against external systems (GitHub, Slack, etc.).

## Endpoint pattern
- POST /v1/adapters/{tool}/execute { action, arguments }

## Example
- tool: github, action: create_pull_request
