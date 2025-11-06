---
title: Backup and Recovery Guide
---

# Backup and Recovery Guide

This document describes how to **snapshot** and **restore** the state of the
SomaAgentHub platform.  The platform consists of several stateful services:

* **PostgreSQL** – Application database (`app-postgres`).
* **Temporal PostgreSQL** – Workflow engine persistence (`temporal-postgres`).
* **Redis** – In‑memory cache used by the Identity and Memory services.
* **Qdrant** – Vector store for the Memory Gateway.

All of these services expose a Docker volume that can be copied to a backup
location.  The repository provides helper scripts in `scripts/` to automate the
process.

---

## Prerequisites

* Access to the repository root (where the `scripts/` directory lives).
* `aws` CLI configured if you intend to upload backups to an S3 bucket.
* Sufficient disk space for the backup files.

---

## 1️⃣ Create a Backup

Run the provided `backup-databases.sh` script.  It creates compressed
snapshots for PostgreSQL, Temporal‑Postgres, and Redis, and stores them in the
`$(BACKUP_DIR)` directory (default: `/tmp/somaagent-backups`).

```bash
make backup-databases   # Uses the Make target defined in the root Makefile
```

The script performs the following steps:

1. **PostgreSQL** – Uses `pg_dump` to export the `somaagent` database.
2. **Temporal‑Postgres** – Dumps the `temporal` database.
3. **Redis** – Saves an RDB snapshot (`redis-cli --rdb`).
4. **Compression** – All files are compressed with `gzip`.

If you prefer to run the script directly:

```bash
./scripts/backup-databases.sh
```

---

## 2️⃣ Upload to Object Storage (Optional)

The script can optionally upload the archive to an S3 bucket.  Set the
environment variable `S3_BUCKET` before invoking the script:

```bash
export S3_BUCKET=s3://my-soma-backups
make backup-databases
```

The script uses the AWS CLI to `aws s3 cp` each archive into the bucket, naming
the objects with a timestamp (`$(date +%Y%m%d%H%M%S)`).

---

## 3️⃣ Restore a Backup

To restore a previously created backup, use the `restore-databases.sh` script.
Provide the timestamped backup filename via the `RESTORE_TIMESTAMP`
environment variable:

```bash
export RESTORE_TIMESTAMP=20251106T120000   # example timestamp
make restore-databases
```

The script will:

1. Download the archive from S3 if `S3_BUCKET` is set.
2. Decompress the files.
3. Use `psql` to restore PostgreSQL databases.
4. Load the Redis RDB snapshot.

---

## 4️⃣ Verify the Restore

After restoration, ensure the services start correctly:

```bash
make dev-up            # Start supporting services (Temporal, Redis, etc.)
make dev-start-services
make k8s-smoke         # Run smoke tests against the restored state
```

If any service fails to start, check the logs in `.logs/` for error details.

---

## 5️⃣ Automation Recommendations

* **Scheduled Backups** – Use a cron job or GitHub Actions workflow that runs
  `make backup-databases` nightly.
* **Retention Policy** – Keep the last N backups (e.g., 7 days) and purge older
  archives from the bucket.
* **Disaster Recovery Drill** – Periodically perform a full restore on a
  staging cluster to verify the backup process.

---

**References**

* `scripts/backup-databases.sh` – Implementation details.
* `scripts/restore-databases.sh` – Restoration logic.
* `Makefile` – Targets `backup-databases` and `restore-databases`.

---

*Last updated*: `$(date +%Y-%m-%d)`
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
