# Backup & Recovery (Stub)

This page describes the high-level backup and recovery strategy for SomaAgentHub.

Critical data
- PostgreSQL (dump & WAL)
- Qdrant/vector DB snapshots
- Object storage (MinIO/S3)

Restoration steps
1. Restore database from latest snapshot.
2. Recreate services and verify health checks.

TODO: add commands and verified playbooks.
