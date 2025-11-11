# Documentation Style Guide (ISO12207§8.3)

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## General Rules
- **File names**: `kebab-case.md` (e.g., `propagation-service.md`).
- **Headings**: Use ATX style (`#`, `##`, `###`).
- **Code blocks**: Triple backticks with language identifier.
- **Diagrams**: PlantUML (`.puml`) or Mermaid (````mermaid`).
- **Version badge**: Insert `![Version](https://img.shields.io/badge/version-1.0.0-blue)` at the top of every page.
- **Links**: Prefer relative links (`[text](../path/file.md)`).
- **Accessibility**: All images must have `alt` text; tables need a caption.

## Linting
The CI runs `markdownlint-cli2` with the following rule set (see `.markdownlint.json`):
- `MD001` – heading levels should only increment by one.
- `MD013` – line length ≤120.
- `MD041` – first line should be a top‑level heading.

## SomaAgentHub Specific Conventions
- **Service names**: Use PascalCase for service references (e.g., GatewayAPI, Orchestrator)
- **Port references**: Always include both container and host ports (e.g., "10000 (host) → 8000 (container)")
- **Code examples**: Follow existing patterns from services/ directory
- **Architecture diagrams**: Use PlantUML for system architecture, Mermaid for data flows