#!/bin/bash
set -e

echo "🚀 Starting Temporal cluster and MAO service..."

# Start Temporal cluster
echo "📦 Starting Temporal cluster (Docker Compose)..."
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaagent/infra/temporal
docker-compose up -d

# Wait for Temporal to be ready
echo "⏳ Waiting for Temporal server to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:7233 > /dev/null 2>&1; then
        echo "✅ Temporal server is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Temporal server failed to start"
    exit 1
fi

# Open Temporal UI
echo "🌐 Temporal UI available at: http://localhost:8088"

# Start MAO worker
echo "🤖 Starting MAO worker..."
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaagent/services/mao-service
python worker.py &
WORKER_PID=$!

# Start MAO API service
echo "🌐 Starting MAO API service..."
python app/main.py &
API_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "   📊 Temporal UI:    http://localhost:8088"
echo "   🔌 MAO API:        http://localhost:8007"
echo "   📖 API Docs:       http://localhost:8007/docs"
echo ""
echo "   Worker PID: $WORKER_PID"
echo "   API PID:    $API_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Trap Ctrl+C to cleanup
trap "echo '🛑 Stopping services...'; kill $WORKER_PID $API_PID; docker-compose -f /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaagent/infra/temporal/docker-compose.yml down; exit 0" INT

# Wait
wait
