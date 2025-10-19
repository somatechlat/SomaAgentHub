# Testing Workbench

Centralized testing for SomaAgentHub - all tests consolidated here.

## Structure

```
testing-workbench/
├── unit/           # Individual service unit tests
├── integration/    # Cross-service integration tests  
├── e2e/           # End-to-end workflow tests
├── smoke/         # Deployment verification tests
├── fixtures/      # Shared test fixtures and data
├── conftest.py    # Pytest configuration
└── README.md      # This file
```

## Running Tests

```bash
# All tests
pytest testing-workbench/

# Specific category
pytest testing-workbench/unit/
pytest testing-workbench/integration/
pytest testing-workbench/e2e/

# Specific service
pytest testing-workbench/unit/test_gateway_api.py
```

## Test Categories

- **Unit**: Test individual service functionality
- **Integration**: Test service-to-service communication
- **E2E**: Test complete user workflows
- **Smoke**: Verify deployment health