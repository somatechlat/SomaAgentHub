# Refactoring Roadmap

Last Updated: October 9, 2025

## Objectives
- Simplify, remove entropy, and improve operability without breaking behavior.

## High-impact items (short term)
- Consolidate observability helpers
  - Unify duplicated observability modules across services (common package) to reduce drift.
- Standardize health payloads and metrics names (done for SLM; apply to others)
- Fix config normalization
  - Centralize env parsing with a common settings helper; keep legacy aliases but reduce duplication.

## Medium-term
- Helm chart improvements
  - Service-specific templates with common partials; add ServiceMonitors templates behind flags.
- API contract checks
  - Introduce shared OpenAPI schemas; validate in CI to catch drift.
- Test harness
  - Create a small library to spin services locally (testcontainers/k3d optional) for faster integration tests.

## Long-term
- Modularize services where coupling is high; extract shared libs (auth, policy clients) into a repo-internal common package.
- Gradual typed APIs (pydantic models for all request/response paths) and stricter lint/type checks.
