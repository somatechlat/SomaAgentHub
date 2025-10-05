#!/bin/bash
#
# Database migration script for SomaAgent
# Applies ClickHouse and PostgreSQL migrations safely

set -e

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-8123}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-somaagent}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLICKHOUSE_MIGRATIONS_DIR="$SCRIPT_DIR/../infra/clickhouse/migrations"
POSTGRES_MIGRATIONS_DIR="$SCRIPT_DIR/../infra/postgres"

echo "🔄 Starting database migrations..."

# Function to run ClickHouse migration
run_clickhouse_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file")
    
    echo "  📊 Applying ClickHouse migration: $migration_name"
    
    curl -X POST \
        "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" \
        --data-binary @"$migration_file" \
        -H "Content-Type: text/plain" \
        -s -o /dev/null -w "HTTP %{http_code}\n" || {
            echo "❌ Failed to apply ClickHouse migration: $migration_name"
            return 1
        }
}

# Function to run PostgreSQL migration
run_postgres_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file")
    
    echo "  🐘 Applying PostgreSQL migration: $migration_name"
    
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB}" \
        -f "$migration_file" || {
            echo "❌ Failed to apply PostgreSQL migration: $migration_name"
            return 1
        }
}

# Apply ClickHouse migrations
echo ""
echo "📊 ClickHouse Migrations:"
if [ -d "$CLICKHOUSE_MIGRATIONS_DIR" ]; then
    for migration in "$CLICKHOUSE_MIGRATIONS_DIR"/*.sql; do
        if [ -f "$migration" ]; then
            run_clickhouse_migration "$migration"
        fi
    done
else
    echo "  ⚠️  No ClickHouse migrations directory found"
fi

# Apply PostgreSQL migrations
echo ""
echo "🐘 PostgreSQL Migrations:"
if [ -d "$POSTGRES_MIGRATIONS_DIR" ]; then
    for migration in "$POSTGRES_MIGRATIONS_DIR"/*.sql; do
        if [ -f "$migration" ]; then
            run_postgres_migration "$migration"
        fi
    done
else
    echo "  ⚠️  No PostgreSQL migrations directory found"
fi

# Verify migrations
echo ""
echo "✅ Verifying migrations..."

# Check ClickHouse tables
CLICKHOUSE_TABLES=$(curl -s "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/?query=SHOW TABLES")
echo "  ClickHouse tables: $(echo "$CLICKHOUSE_TABLES" | tr '\n' ', ')"

# Check PostgreSQL tables
if command -v psql &> /dev/null; then
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB}" \
        -c "\dt" 2>/dev/null | grep -v "No relations found" && echo "  PostgreSQL tables verified" || true
fi

echo ""
echo "✅ Database migrations completed successfully!"
