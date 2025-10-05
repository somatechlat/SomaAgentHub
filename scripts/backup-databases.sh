#!/bin/bash
#
# Automated backup script for SomaAgent databases
# Backs up ClickHouse, PostgreSQL, and Redis to S3

set -e

BACKUP_DIR="${BACKUP_DIR:-/tmp/somaagent-backups}"
S3_BUCKET="${S3_BUCKET:-s3://somaagent-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔄 Starting backup process..."
mkdir -p "$BACKUP_DIR"

# Backup ClickHouse
echo ""
echo "📊 Backing up ClickHouse..."
CLICKHOUSE_BACKUP_FILE="$BACKUP_DIR/clickhouse_$TIMESTAMP.tar.gz"

clickhouse-client --query="BACKUP DATABASE somaagent TO Disk('backups', '$TIMESTAMP')" || {
    echo "⚠️  ClickHouse native backup failed, using clickhouse-backup"
    clickhouse-backup create "$TIMESTAMP"
    clickhouse-backup upload "$TIMESTAMP"
}

echo "  ✅ ClickHouse backup complete"

# Backup PostgreSQL
echo ""
echo "🐘 Backing up PostgreSQL..."
POSTGRES_BACKUP_FILE="$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-postgres}" \
    -d somaagent \
    --format=custom \
    --compress=9 \
    --file="$POSTGRES_BACKUP_FILE"

echo "  ✅ PostgreSQL backup complete: $(du -h "$POSTGRES_BACKUP_FILE" | cut -f1)"

# Backup Redis (if using for session/cache)
echo ""
echo "💾 Backing up Redis..."
REDIS_BACKUP_FILE="$BACKUP_DIR/redis_$TIMESTAMP.rdb"

redis-cli --rdb "$REDIS_BACKUP_FILE" || {
    echo "  ⚠️  Redis backup skipped (not running or RDB disabled)"
}

# Upload to S3
echo ""
echo "☁️  Uploading backups to S3..."

aws s3 sync "$BACKUP_DIR" "$S3_BUCKET/backups/$TIMESTAMP/" \
    --storage-class STANDARD_IA \
    --sse AES256

echo "  ✅ Uploaded to $S3_BUCKET/backups/$TIMESTAMP/"

# Clean up old local backups
echo ""
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -type f -mtime +7 -delete
echo "  ✅ Removed local backups older than 7 days"

# Clean up old S3 backups
echo "  🗑️  Removing S3 backups older than $RETENTION_DAYS days..."
CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)

aws s3 ls "$S3_BUCKET/backups/" | while read -r line; do
    backup_date=$(echo "$line" | awk '{print $2}' | cut -d_ -f1 | tr -d '/')
    if [[ "$backup_date" < "$CUTOFF_DATE" ]]; then
        backup_path=$(echo "$line" | awk '{print $2}')
        aws s3 rm "$S3_BUCKET/backups/$backup_path" --recursive
        echo "    Deleted: $backup_path"
    fi
done

echo ""
echo "✅ Backup process completed successfully!"
echo "📦 Backup location: $S3_BUCKET/backups/$TIMESTAMP/"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
