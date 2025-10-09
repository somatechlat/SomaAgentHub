# Identity Service – User Manual

## Overview
Issues tokens for authenticated requests.

## Endpoint
- POST /v1/tokens/issue { username, password }

## Usage
- Use the returned token with Gateway API Authorization: Bearer <token>
