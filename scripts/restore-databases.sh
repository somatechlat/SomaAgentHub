#!/bin/bash
#
# Restore databases from backup
# Restores ClickHouse and PostgreSQL from S3 backup

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo ""
    echo "Example: $0 20250105_120000"
    echo ""
    echo "Available backups:"
    aws s3 ls s3://somaagent-backups/backups/ | tail -10
    exit 1
fi

BACKUP_TIMESTAMP=$1
S3_BUCKET="${S3_BUCKET:-s3://somaagent-backups}"
RESTORE_DIR="/tmp/somaagent-restore"

echo "🔄 Starting restore process for backup: $BACKUP_TIMESTAMP"
mkdir -p "$RESTORE_DIR"

# Download backup from S3
echo ""
echo "☁️  Downloading backup from S3..."
aws s3 sync "$S3_BUCKET/backups/$BACKUP_TIMESTAMP/" "$RESTORE_DIR/"

if [ ! "$(ls -A "$RESTORE_DIR")" ]; then
    echo "❌ Backup not found: $BACKUP_TIMESTAMP"
    exit 1
fi

echo "  ✅ Downloaded backup files"

# Confirm restore
echo ""
echo "⚠️  WARNING: This will OVERWRITE the current database!"
read -p "Are you sure you want to restore? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Restore ClickHouse
echo ""
echo "📊 Restoring ClickHouse..."

# Stop ClickHouse writes
clickhouse-client --query="SYSTEM STOP MERGES"

# Restore from backup
clickhouse-client --query="RESTORE DATABASE somaagent FROM Disk('backups', '$BACKUP_TIMESTAMP')" || {
    echo "  Using clickhouse-backup for restore"
    clickhouse-backup restore "$BACKUP_TIMESTAMP"
}

# Resume operations
clickhouse-client --query="SYSTEM START MERGES"

echo "  ✅ ClickHouse restore complete"

# Restore PostgreSQL
echo ""
echo "🐘 Restoring PostgreSQL..."

POSTGRES_BACKUP_FILE="$RESTORE_DIR/postgres_$BACKUP_TIMESTAMP.sql.gz"

if [ -f "$POSTGRES_BACKUP_FILE" ]; then
    # Drop existing database (with confirmation)
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-postgres}" \
        -c "DROP DATABASE IF EXISTS somaagent_old"
    
    # Rename current to _old
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-postgres}" \
        -c "ALTER DATABASE somaagent RENAME TO somaagent_old" || true
    
    # Create fresh database
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-postgres}" \
        -c "CREATE DATABASE somaagent"
    
    # Restore backup
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
        -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "${POSTGRES_USER:-postgres}" \
        -d somaagent \
        --no-owner \
        --no-acl \
        "$POSTGRES_BACKUP_FILE"
    
    echo "  ✅ PostgreSQL restore complete"
else
    echo "  ⚠️  PostgreSQL backup file not found"
fi

# Restore Redis
echo ""
echo "💾 Restoring Redis..."
REDIS_BACKUP_FILE="$RESTORE_DIR/redis_$BACKUP_TIMESTAMP.rdb"

if [ -f "$REDIS_BACKUP_FILE" ]; then
    redis-cli SHUTDOWN NOSAVE || true
    cp "$REDIS_BACKUP_FILE" /var/lib/redis/dump.rdb
    redis-server --daemonize yes
    echo "  ✅ Redis restore complete"
else
    echo "  ⚠️  Redis backup file not found"
fi

# Verify restoration
echo ""
echo "✅ Verifying restoration..."

# Check ClickHouse
CLICKHOUSE_TABLES=$(clickhouse-client --query="SHOW TABLES FROM somaagent")
echo "  ClickHouse tables restored: $(echo "$CLICKHOUSE_TABLES" | wc -l)"

# Check PostgreSQL
POSTGRES_TABLES=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-postgres}" \
    -d somaagent \
    -c "\dt" | grep -c "public" || echo "0")
echo "  PostgreSQL tables restored: $POSTGRES_TABLES"

# Clean up
rm -rf "$RESTORE_DIR"

echo ""
echo "✅ Restore process completed successfully!"
echo "⚠️  Remember to restart application services"
