# Testing Guide

Comprehensive guide for testing the Orchestrator API, including unit tests, integration tests, and testing best practices.

## 📋 Table of Contents

- [Testing Overview](#testing-overview)
- [Test Structure](#test-structure)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Test Configuration](#test-configuration)
- [Coverage and Quality](#coverage-and-quality)
- [Testing Best Practices](#testing-best-practices)

## 🧪 Testing Overview

The Orchestrator API uses a comprehensive testing strategy:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows
- **Performance Tests** - Test performance characteristics

### Testing Framework Stack

| Tool | Purpose | Version |
|------|---------|---------|
| **pytest** | Test framework | 7.4+ |
| **pytest-asyncio** | Async test support | 0.21+ |
| **pytest-cov** | Coverage reporting | 4.1+ |
| **pytest-mock** | Mocking utilities | 3.12+ |
| **httpx** | HTTP client for testing | 0.25+ |

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared test configuration
├── fixtures/                     # Test data and fixtures
│   ├── config.yaml               # Test configuration
│   └── sample_responses.json     # Mock API responses
├── unit/                         # Unit tests (fast, isolated)
│   ├── test_app.py               # Application factory tests
│   ├── test_circuit_breaker.py   # Circuit breaker logic
│   ├── test_config.py            # Configuration management
│   ├── test_health.py            # Health checker
│   ├── test_registry.py          # Endpoint registry
│   └── test_router.py            # Request routing
├── integration/                  # Integration tests (moderate speed)
│   ├── test_api_integration.py   # API endpoint integration
│   ├── test_config_reload.py     # Configuration reloading
│   └── test_health_monitoring.py # Health monitoring integration
└── utils/                       # Test utilities
    ├── fixtures.py              # Shared test fixtures
    └── helpers.py               # Test helper functions
```

## 🔬 Unit Testing

Unit tests focus on individual components in isolation.

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific unit test file
pytest tests/unit/test_registry.py

# Run with verbose output
pytest tests/unit/ -v

# Run specific test function
pytest tests/unit/test_registry.py::test_register_endpoint
```

### Example Unit Test

```python
# tests/unit/test_registry.py
import pytest
from src.orchestrator.registry import EndpointRegistry
from src.orchestrator.models import EndpointConfig


class TestEndpointRegistry:
    """Test cases for the EndpointRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return EndpointRegistry()
    
    @pytest.fixture
    def sample_config(self):
        """Sample endpoint configuration."""
        return EndpointConfig(
            url="https://api.example.com",
            name="test_service",
            methods=["GET", "POST"],
            auth_type="bearer"
        )
    
    def test_register_endpoint_success(self, registry, sample_config):
        """Test successful endpoint registration."""
        # Act
        endpoint = registry.register_endpoint(sample_config)
        
        # Assert
        assert endpoint.endpoint_id == "test_service"
        assert endpoint.config.url == sample_config.url
        assert registry.get_endpoint_count() == 1
    
    def test_register_duplicate_endpoint(self, registry, sample_config):
        """Test registering duplicate endpoint updates existing."""
        # Arrange
        registry.register_endpoint(sample_config)
        
        # Act - register same endpoint again
        updated_config = EndpointConfig(
            url="https://api.example.com",
            name="test_service",
            methods=["GET", "POST", "PUT"],  # Different methods
            auth_type="api_key"              # Different auth
        )
        endpoint = registry.register_endpoint(updated_config)
        
        # Assert
        assert registry.get_endpoint_count() == 1  # Still only one
        assert endpoint.config.methods == ["GET", "POST", "PUT"]
        assert endpoint.config.auth_type == "api_key"
```

## 🔗 Integration Testing

Integration tests verify that components work together correctly.

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_api_integration.py
```

### Example Integration Test

```python
# tests/integration/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from src.orchestrator.app import create_app


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health endpoint returns correct status."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_endpoint_registration(self, client):
        """Test dynamic endpoint registration."""
        # Arrange
        endpoint_config = {
            "config": {
                "url": "https://new-api.example.com",
                "name": "new_service",
                "methods": ["GET", "POST"],
                "auth_type": "bearer"
            }
        }
        
        # Act
        response = client.post("/registry/endpoints", json=endpoint_config)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["endpoint_id"] == "new_service"
```

## 🌐 End-to-End Testing

E2E tests verify complete user workflows and system behavior.

### Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/

# Run specific E2E test
pytest tests/e2e/test_full_workflow.py
```

## ⚙️ Test Configuration

### pytest Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (moderate speed)
    e2e: End-to-end tests (slower)
    slow: Tests that take a long time to run
    asyncio: Async tests
    mock: Tests that use mocking
asyncio_mode = auto
```

### Test Environment Configuration

Create `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from src.orchestrator.app import create_app
from src.orchestrator.models import EndpointConfig


@pytest.fixture
def temp_config_file():
    """Create temporary configuration file for testing."""
    config_data = {
        "endpoints": [
            {
                "url": "https://httpbin.org/get",
                "name": "test_service",
                "methods": ["GET"],
                "auth_type": "none"
            }
        ],
        "circuit_breaker": {
            "failure_threshold": 3,
            "reset_timeout": 30
        },
        "health_check": {
            "enabled": True,
            "interval": 10,
            "timeout": 5
        },
        "log_level": "DEBUG"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def test_client():
    """Create test client for API testing."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_endpoint_configs():
    """Sample endpoint configurations for testing."""
    return [
        EndpointConfig(
            url="https://api1.example.com",
            name="service1",
            methods=["GET", "POST"],
            auth_type="bearer"
        ),
        EndpointConfig(
            url="https://api2.example.com",
            name="service2",
            methods=["GET"],
            auth_type="api_key"
        )
    ]
```

## 📊 Coverage and Quality

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generate coverage report
coverage html

# View coverage report
open htmlcov/index.html

# Check coverage percentage
coverage report --fail-under=80
```

### Quality Metrics

```bash
# Run all quality checks
pytest --cov=src --cov-report=term-missing
black --check src/ tests/
flake8 src/ tests/
mypy src/

# All-in-one quality check script
cat > run_tests.sh << 'EOF'
#!/bin/bash
set -e

echo "Running tests with coverage..."
pytest --cov=src --cov-report=term-missing --cov-report=html

echo "Checking code formatting..."
black --check src/ tests/

echo "Running linter..."
flake8 src/ tests/

echo "Running type checker..."
mypy src/

echo "All checks passed! ✅"
EOF

chmod +x run_tests.sh
./run_tests.sh
```

## ✅ Testing Best Practices

### 1. Test Naming Convention

```python
# Good test names
def test_register_endpoint_with_valid_config_returns_endpoint():
    """Test that registering an endpoint with valid config returns the endpoint."""
    pass

def test_register_endpoint_with_duplicate_name_updates_existing():
    """Test that registering an endpoint with duplicate name updates existing."""
    pass

def test_circuit_breaker_opens_after_threshold_failures():
    """Test that circuit breaker opens after reaching failure threshold."""
    pass
```

### 2. Test Organization

```python
class TestEndpointRegistry:
    """Group related tests in classes."""
    
    class TestRegistration:
        """Nested class for registration-specific tests."""
        
        def test_register_valid_endpoint(self):
            pass
        
        def test_register_invalid_endpoint(self):
            pass
    
    class TestRetrieval:
        """Nested class for retrieval-specific tests."""
        
        def test_get_existing_endpoint(self):
            pass
        
        def test_get_nonexistent_endpoint(self):
            pass
```

### 3. Parameterized Tests

```python
@pytest.mark.parametrize("auth_type,expected", [
    ("bearer", "Authorization: Bearer"),
    ("api_key", "X-API-Key"),
    ("basic", "Authorization: Basic"),
    ("none", None),
])
def test_auth_header_handling(auth_type, expected):
    """Test different authentication header types."""
    # Test implementation
    pass
```

### 4. Async Test Patterns

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async operations properly."""
    # Arrange
    from unittest.mock import AsyncMock
    mock_service = AsyncMock()
    mock_service.process.return_value = "result"
    
    # Act
    result = await mock_service.process()
    
    # Assert
    assert result == "result"
    mock_service.process.assert_called_once()
```

## 📚 Current Test Status

The current project has **202 tests** with **83% coverage**. The tests cover:

- ✅ **Unit Tests**: Core component functionality
- ✅ **Integration Tests**: API endpoint interactions  
- ✅ **Async Tests**: Circuit breaker and health monitoring
- ✅ **Configuration Tests**: YAML loading and validation
- ✅ **Registry Tests**: Endpoint registration and management

### Running Current Tests

```bash
# Run all existing tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📚 Next Steps

- **[Development Setup](development-setup.md)** - Set up your development environment
- **[Contributing Guide](contributing.md)** - Learn the contribution workflow
- **[Architecture Guide](architecture.md)** - Understand the system design

---

**Need help with testing?** Check the existing test files in the `tests/` directory for more examples, or create an issue on GitHub. 