# FastAPI Orchestrating Service - Comprehensive Operational Guide

> **📚 New to the project?** Start with the **[Main Documentation](docs/)** for organized guides by audience.  
> **🎯 Need to deploy quickly?** Check the **[5-minute Quick Start](docs/user-guide/quick-start.md)**.  
> **📖 Want the full reference?** You're in the right place - this guide covers everything!

---

A comprehensive, single-file operational reference for running and using the FastAPI Orchestrating Service. This guide contains complete setup instructions, API examples, troubleshooting, and operational procedures all in one place.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Service](#running-the-service)
- [API Usage](#api-usage)
- [Authentication Passthrough](#authentication-passthrough)
- [Health Checks & Circuit Breakers](#health-checks--circuit-breakers)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone and Setup

```bash
# Clone the repository (if from git)
git clone <repository-url>
cd yet-another-orch-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (recommended)
pip install -e .

# Or install development dependencies
pip install -e ".[dev]"
```

### 2. Verify Installation

```bash
# Test the application
python main.py --help
```

## ⚙️ Configuration

### 1. Configuration File

The service uses `config/config.yaml` by default. A sample configuration is created automatically on first run.

```yaml
# config/config.yaml
endpoints:
  - url: "https://httpbin.org/get"
    name: "httpbin_get"
    version: "v1"
    methods: ["GET"]
    auth_type: "none"  # Documentation only - no auth required
    disabled: false
    health_check_path: "/get"
    timeout: 30

  - url: "https://api.example.com/v1"
    name: "secure_api"
    version: "v1"
    methods: ["GET", "POST"]
    auth_type: "bearer"  # Documentation only - backend expects Bearer token
    disabled: false
    health_check_path: "/health"
    timeout: 30

circuit_breaker:
  failure_threshold: 5
  reset_timeout: 60
  half_open_max_calls: 3
  fallback_strategy: "error_response"

health_check:
  enabled: true
  interval: 30
  timeout: 10
  unhealthy_threshold: 3
  healthy_threshold: 2

log_level: "INFO"
```

### 2. Environment Variables

```bash
# Optional environment variables
export CONFIG_PATH="config/config.yaml"
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="INFO"
export RELOAD="false"
```

## 🎯 Running the Service

### 1. Basic Startup

```bash
# Start with default settings
python main.py

# The service will start on http://localhost:8000
```

### 2. Custom Configuration

```bash
# Start with custom config file
python main.py --config path/to/your/config.yaml

# Start on different port
python main.py --port 9000

# Start with debug logging
python main.py --log-level debug
```

### 3. Development Mode

```bash
# Start with auto-reload (for development)
python main.py --reload --log-level debug

# This will automatically restart the server when code changes
```

### 4. Production Mode

```bash
# Start for production
python main.py --host 0.0.0.0 --port 8000 --log-level info
```

## 📚 API Usage

### 1. Service Information

```bash
# Check service status
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health

# View API documentation (Interactive Swagger UI)
# Open http://localhost:8000/docs in your browser

# Alternative API documentation (ReDoc)
# Open http://localhost:8000/redoc in your browser

# Get OpenAPI schema
curl http://localhost:8000/openapi.json
```

### 2. Configuration Management

```bash
# Get configuration status
curl http://localhost:8000/config/status

# Reload configuration
curl -X POST http://localhost:8000/config/reload

# List configured endpoints
curl http://localhost:8000/config/endpoints

# Validate configuration file
curl -X POST "http://localhost:8000/config/validate?config_path=config/config.yaml"
```

### 3. Registry Management

```bash
# List registered endpoints
curl http://localhost:8000/registry/endpoints

# List with filtering and pagination
curl "http://localhost:8000/registry/endpoints?status=active&limit=10&offset=0"

# Get specific endpoint details
curl http://localhost:8000/registry/endpoints/httpbin_get

# Register a new endpoint
curl -X POST http://localhost:8000/registry/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "url": "https://api.example.com/v2",
      "name": "example_v2",
      "version": "v2",
      "methods": ["GET", "POST"],
      "auth_type": "bearer",
      "disabled": false,
      "timeout": 30
    }
  }'

# Update endpoint status
curl -X PUT "http://localhost:8000/registry/endpoints/example_v2/status?status=inactive"

# Get registry statistics
curl http://localhost:8000/registry/stats

# Sync registry with configuration
curl -X POST http://localhost:8000/registry/sync

# Unregister an endpoint
curl -X DELETE http://localhost:8000/registry/endpoints/example_v2
```

### 4. Health Monitoring

```bash
# Get overall system health status
curl http://localhost:8000/health/status

# Get all endpoints health status
curl http://localhost:8000/health/endpoints

# Get specific endpoint health
curl http://localhost:8000/health/endpoints/httpbin_get

# Trigger immediate health check
curl -X POST http://localhost:8000/health/check/httpbin_get

# Get unhealthy endpoints
curl http://localhost:8000/health/unhealthy

# Get health summary
curl http://localhost:8000/health/summary
```

### 5. Routing

```bash
# List active routes
curl http://localhost:8000/router/routes

# Test endpoint connectivity
curl http://localhost:8000/router/test/httpbin_get

# Refresh route mappings
curl -X POST http://localhost:8000/router/refresh

# Debug route resolution
curl http://localhost:8000/router/debug/httpbin_get/some/path
```

## 🔐 Authentication Passthrough

The orchestrator acts as a **transparent proxy** for authentication, forwarding all authentication headers to backend services.

### How It Works

1. **No Orchestrator Authentication**: The orchestrator itself doesn't authenticate requests
2. **Header Forwarding**: All authentication headers are automatically forwarded to backend services
3. **Backend Responsibility**: Each registered endpoint handles its own authentication
4. **Transparent Operation**: Clients authenticate with backend services through the orchestrator

### Examples

#### Bearer Token Authentication

```bash
# Request with JWT token - forwarded to backend
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8000/orchestrator/secure_api/users

# Example with actual resource endpoint (to see auth enforcement)
# Without token (should fail with 401)
curl http://localhost:8000/orchestrator/user_service/users

# With token (should succeed)
curl -H "Authorization: Bearer sample-token-12345" \
     http://localhost:8000/orchestrator/user_service/users

# The orchestrator forwards the Authorization header to the backend service
```

#### API Key Authentication

```bash
# Request with API key - forwarded to backend
curl -H "X-API-Key: your-secret-api-key" \
     http://localhost:8000/orchestrator/api_service/data

# The orchestrator forwards the X-API-Key header to the backend service
```

#### Basic Authentication

```bash
# Request with basic auth - forwarded to backend
curl -u username:password \
     http://localhost:8000/orchestrator/basic_auth_service/resource

# The orchestrator forwards the Authorization: Basic header to the backend service
```

#### Public Endpoints

```bash
# Request to public endpoint - no authentication needed
curl http://localhost:8000/orchestrator/public_service/info

# No authentication headers are required or forwarded
```

### Configuration for Authentication

```yaml
endpoints:
  # Public endpoint - no authentication required
  - url: "https://httpbin.org/get"
    name: "public_service"
    auth_type: "none"  # Documentation only
    
  # JWT protected endpoint
  - url: "https://api.example.com/v1"
    name: "jwt_service"
    auth_type: "bearer"  # Documentation only - indicates backend expects Bearer token
    
  # API key protected endpoint
  - url: "https://api.service.com"
    name: "api_key_service"
    auth_type: "api_key"  # Documentation only - indicates backend expects API key
    
  # Basic auth protected endpoint
  - url: "https://legacy.api.com"
    name: "legacy_service"
    auth_type: "basic"  # Documentation only - indicates backend expects basic auth
```

**Note**: The `auth_type` field is for documentation purposes only and helps developers understand what authentication method the backend service expects. The orchestrator doesn't enforce authentication - it simply forwards all headers.

## 🏥 Health Checks & Circuit Breakers

### Health Check Configuration

```yaml
health_check:
  enabled: true
  interval: 30        # Check every 30 seconds
  timeout: 10         # 10 second timeout
  unhealthy_threshold: 3  # Mark unhealthy after 3 failures
  healthy_threshold: 2    # Mark healthy after 2 successes
```

### Circuit Breaker Configuration

```yaml
circuit_breaker:
  failure_threshold: 5      # Open circuit after 5 failures
  reset_timeout: 60         # Try to close after 60 seconds
  half_open_max_calls: 3    # Allow 3 calls in half-open state
  fallback_strategy: "error_response"
```

### Monitoring Examples

```bash
# Check overall system health (includes circuit breaker info)
curl http://localhost:8000/health/status

# Monitor circuit breaker states
curl http://localhost:8000/health/circuit-breakers

# Get open circuit breakers
curl http://localhost:8000/health/circuit-breakers/open

# Get detailed health summary
curl http://localhost:8000/health/summary
```

**Note**: Circuit breaker statistics will only appear after requests have been made through the orchestrator to endpoints. Initial registration won't show circuit breaker data until actual traffic flows through the system.

## 🛠️ Development

### Development Setup

```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run with auto-reload
python main.py --reload --log-level debug

# Run tests
pytest

# Run specific test file (e.g., registry API tests)
pytest tests/unit/test_registry_api.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# Code formatting
black src/ tests/
flake8 src/ tests/
mypy src/

# Check current test coverage
pytest --cov=src --cov-report=term-missing
```

### Adding New Endpoints

1. **Via Configuration File**:
   ```yaml
   # Add to config/config.yaml
   endpoints:
     - url: "https://your-api.com"
       name: "your_service"
       version: "v1"
       methods: ["GET", "POST"]
       auth_type: "bearer"
   ```

2. **Via API**:
   ```bash
   curl -X POST http://localhost:8000/registry/endpoints \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "url": "https://your-api.com",
         "name": "your_service",
         "version": "v1",
         "methods": ["GET", "POST"],
         "auth_type": "bearer"
       }
     }'
   ```

3. **Test the endpoint**:
   ```bash
   # Test connectivity
   curl http://localhost:8000/router/test/your_service
   
   # Make actual request
   curl -H "Authorization: Bearer your-token" \
        http://localhost:8000/orchestrator/your_service/some/path
   ```

### Complete Dynamic Registration Example

Here's a complete workflow for adding a new service:

```bash
# 1. Start a mock service (for testing)
python -c "
from fastapi import FastAPI, HTTPException, Header
import uvicorn
from typing import Optional

app = FastAPI(title='Mock Payment API')

@app.get('/health')
def health(): return {'status': 'healthy'}

@app.get('/payments')
def get_payments(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Auth required')
    return {'payments': [{'id': 1, 'amount': 100}]}

uvicorn.run(app, host='0.0.0.0', port=8010)
" &

# 2. Register the service dynamically
curl -X POST http://localhost:8000/registry/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "url": "http://localhost:8010",
      "name": "payment_service",
      "version": "v1",
      "methods": ["GET", "POST"],
      "auth_type": "bearer",
      "disabled": false,
      "health_check_path": "/health",
      "timeout": 30
    }
  }'

# 3. Verify registration
curl http://localhost:8000/registry/endpoints/payment_service

# 4. Test the service through orchestrator
curl -H "Authorization: Bearer test-token" \
     http://localhost:8000/orchestrator/payment_service/payments

# 5. Monitor health and circuit breaker status
curl http://localhost:8000/health/endpoints/payment_service
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check if port is already in use
lsof -i :8000

# Try different port
python main.py --port 8001
```

#### 2. Configuration Errors

```bash
# Validate configuration
curl -X POST "http://localhost:8000/config/validate?config_path=config/config.yaml"

# Check configuration status
curl http://localhost:8000/config/status

# List current configured endpoints
curl http://localhost:8000/config/endpoints
```

#### 3. Endpoint Not Reachable

```bash
# Check endpoint registration
curl http://localhost:8000/registry/endpoints/your_endpoint

# Test connectivity
curl http://localhost:8000/router/test/your_endpoint

# Check health status
curl http://localhost:8000/health/endpoints/your_endpoint

# Trigger immediate health check
curl -X POST http://localhost:8000/health/check/your_endpoint

# Check circuit breaker state (integrated in health endpoint)
curl http://localhost:8000/health/endpoints/your_endpoint

# Debug routing
curl http://localhost:8000/router/debug/your_endpoint/path

# Check if route mappings need refresh
curl -X POST http://localhost:8000/router/refresh
```

#### 4. Authentication Issues

- **Problem**: Backend returns 401 Unauthorized
- **Solution**: Ensure you're passing the correct authentication headers:
  ```bash
  # Check what headers are being forwarded
  curl -v -H "Authorization: Bearer your-token" \
       http://localhost:8000/orchestrator/your_service/endpoint
  ```

#### 5. Circuit Breaker Open

```bash
# Check circuit breaker status
curl http://localhost:8000/health/endpoints/your_endpoint

# Get circuit breaker information
curl http://localhost:8000/health/circuit-breakers
```

#### 6. Port Conflicts During Development

- **Problem**: Mock services can't start due to port conflicts
- **Solution**: Check and kill conflicting processes:
  ```bash
  # Check what's using a port
  lsof -i :8001
  
  # Kill processes using specific ports
  pkill -f "simple_mock.py"
  
  # Or use different ports for your mock services
  python simple_mock.py UserService 8011 true
  ```

#### 7. URL Path Issues

- **Problem**: Double slashes in forwarded URLs or 404 errors
- **Solution**: Use the debug endpoint to check path resolution:
  ```bash
  # Debug how paths are being resolved
  curl http://localhost:8000/router/debug/your_service/your/path
  
  # Check active routes
  curl http://localhost:8000/router/routes
  
  # Refresh route mappings if needed
  curl -X POST http://localhost:8000/router/refresh
  ```

### Debugging Tips

1. **Enable Debug Logging**:
   ```bash
   python main.py --log-level debug
   ```

2. **Check Service Health**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Monitor Route Resolution**:
   ```bash
   curl http://localhost:8000/router/debug/your/path
   ```

4. **View Active Routes**:
   ```bash
   curl http://localhost:8000/router/routes
   ```

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/health
- **Configuration**: Check `config/config.yaml`
- **Logs**: Enable debug logging for detailed information

## 📊 Additional Information

### Enhanced Architecture

The orchestrator now features a **simplified, integrated architecture**:
- **Circuit Breaker Integration**: Circuit breaker monitoring is integrated into health APIs (no separate circuit breaker APIs)
- **Transparent Fault Tolerance**: Circuit breakers work internally with automatic fallback responses
- **Unified Monitoring**: All system health, endpoint status, and circuit breaker information available through `/health/*` endpoints

### API Coverage & Testing

The orchestrator service now has comprehensive test coverage:
- **Registry API**: 98% coverage with 28 test cases
- **Overall Project**: 81% test coverage
- All 202 tests passing ✅

### Version Information

- **Service Version**: 0.1.0
- **FastAPI Framework**: Latest
- **Authentication**: Passthrough to backend services
- **Python**: 3.9+ required

---

## 📚 Related Documentation

This comprehensive guide covers all operational aspects. For organized, audience-specific documentation:

- **[📖 Main Documentation Hub](docs/)** - Start here for organized guides
- **[🎯 User Guide](docs/user-guide/)** - For operators and DevOps teams
- **[🛠️ Developer Guide](docs/developer-guide/)** - For contributors and developers
- **[🏗️ Architecture Details](docs/developer-guide/architecture.md)** - Technical deep-dive
- **[🚀 Contributing](docs/developer-guide/contributing.md)** - How to contribute

---

This guide covers the essential aspects of running and using the FastAPI Orchestrating Service. The service acts as a transparent proxy, making it easy to route requests to multiple backend APIs while forwarding authentication seamlessly.

For the most up-to-date API documentation, always refer to the interactive docs at `http://localhost:8000/docs` when the service is running.