#!/usr/bin/env bash
set -euo pipefail

# Create Kafka topics for SomaAgentHub event pipeline
# Run from: kubectl exec -it kafka-0 -n kafka-system -- bash

BROKER="localhost:9092"

echo "🔧 Creating Kafka topics..."

# 1. Audit logs topic
kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic soma-audit-logs \
  --partitions 3 \
  --replication-factor 3 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete

echo "✅ Created: soma-audit-logs"

# 2. Metrics topic
kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic soma-metrics \
  --partitions 6 \
  --replication-factor 3 \
  --config retention.ms=86400000 \
  --config cleanup.policy=delete

echo "✅ Created: soma-metrics"

# 3. Traces topic
kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic soma-traces \
  --partitions 6 \
  --replication-factor 3 \
  --config retention.ms=86400000 \
  --config cleanup.policy=delete

echo "✅ Created: soma-traces"

# 4. Events topic
kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic soma-events \
  --partitions 3 \
  --replication-factor 3 \
  --config retention.ms=259200000

echo "✅ Created: soma-events"

# 5. DLQ (Dead Letter Queue)
kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic soma-dlq \
  --partitions 1 \
  --replication-factor 3

echo "✅ Created: soma-dlq"

# List all topics
echo ""
echo "📋 All topics:"
kafka-topics --bootstrap-server "$BROKER" --list | grep soma
