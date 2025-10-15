# SomaAgentHub Testing Guidelines

**A guide to the testing strategy, types of tests, and procedures for SomaAgentHub.**

This document outlines the testing philosophy and practices for the SomaAgentHub project. Writing robust, comprehensive tests is critical for maintaining code quality, preventing regressions, and enabling confident refactoring.

---

## 🎯 Testing Philosophy

- **The Test Pyramid**: We follow the classic test pyramid model, emphasizing a large base of fast unit tests, a smaller layer of integration tests, and a very small layer of end-to-end tests.
- **Automation is Key**: All tests must be automated and run in our CI/CD pipeline.
- **Test for Behavior, Not Implementation**: Tests should verify the public behavior of a component, not its internal implementation details.
- **Code Is Not Done Until It's Tested**: All new features and bug fixes must be accompanied by corresponding tests.

---

## 📊 Types of Tests

### 1. Unit Tests
- **Purpose**: To test individual functions or classes in isolation.
- **Location**: `services/<service-name>/tests/unit/`
- **Framework**: `pytest`
- **Characteristics**:
    - Fast to execute.
    - No external dependencies (databases, APIs, etc.). Dependencies are mocked.
    - Make up the majority (~70%) of our tests.

### 2. Integration Tests
- **Purpose**: To test the interaction between multiple services or between a service and its external dependencies (e.g., a database).
- **Location**: `tests/integration/`
- **Framework**: `pytest` with `docker-compose` for dependencies.
- **Characteristics**:
    - Slower than unit tests.
    - Use real backing services (e.g., a real PostgreSQL database).
    - Verify contracts between services.

### 3. End-to-End (E2E) Tests
- **Purpose**: To test a complete user workflow from the API gateway down to the database.
- **Location**: `tests/e2e/`
- **Framework**: `pytest` with `requests`.
- **Characteristics**:
    - The slowest and most brittle tests.
    - Run against a fully deployed environment (local or staging).
    - Cover critical user paths only.

---

## 🚀 How to Run Tests

The `Makefile` provides convenient targets for running tests.

```bash
# Run all tests (unit, integration, quality checks)
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run only E2E tests
make test-e2e

# Run tests for a specific service
make test-service SERVICE=gateway-api

# Generate a test coverage report
make test-coverage
```

---

## ✍️ How to Write Tests

### Writing Unit Tests
- Use `pytest` fixtures for setup and teardown.
- Use the `unittest.mock` library to patch external dependencies.
- Keep tests focused on a single piece of behavior.

```python
# services/gateway-api/tests/unit/test_example.py
from unittest.mock import patch
from my_service.logic import process_data

@patch("my_service.logic.get_external_data")
def test_process_data_with_mock(mock_get_data):
    """Tests that process_data correctly handles data from a mocked dependency."""
    # Arrange
    mock_get_data.return_value = {"key": "value"}

    # Act
    result = process_data()

    # Assert
    assert result == "processed: value"
    mock_get_data.assert_called_once()
```

### Writing Integration Tests
- Use `docker-compose.test.yml` to define the required services.
- Tests should interact with services via their API endpoints.
- Clean up the database or state between tests to ensure isolation.

```python
# tests/integration/test_gateway_api.py
import requests

def test_health_check_returns_200():
    """Ensures the gateway's /health endpoint is responsive."""
    # Arrange
    gateway_url = "http://localhost:8080"

    # Act
    response = requests.get(f"{gateway_url}/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

---

## 📈 Test Coverage

- **Target**: We aim for a minimum of **80% test coverage** for all new code.
- **How to Check**:
    ```bash
    make test-coverage
    # Open htmlcov/index.html in your browser
    ```
- **Note**: Coverage is a useful metric, but it's not a substitute for writing thoughtful, effective tests.

---
## 🔗 Related Documentation
- **[Contribution Process](contribution-process.md)**: For the full development workflow.
- **[Coding Standards](coding-standards.md)**: For code style and best practices.
```