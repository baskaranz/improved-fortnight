# Developer Guide - Orchestrator API

**For Contributors, Developers, and Anyone Contributing Code**

Welcome! This guide will help you understand the codebase, set up your development environment, and contribute effectively.

## 🏗️ What You're Working With

The Orchestrator API is a **FastAPI-based microservice gateway** built with:

- **FastAPI** - Modern async Python web framework
- **Pydantic** - Data validation and settings management
- **HTTPX** - Async HTTP client for service communication
- **Circuit Breaker Pattern** - Fault tolerance and resilience
- **Health Monitoring** - Automated endpoint health checking
- **Dynamic Configuration** - Hot-reloading YAML configuration

## 🚀 Quick Development Setup

### Option 1: Docker Development (Recommended)

```bash
git clone <repository-url>
cd yet-another-orch-api

# Quick setup with hot reload
make setup
# OR
docker-compose --profile dev up -d orchestrator-dev
```

### Option 2: Python Development

```bash
git clone <repository-url>
cd yet-another-orch-api
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**Verify setup:**
```bash
# Docker
curl http://localhost:8000/health

# Python  
pytest
python main.py --reload --log-level debug
```

➡️ **[Complete Development Setup Guide →](development-setup.md)**

## 📋 Developer Documentation

| Guide | Description | When to Use |
|-------|-------------|-------------|
| **[Development Setup](development-setup.md)** | Complete local development environment | First-time setup |
| **[Architecture](architecture.md)** | System architecture and design | Understanding the codebase |
| **[Testing](testing.md)** | Running and writing tests | Before submitting PRs |
| **[Contributing](contributing.md)** | Contribution guidelines and workflow | When submitting code |
| **[Design Decisions](design-decisions.md)** | Why we built it this way | Understanding trade-offs |
| **[Release Process](release-process.md)** | How releases are made | For maintainers |

## 🏛️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │────│  Orchestrator   │────│ Backend Service │
│                 │    │      API        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
               ┌─────────┐ ┌─────────┐ ┌─────────┐
               │Registry │ │ Health  │ │Circuit  │
               │         │ │Checker  │ │Breaker  │
               └─────────┘ └─────────┘ └─────────┘
```

### Core Components

- **Request Router** (`router.py`) - Routes incoming requests to backend services
- **Registry** (`registry.py`) - Manages registered endpoints and their metadata
- **Health Checker** (`health.py`) - Monitors endpoint availability  
- **Circuit Breaker** (`circuit_breaker.py`) - Provides fault tolerance
- **Configuration Manager** (`config.py`) - Handles YAML config and hot-reloading

➡️ **[Detailed Architecture Guide →](architecture.md)**

## 🧪 Testing Strategy

We use a comprehensive testing approach:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete request flows

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

➡️ **[Complete Testing Guide →](testing.md)**

## 🔄 Development Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and add tests:**
   ```bash
   # Add your code changes
   # Add corresponding tests
   pytest  # Verify tests pass
   ```

3. **Run code quality checks:**
   ```bash
   black src/ tests/         # Format code
   flake8 src/ tests/        # Lint code  
   mypy src/                 # Type checking
   ```

4. **Submit pull request** with:
   - Clear description of changes
   - Tests covering new functionality
   - Updated documentation if needed

➡️ **[Complete Contributing Guide →](contributing.md)**

## 🔍 Key Development Areas

### Adding New API Endpoints
1. Add route handler in appropriate `*_api.py` file
2. Add corresponding business logic in core modules
3. Add unit and integration tests
4. Update OpenAPI documentation

### Extending Health Monitoring
1. Modify `health.py` for new health check types
2. Update `health_api.py` for new endpoints
3. Add tests for new functionality
4. Consider circuit breaker integration

### Adding Configuration Options
1. Update models in `models.py`
2. Modify `config.py` for new config handling
3. Add validation and tests
4. Update documentation

## 🐛 Debugging & Development Tools

### Development Server
```bash
# Auto-reload on code changes
python main.py --reload --log-level debug

# Enable detailed logging
python main.py --log-level debug
```

### Interactive API Testing
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Code Quality Tools
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security checks
bandit -r src/
```

## 📊 Performance Considerations

- **Async/Await**: All I/O operations use async patterns
- **Connection Pooling**: HTTPX client reuses connections
- **Circuit Breakers**: Prevent cascading failures
- **Health Monitoring**: Configurable intervals to balance accuracy vs performance

## 🔐 Security Considerations

- **Input Validation**: All inputs validated with Pydantic
- **Authentication Passthrough**: Headers forwarded to backend services
- **No Secret Storage**: Service doesn't store authentication secrets
- **CORS Configuration**: Configurable for production environments

## 🆘 Getting Help

- **Architecture questions**: Check [Architecture Guide](architecture.md)
- **Development setup issues**: See [Development Setup](development-setup.md)
- **Testing problems**: Review [Testing Guide](testing.md)
- **Contribution questions**: Check [Contributing Guide](contributing.md)
- **Code discussions**: Create a GitHub issue

## 📈 Next Steps

1. **New contributor?** → [Development Setup](development-setup.md)
2. **Want to understand the code?** → [Architecture Guide](architecture.md)
3. **Ready to contribute?** → [Contributing Guide](contributing.md)
4. **Working on tests?** → [Testing Guide](testing.md) 