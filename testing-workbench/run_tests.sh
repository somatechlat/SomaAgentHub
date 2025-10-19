#!/bin/bash
# Testing Workbench Test Runner

set -e

echo "=== SomaAgentHub Testing Workbench ==="
echo

# Check if services are running
echo "Checking if services are running..."
if curl -s http://localhost:10000/health > /dev/null 2>&1; then
    echo "✓ Gateway API is running"
else
    echo "✗ Gateway API not running on port 10000"
fi

if curl -s http://localhost:10001/health > /dev/null 2>&1; then
    echo "✓ Orchestrator is running"
else
    echo "✗ Orchestrator not running on port 10001"
fi

if curl -s http://localhost:10002/health > /dev/null 2>&1; then
    echo "✓ Identity Service is running"
else
    echo "✗ Identity Service not running on port 10002"
fi

echo

# Run tests based on argument
case "${1:-all}" in
    "unit")
        echo "Running unit tests..."
        pytest unit/ -v
        ;;
    "integration")
        echo "Running integration tests..."
        pytest integration/ -v
        ;;
    "e2e")
        echo "Running end-to-end tests..."
        pytest e2e/ -v
        ;;
    "smoke")
        echo "Running smoke tests..."
        pytest smoke/ -v
        ;;
    "all")
        echo "Running all tests..."
        pytest . -v
        ;;
    *)
        echo "Usage: $0 [unit|integration|e2e|smoke|all]"
        exit 1
        ;;
esac