# SomaAgentHub Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Intelligent Dev Environment**: Implemented a new `make dev-env` command that intelligently detects cluster state, verifies health, and interactively prompts for recreation, ensuring a robust and idempotent startup process.
- **Persistent Local Storage**: Reconfigured the local Kind cluster to use persistent host-path mounting, ensuring all data survives cluster recreation.
- **Optimized Build Process**: Created a new `build-changed.sh` script that intelligently builds only the necessary Docker images, dramatically speeding up local development cycles.
- **Comprehensive Documentation Framework**:
    - Implemented a new four-manual documentation structure: User, Technical, Development, and Onboarding manuals.
    - Created detailed, high-quality content for all documentation files based on a deep analysis of the codebase.
    - Added a `DOCUMENTATION_GUIDE_TEMPLATE.md` to standardize future documentation.
    - Added a `style-guide.md` and `glossary.md`.

### Changed
- **Standardized All Ports**: Refactored the entire repository to use a new, consistent port mapping starting from 10000. All hardcoded ports have been removed in favor of a centralized Helm configuration.
- **Standardized Dockerfiles**: Audited and refactored all `Dockerfiles` to use official, version-pinned, minimal base images, improving security and build reliability.
- **Simplified Makefile**: Refactored the `Makefile` to be a clean wrapper around Helm and automation scripts, adopting best practices from `SomaStack`.
- Replaced the monolithic `HANDBOOK.md` and other scattered documentation files with the new structured documentation.

### Removed
- Deleted numerous outdated and redundant documentation files from the `docs/` directory to centralize information.

---

## [1.0.0] - 2024-10-01

### Added
- Initial release of the SomaAgentHub platform.
- Core services: Gateway API, Orchestrator, Identity Service, Policy Engine, Memory Gateway.
- Kubernetes deployment support via Helm.
- Basic documentation and README.
```
