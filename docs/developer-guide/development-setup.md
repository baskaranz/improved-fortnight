# Development Setup

Complete guide for setting up a local development environment for the Orchestrator API.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Installation](#development-installation)
- [IDE Configuration](#ide-configuration)
- [Code Quality Tools](#code-quality-tools)
- [Testing Setup](#testing-setup)
- [Development Workflow](#development-workflow)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.9+ | 3.11+ |
| **pip** | 21.0+ | Latest |
| **Git** | 2.0+ | Latest |
| **RAM** | 4GB | 8GB+ |
| **Disk Space** | 1GB | 2GB+ |

### Development Tools

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check Git version
git --version
```

### Operating System Support

- ✅ **macOS** (10.15+)
- ✅ **Linux** (Ubuntu 18.04+, CentOS 7+)
- ✅ **Windows** (Windows 10+ with WSL2 recommended)

## 🌍 Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/yet-another-orch-api.git
cd yet-another-orch-api

# Or clone your fork
git clone https://github.com/YOUR-USERNAME/yet-another-orch-api.git
cd yet-another-orch-api

# Add upstream remote (for forks)
git remote add upstream https://github.com/original-repo/yet-another-orch-api.git
```

### 2. Choose Your Development Environment

**Option A: Docker Development (Recommended)**
- ✅ Consistent environment across all developers
- ✅ No local Python setup required
- ✅ Matches production environment
- ✅ Includes hot reload for development

**Option B: Local Python Development**  
- ✅ Direct access to Python tools
- ✅ Faster iteration for some workflows
- ✅ Better IDE integration for debugging

## 🐳 Docker Development Setup

### Prerequisites for Docker
- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience)

### Quick Docker Setup

```bash
# Option 1: Using Make (recommended)
make setup
# This will build and start the development environment

# Option 2: Using Docker Compose directly
docker-compose --profile dev up -d orchestrator-dev

# Option 3: Manual Docker commands
docker build -t orchestrator-api .
docker run -d \
  --name orchestrator-dev \
  -p 8000:8000 \
  -v $(pwd):/app \
  orchestrator-api \
  python main.py --reload --log-level debug
```

### Docker Development Commands

```bash
# Start development environment with hot reload
make run-dev
# OR
docker-compose --profile dev up -d orchestrator-dev

# View logs
make logs-dev
# OR  
docker-compose logs -f orchestrator-dev

# Run tests in container
make test
# OR
docker-compose exec orchestrator-dev python -m pytest

# Access container shell
make shell
# OR
docker-compose exec orchestrator-dev /bin/bash

# Stop development environment
make stop
# OR
docker-compose down
```

### Verify Docker Setup

```bash
# Check container is running
docker ps

# Test health endpoint
curl http://localhost:8000/health

# Test API documentation
open http://localhost:8000/docs
```

### Docker Development Benefits

- **Hot Reload**: Code changes automatically trigger server restart
- **Consistent Environment**: Same Python version and dependencies
- **No Local Setup**: No need to install Python or manage virtual environments
- **Production Parity**: Container matches production environment

> **📖 Complete Docker Guide**: For more Docker options, see [DOCKER.md](../../DOCKER.md)

## 🐍 Local Python Development Setup

### 2. Create Virtual Environment

#### Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Verify activation
which python
# Should show: /path/to/project/venv/bin/python
```

#### Using conda (Alternative)

```bash
# Create conda environment
conda create -n orchestrator python=3.11
conda activate orchestrator
```

### 3. Verify Environment

```bash
# Check Python version in virtual environment
python --version

# Check pip is using virtual environment
which pip
pip --version
```

## 📦 Development Installation

### 1. Install Development Dependencies

```bash
# Install the package in development mode with all dependencies
pip install -e ".[dev]"

# Or step by step:
pip install -e .                    # Install package in development mode
pip install pytest pytest-asyncio   # Testing framework
pip install pytest-cov              # Coverage reporting
pip install black flake8 mypy       # Code quality tools
pip install httpx[dev]              # HTTP client with development extras
pip install pytest-mock             # Mocking for tests
```

### 2. Verify Installation

```bash
# Test basic imports
python -c "
import src.orchestrator
from src.orchestrator.app import create_app
print('✅ Basic imports successful')
"

# Run application help
python main.py --help

# Check development tools
black --version
flake8 --version
mypy --version
pytest --version
```

### 3. Install Pre-commit Hooks (Optional but Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

## 🔧 IDE Configuration

### Visual Studio Code

#### Recommended Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "ms-vscode.test-adapter-converter",
    "littlefoxteam.vscode-python-test-adapter",
    "ms-vscode.vscode-json"
  ]
}
```

#### Settings (.vscode/settings.json)

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".mypy_cache": true,
    ".pytest_cache": true,
    "htmlcov": true
  }
}
```

#### Launch Configuration (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Orchestrator",
      "type": "python",
      "request": "launch",
      "program": "main.py",
      "args": ["--log-level", "debug", "--reload"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Run Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

### PyCharm

#### Project Setup

1. **Open Project**: File → Open → Select project directory
2. **Set Interpreter**: File → Settings → Project → Python Interpreter → Add → Existing Environment → Select `venv/bin/python`
3. **Enable pytest**: Settings → Tools → Python Integrated Tools → Testing → Default test runner: pytest
4. **Configure Code Style**: Settings → Editor → Code Style → Python → Use Black formatter

#### Run Configurations

**Orchestrator Service:**
- Script path: `main.py`
- Parameters: `--log-level debug --reload`
- Working directory: project root

**Tests:**
- Target: Custom
- Target: `tests/`
- Additional arguments: `-v --cov=src`

## 🎯 Code Quality Tools

### Code Formatting with Black

```bash
# Format all Python files
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Format with custom line length
black --line-length 88 src/ tests/
```

### Linting with Flake8

```bash
# Lint all Python files
flake8 src/ tests/

# Lint with specific configuration
flake8 --max-line-length=88 --extend-ignore=E203,W503 src/ tests/
```

### Type Checking with MyPy

```bash
# Type check source code
mypy src/

# Type check with specific configuration
mypy --strict src/
```

### Pre-commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

## 🧪 Testing Setup

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared test configuration
├── unit/                    # Unit tests
│   ├── test_app.py
│   ├── test_config.py
│   ├── test_registry.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_api_integration.py
│   └── ...
├── e2e/                     # End-to-end tests
│   ├── test_full_workflow.py
│   └── ...
└── utils/                   # Test utilities
    ├── fixtures.py
    └── helpers.py
```

### Running Tests

#### Docker Testing

```bash
# Run all tests in container
make test
# OR
docker-compose exec orchestrator-dev python -m pytest

# Run with coverage
docker-compose exec orchestrator-dev python -m pytest --cov=src --cov-report=term-missing

# Run specific test file
docker-compose exec orchestrator-dev python -m pytest tests/unit/test_app.py

# Run tests with verbose output
docker-compose exec orchestrator-dev python -m pytest -v

# Run tests interactively (for debugging)
docker-compose exec orchestrator-dev python -m pytest -s --pdb
```

#### Local Python Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_app.py

# Run specific test function
pytest tests/unit/test_app.py::test_create_app

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests with coverage and missing lines
pytest --cov=src --cov-report=term-missing

# Run tests in parallel (faster)
pip install pytest-xdist
pytest -n auto
```

### Test Configuration

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
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take a long time to run
```

## 🔄 Development Workflow

### 1. Start Development Environment

#### Docker Workflow

```bash
# Start development environment with hot reload
make run-dev
# OR
docker-compose --profile dev up -d orchestrator-dev

# View logs in real-time
make logs-dev
# OR
docker-compose logs -f orchestrator-dev

# In another terminal, run tests
make test
```

#### Python Workflow

```bash
# Activate virtual environment
source venv/bin/activate

# Start the service in development mode
python main.py --reload --log-level debug

# In another terminal, run tests in watch mode
pytest-watch -- tests/
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Edit files in src/orchestrator/

# Run tests
pytest

# Check code quality
black src/ tests/
flake8 src/ tests/
mypy src/

# Commit changes
git add .
git commit -m "feat: add your feature description"
```

### 3. Testing Changes

```bash
# Run specific tests related to your changes
pytest tests/unit/test_your_module.py

# Run integration tests
pytest tests/integration/

# Test with different configurations
CONFIG_PATH=tests/fixtures/test_config.yaml python main.py --port 8001
```

### 4. Performance Testing

```bash
# Start service
python main.py &
SERVICE_PID=$!

# Run performance tests
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health

# Load testing with ApacheBench (if installed)
ab -n 1000 -c 10 http://localhost:8000/health

# Stop service
kill $SERVICE_PID
```

## 🐛 Debugging

### Debug Configuration

#### Environment Variables

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Enable Python debug mode
export PYTHONDEBUG=1

# Enable asyncio debug mode
export PYTHONASYNCIODEBUG=1
```

#### Debug with PDB

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+)
breakpoint()
```

#### Debug with IDE

**VS Code:**
1. Set breakpoints in the editor
2. Press F5 or use "Run and Debug" panel
3. Select "Run Orchestrator" configuration

**PyCharm:**
1. Set breakpoints in the editor
2. Right-click on `main.py` → Debug 'main'

### Debug Tips

```bash
# Debug specific test
pytest -s tests/unit/test_app.py::test_specific_function

# Debug with pdb on test failure
pytest --pdb tests/

# Debug HTTP requests
curl -v http://localhost:8000/health

# Debug with HTTPie (if installed)
pip install httpie
http GET localhost:8000/health
```

## 🔍 Logging and Monitoring

### Development Logging

```bash
# Start with debug logging
python main.py --log-level debug

# Filter logs
python main.py --log-level debug 2>&1 | grep "ERROR\|WARNING"

# Save logs to file
python main.py --log-level debug > logs/app.log 2>&1
```

### Health Check During Development

```bash
# Monitor health while developing
watch -n 2 'curl -s http://localhost:8000/health | jq'

# Monitor specific endpoint
watch -n 5 'curl -s http://localhost:8000/health/endpoints/your_test_endpoint'
```

## 🚨 Troubleshooting

### Common Issues

#### Virtual Environment Issues

```bash
# Problem: Command not found after activation
# Solution: Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

#### Import Errors

```bash
# Problem: ModuleNotFoundError
# Solution: Check PYTHONPATH and installation
echo $PYTHONPATH
pip list | grep orchestrator

# Reinstall in development mode
pip install -e .
```

#### Port Already in Use

```bash
# Problem: Port 8000 already in use
# Solution: Find and kill process or use different port
lsof -i :8000
kill -9 $(lsof -t -i:8000)

# Or use different port
python main.py --port 8001
```

#### Test Failures

```bash
# Problem: Tests fail due to async issues
# Solution: Check pytest-asyncio installation
pip install pytest-asyncio

# Run with more verbose output
pytest -vvv --tb=long
```

### Development Database

For testing with persistent data:

```bash
# Use SQLite for development (if implementing persistence)
export DATABASE_URL="sqlite:///./test.db"

# Reset test database
rm -f test.db
```

### Memory and Performance Issues

```bash
# Monitor memory usage
pip install memory-profiler
python -m memory_profiler main.py

# Profile performance
pip install line-profiler
kernprof -l -v main.py
```

## 📚 Next Steps

- **[Architecture Guide](architecture.md)** - Understand the system design
- **[Contributing Guide](contributing.md)** - Learn the contribution workflow
- **[Testing Guide](testing.md)** - Deep dive into testing practices

---

**Need help?** Check the [troubleshooting section](#troubleshooting) or create an issue on GitHub. 