#!/bin/bash
set -e

echo "🧪 Running Governance Service Tests"

# Change to the service directory
cd "$(dirname "$0")/.."

# Install test dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

echo "📦 Installing test dependencies..."
source venv/bin/activate
pip install -r tests/requirements-test.txt

# Set environment variables for testing
export ENVIRONMENT="test"
export LOG_LEVEL="DEBUG"
export VAULT_URL="http://localhost:8200"
export VAULT_TOKEN="test-token"

# Run tests with coverage
echo "🔍 Running test suite..."
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report available in htmlcov/"
else
    echo "❌ Tests failed!"
    exit 1
fi

# Run linting if requested
if [ "$1" = "--lint" ]; then
    echo "🔍 Running linting..."
    python -m flake8 app/ tests/
    python -m black --check app/ tests/
    python -m isort --check-only app/ tests/
fi

echo "🎉 Test execution complete!"