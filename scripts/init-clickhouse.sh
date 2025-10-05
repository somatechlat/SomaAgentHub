#!/bin/bash
# Initialize ClickHouse database with schema and sample data
# Sprint-7: Analytics database setup

set -e

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-9000}"
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🗄️  ClickHouse Initialization"
echo "============================"
echo "Host: $CLICKHOUSE_HOST:$CLICKHOUSE_PORT"
echo ""

# Check ClickHouse connection
echo "✓ Checking ClickHouse connection..."
if ! clickhouse-client --host "$CLICKHOUSE_HOST" --port "$CLICKHOUSE_PORT" --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --query "SELECT 1" &> /dev/null; then
    echo "❌ Cannot connect to ClickHouse at $CLICKHOUSE_HOST:$CLICKHOUSE_PORT"
    echo "   Please ensure ClickHouse is running"
    exit 1
fi
echo "   ✓ Connected successfully"
echo ""

# Load main schema
echo "📝 Loading main schema..."
clickhouse-client \
    --host "$CLICKHOUSE_HOST" \
    --port "$CLICKHOUSE_PORT" \
    --user "$CLICKHOUSE_USER" \
    --password "$CLICKHOUSE_PASSWORD" \
    --multiquery < "$PROJECT_ROOT/infra/clickhouse/schema.sql"
echo "   ✓ Schema loaded"
echo ""

# Run migrations
echo "🔄 Running migrations..."
clickhouse-client \
    --host "$CLICKHOUSE_HOST" \
    --port "$CLICKHOUSE_PORT" \
    --user "$CLICKHOUSE_USER" \
    --password "$CLICKHOUSE_PASSWORD" \
    --multiquery < "$PROJECT_ROOT/infra/clickhouse/migrations/001_initial_schema.sql"
echo "   ✓ Migrations complete"
echo ""

# Load sample data (if requested)
if [ "${LOAD_SAMPLE_DATA:-false}" = "true" ]; then
    echo "📊 Loading sample data..."
    clickhouse-client \
        --host "$CLICKHOUSE_HOST" \
        --port "$CLICKHOUSE_PORT" \
        --user "$CLICKHOUSE_USER" \
        --password "$CLICKHOUSE_PASSWORD" \
        --multiquery < "$PROJECT_ROOT/infra/clickhouse/seeds/sample_data.sql"
    echo "   ✓ Sample data loaded"
    echo ""
fi

# Verify tables
echo "📋 Verifying tables..."
clickhouse-client \
    --host "$CLICKHOUSE_HOST" \
    --port "$CLICKHOUSE_PORT" \
    --user "$CLICKHOUSE_USER" \
    --password "$CLICKHOUSE_PASSWORD" \
    --query "SELECT name, engine, total_rows FROM system.tables WHERE database = 'somaagent' FORMAT PrettyCompact"
echo ""

echo "✅ ClickHouse initialization complete!"
echo ""
echo "Next steps:"
echo "  1. Configure analytics-service to connect to ClickHouse"
echo "  2. Test data ingestion"
echo "  3. Create Grafana datasource for ClickHouse"
echo ""
