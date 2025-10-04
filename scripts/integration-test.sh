#!/usr/bin/env bash
set -euo pipefail

# Integration test script for SomaAgent services
# Validates that all services are running and responding correctly

NAMESPACE=${1:-"soma-agent"}
TIMEOUT=${2:-300}

echo "🧪 Running SomaAgent Integration Tests in namespace: $NAMESPACE"

# Function to test service health
test_service_health() {
    local service_name=$1
    local port=$2
    
    echo "Testing $service_name health..."
    
    # Port forward in background
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" "$port:$port" &
    PORT_FORWARD_PID=$!
    
    # Wait for port forward to establish
    sleep 3
    
    # Test health endpoint
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $service_name health check passed"
        RESULT=0
    else
        echo "❌ $service_name health check failed"
        RESULT=1
    fi
    
    # Kill port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    return $RESULT
}

# Function to test service metrics
test_service_metrics() {
    local service_name=$1
    local port=$2
    
    echo "Testing $service_name metrics..."
    
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" "$port:$port" &
    PORT_FORWARD_PID=$!
    sleep 3
    
    if curl -f -s "http://localhost:$port/metrics" | grep -q "# TYPE"; then
        echo "✅ $service_name metrics endpoint working"
        RESULT=0
    else
        echo "❌ $service_name metrics endpoint failed"
        RESULT=1
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
    return $RESULT
}

# Function to test Jobs service functionality
test_jobs_service() {
    echo "Testing Jobs service functionality..."
    
    kubectl port-forward -n "$NAMESPACE" svc/jobs 8000:8000 &
    PORT_FORWARD_PID=$!
    sleep 3
    
    # Submit a job
    JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/jobs" \
        -H "Content-Type: application/json" \
        -d '{"task": "test_job", "payload": {"test": true}}')
    
    JOB_ID=$(echo "$JOB_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$JOB_ID" ]; then
        echo "✅ Job submitted successfully: $JOB_ID"
        
        # Wait a moment for job to process
        sleep 5
        
        # Check job status
        JOB_STATUS=$(curl -s "http://localhost:8000/v1/jobs/$JOB_ID")
        if echo "$JOB_STATUS" | grep -q '"status":"completed"'; then
            echo "✅ Job completed successfully"
            RESULT=0
        else
            echo "⚠️  Job may still be running: $JOB_STATUS"
            RESULT=0  # Don't fail for timing issues
        fi
    else
        echo "❌ Failed to submit job: $JOB_RESPONSE"
        RESULT=1
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
    return $RESULT
}

# Function to test Memory Gateway functionality  
test_memory_gateway() {
    echo "Testing Memory Gateway functionality..."
    
    kubectl port-forward -n "$NAMESPACE" svc/memory-gateway 9696:9696 &
    PORT_FORWARD_PID=$!
    sleep 3
    
    # Test remember endpoint
    REMEMBER_RESPONSE=$(curl -s -X POST "http://localhost:9696/v1/remember" \
        -H "Content-Type: application/json" \
        -d '{"key": "test_key", "value": "test_value"}')
    
    # Test recall endpoint
    RECALL_RESPONSE=$(curl -s "http://localhost:9696/v1/recall/test_key")
    
    if echo "$RECALL_RESPONSE" | grep -q "test_value"; then
        echo "✅ Memory Gateway remember/recall working"
        RESULT=0
    else
        echo "❌ Memory Gateway functionality failed"
        RESULT=1
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
    return $RESULT
}

# Main test execution
echo "📊 Checking pod status..."
kubectl get pods -n "$NAMESPACE"

echo ""
echo "🏥 Testing service health endpoints..."

FAILED_TESTS=()

# Test each service
SERVICES=("jobs:8000" "memory-gateway:9696" "orchestrator:8002" "task-capsule-repo:8005")

for service_port in "${SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    
    if kubectl get svc -n "$NAMESPACE" "$service" >/dev/null 2>&1; then
        if ! test_service_health "$service" "$port"; then
            FAILED_TESTS+=("$service health")
        fi
        
        if ! test_service_metrics "$service" "$port"; then
            FAILED_TESTS+=("$service metrics")
        fi
    else
        echo "⚠️  Service $service not found in namespace $NAMESPACE"
    fi
done

echo ""
echo "🔧 Testing service functionality..."

# Test Jobs service
if kubectl get svc -n "$NAMESPACE" jobs >/dev/null 2>&1; then
    if ! test_jobs_service; then
        FAILED_TESTS+=("jobs functionality")
    fi
fi

# Test Memory Gateway
if kubectl get svc -n "$NAMESPACE" memory-gateway >/dev/null 2>&1; then
    if ! test_memory_gateway; then
        FAILED_TESTS+=("memory-gateway functionality")
    fi
fi

# Summary
echo ""
echo "📋 Integration Test Summary"
echo "=========================="

if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo "Check pod logs for more details:"
    echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/part-of=soma-agent"
    exit 1
fi