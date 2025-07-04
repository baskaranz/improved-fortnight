# Contributing Guide

Welcome! We're excited that you want to contribute to the Orchestrator API. This guide will help you get started with contributing code, documentation, or other improvements.

## 🚀 Quick Start for Contributors

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/yet-another-orch-api.git
   cd yet-another-orch-api
   ```

2. **Set up development environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Run tests to verify setup:**
   ```bash
   pytest
   ```

4. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📋 Development Workflow

### 1. Development Environment Setup

**Dependencies:**
```bash
# Install all dependencies including dev tools
pip install -e ".[dev]"

# Verify installation
python -c "import src.orchestrator; print('Import successful')"
pytest --version
black --version
```

**IDE Configuration:**
```bash
# VS Code settings (optional)
mkdir -p .vscode
cat > .vscode/settings.json << EOF
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"]
}
EOF
```

### 2. Making Changes

**Code Style:**
We follow Python community standards:
- **Black** for code formatting
- **Flake8** for linting  
- **MyPy** for type checking
- **Line length**: 100 characters
- **Imports**: Use isort for import sorting

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Import sorting
isort src/ tests/
```

**Commit Messages:**
Use conventional commit format:
```
type(scope): description

feat(router): add support for custom headers
fix(health): resolve circuit breaker state sync issue
docs(api): update endpoint registration examples
test(registry): add tests for bulk endpoint operations
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### 3. Testing Requirements

**All changes must include appropriate tests:**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run specific test file
pytest tests/unit/test_router.py

# Run tests matching pattern
pytest -k "test_health"
```

**Test Coverage Requirements:**
- **Minimum coverage**: 85%
- **New code**: 95% coverage required
- **Critical paths**: 100% coverage (auth, routing, health)

### 4. Pull Request Process

**Before submitting:**
```bash
# 1. Ensure all tests pass
pytest

# 2. Run code quality checks
black src/ tests/
flake8 src/ tests/
mypy src/
isort src/ tests/

# 3. Update documentation if needed
# 4. Add changelog entry if significant change
```

**Pull Request Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly marked)
```

## 🏗️ Architecture Contributions

### Adding New Features

**1. API Endpoints:**
```python
# 1. Create new router file
# src/orchestrator/new_feature_api.py

from fastapi import APIRouter, Depends
from .models import SomeModel

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/endpoint")
async def new_endpoint():
    return {"message": "Hello from new feature"}

# 2. Add to main app
# src/orchestrator/app.py
from .new_feature_api import router as new_feature_router
app.include_router(new_feature_router)

# 3. Add tests
# tests/unit/test_new_feature_api.py
def test_new_endpoint():
    # Test implementation
    pass
```

**2. Core Components:**
```python
# 1. Create component
# src/orchestrator/new_component.py

class NewComponent:
    def __init__(self, config):
        self.config = config
    
    async def do_something(self):
        # Implementation
        pass

# 2. Add to app lifecycle
# src/orchestrator/app.py
async def lifespan(app: FastAPI):
    # Initialize component
    new_component = NewComponent(config)
    # Add cleanup in finally block
```

**3. Configuration Options:**
```python
# 1. Add to models
# src/orchestrator/models.py

class NewFeatureConfig(BaseModel):
    enabled: bool = Field(default=True)
    setting: str = Field(default="default_value")

class OrchestratorConfig(BaseModel):
    # ... existing fields ...
    new_feature: NewFeatureConfig = Field(default_factory=NewFeatureConfig)

# 2. Update default config
# src/orchestrator/config.py - in _save_default_config()
```

### Code Guidelines

**Error Handling:**
```python
# Good: Specific exceptions with context
try:
    result = await external_service.call()
except httpx.TimeoutException:
    logger.warning(f"Timeout calling {service_name}")
    raise HTTPException(status_code=504, detail="Service timeout")
except httpx.ConnectError as e:
    logger.error(f"Connection error to {service_name}: {e}")
    raise HTTPException(status_code=502, detail="Service unavailable")

# Good: Log with context
logger.info(f"Endpoint {endpoint_id} health check completed", 
           extra={"endpoint_id": endpoint_id, "response_time": response_time})
```

**Async/Await Patterns:**
```python
# Good: Proper async context management
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Good: Concurrent operations
tasks = [check_endpoint(ep) for ep in endpoints]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Good: Proper cleanup
try:
    await some_operation()
finally:
    await cleanup_resources()
```

**Type Hints:**
```python
# Good: Complete type hints
async def process_request(
    request: Request, 
    endpoint: RegisteredEndpoint
) -> Response:
    # Implementation
    pass

# Good: Optional and Union types
def get_endpoint(endpoint_id: str) -> Optional[RegisteredEndpoint]:
    return self._endpoints.get(endpoint_id)
```

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.orchestrator.example import ExampleClass

class TestExampleClass:
    """Test suite for ExampleClass."""
    
    @pytest.fixture
    def example_instance(self):
        """Create test instance."""
        return ExampleClass(config=Mock())
    
    async def test_async_method(self, example_instance):
        """Test async method with proper mocking."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.call.return_value = {"result": "success"}
        
        # Act
        result = await example_instance.process(mock_service)
        
        # Assert
        assert result["status"] == "success"
        mock_service.call.assert_called_once()
    
    def test_error_handling(self, example_instance):
        """Test error handling scenarios."""
        with pytest.raises(ValueError, match="Invalid input"):
            example_instance.validate("invalid_input")
```

### Integration Testing

```python
# tests/integration/test_health_circuit_breaker.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_affects_circuit_breaker(test_app):
    """Test integration between health checker and circuit breaker."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Setup unhealthy endpoint
        # Verify circuit breaker opens
        # Test recovery
        pass
```

### Mock Guidelines

```python
# Good: Mock external dependencies
@pytest.fixture
def mock_httpx_client():
    with patch('src.orchestrator.router.httpx.AsyncClient') as mock:
        yield mock

# Good: Mock specific methods
@patch('src.orchestrator.health.HealthChecker._check_endpoint_health')
async def test_health_check_success(mock_check, health_checker):
    mock_check.return_value = EndpointHealth(...)
    # Test implementation
```

## 📝 Documentation Contributions

### Code Documentation

```python
class RequestRouter:
    """Routes incoming requests to registered backend services.
    
    The RequestRouter handles the core orchestration logic, including:
    - Dynamic route matching based on endpoint configuration
    - Circuit breaker integration for fault tolerance
    - Request/response header filtering and processing
    
    Attributes:
        registry: EndpointRegistry instance for endpoint management
        circuit_breaker_manager: Optional CircuitBreakerManager for fault tolerance
        proxy: EndpointProxy for HTTP request forwarding
    """
    
    async def route_request(self, request: Request, path: str) -> Response:
        """Route incoming request to appropriate backend service.
        
        Args:
            request: The incoming FastAPI Request object
            path: The URL path to route (without /orchestrator prefix)
            
        Returns:
            Response object with forwarded response from backend service
            
        Raises:
            HTTPException: If no endpoint found, endpoint unhealthy, or other routing errors
            
        Example:
            >>> router = RequestRouter(registry, circuit_breaker_manager)
            >>> response = await router.route_request(request, "user_service/users")
        """
```

### API Documentation

Update OpenAPI documentation by ensuring:
- All endpoints have proper descriptions
- Request/response models are documented
- Examples are provided for complex operations
- Error responses are documented

### User Documentation

When making user-facing changes:
- Update relevant user guide sections
- Add examples to quick start if applicable
- Update troubleshooting guide for new error scenarios
- Add configuration examples if new options added

## 🔄 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Changelog

Update `CHANGELOG.md` with:
```markdown
## [Unreleased]

### Added
- New circuit breaker fallback strategies
- Support for custom health check intervals per endpoint

### Changed
- Improved error messages for configuration validation

### Fixed
- Fixed race condition in health checker startup

### Security
- Updated dependencies to address security vulnerabilities
```

## 🐛 Bug Reports

### Creating Good Bug Reports

Include:
1. **Environment**: Python version, OS, dependencies
2. **Steps to reproduce**: Minimal example
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Configuration**: Relevant config (sanitized)
6. **Logs**: Error messages and stack traces

**Template:**
```markdown
**Environment:**
- Python version: 3.11
- OS: Ubuntu 20.04
- Orchestrator version: 0.1.0

**Steps to reproduce:**
1. Configure endpoint with timeout: 5
2. Send request to slow endpoint
3. Observe behavior

**Expected:** Request should timeout after 5 seconds
**Actual:** Request hangs indefinitely

**Configuration:**
```yaml
endpoints:
  - url: "https://slow-api.com"
    timeout: 5
```

**Logs:**
```
ERROR - Request timeout handling failed
```
```

## 🎯 Feature Requests

### Proposing New Features

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** the feature would solve
3. **Propose a solution** with implementation details
4. **Consider alternatives** and trade-offs
5. **Discuss breaking changes** if any

**Template:**
```markdown
**Problem:**
Currently, circuit breakers use fixed timeouts. Different services may need different recovery times.

**Proposed Solution:**
Add per-endpoint circuit breaker configuration:

```yaml
endpoints:
  - url: "https://fast-service.com"
    circuit_breaker:
      reset_timeout: 30
  - url: "https://slow-service.com"  
    circuit_breaker:
      reset_timeout: 300
```

**Implementation:**
- Extend EndpointConfig model
- Update CircuitBreakerManager to use per-endpoint config
- Maintain backward compatibility with global config
```

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Give constructive feedback** in code reviews
- **Credit contributors** for their work
- **Focus on the code**, not the person

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code discussions and reviews
- **Discussions**: General questions and design discussions

### Recognition

Contributors are recognized in:
- Release notes for significant contributions
- README contributors section
- Project documentation

## 📈 Getting Started

### Good First Issues

Look for issues labeled:
- `good first issue`: Simple, well-defined tasks
- `documentation`: Documentation improvements
- `tests`: Test coverage improvements
- `help wanted`: Community input needed

### Areas We Need Help

- **Testing**: Increase test coverage
- **Documentation**: User guides and examples
- **Performance**: Optimization and benchmarking
- **Features**: Circuit breaker enhancements, monitoring
- **DevOps**: CI/CD improvements, Docker, Kubernetes

## 💡 Tips for Success

1. **Start small**: Begin with documentation or simple bug fixes
2. **Ask questions**: Don't hesitate to ask for clarification
3. **Read the code**: Understand existing patterns before adding new ones
4. **Test thoroughly**: Include edge cases and error scenarios
5. **Document changes**: Help others understand your work

Thank you for contributing to the Orchestrator API! Your contributions help make this project better for everyone. 