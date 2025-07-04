# Configuration Reference

Complete configuration reference for the Orchestrator API service.

## 📋 Table of Contents

- [Configuration File](#configuration-file)
- [Environment Variables](#environment-variables)
- [Endpoint Configuration](#endpoint-configuration)
- [Circuit Breaker Configuration](#circuit-breaker-configuration)
- [Health Check Configuration](#health-check-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Configuration Examples](#configuration-examples)
- [Validation and Reloading](#validation-and-reloading)

## 📄 Configuration File

The service uses a YAML configuration file, default location: `config/config.yaml`

### Basic Structure

```yaml
# Main configuration sections
endpoints: []           # List of endpoint configurations
circuit_breaker: {}     # Circuit breaker settings
health_check: {}        # Health monitoring settings
log_level: "INFO"       # Logging level
```

### File Location

| Method | Description |
|--------|-------------|
| **Default** | `config/config.yaml` |
| **Command Line** | `python main.py --config path/to/config.yaml` |
| **Environment** | `CONFIG_PATH=path/to/config.yaml` |

## 🌍 Environment Variables

Configure the service using environment variables:

```bash
# Core Settings
export CONFIG_PATH="config/config.yaml"   # Configuration file path
export HOST="0.0.0.0"                     # Host to bind to
export PORT="8000"                        # Port to bind to
export LOG_LEVEL="INFO"                   # Logging level
export RELOAD="false"                     # Auto-reload (development)

# Advanced Settings
export WORKERS="1"                        # Number of worker processes
export MAX_REQUESTS="1000"               # Requests per worker before restart
export TIMEOUT="30"                      # Request timeout (seconds)
```

### Environment Variable Priority

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file**
4. **Default values** (lowest priority)

## 🔗 Endpoint Configuration

Configure backend services that the orchestrator will route to:

### Basic Endpoint

```yaml
endpoints:
  - url: "https://api.example.com/v1"     # Required: Backend URL
    name: "example_service"               # Required: Unique identifier
    methods: ["GET", "POST"]              # HTTP methods to allow
    auth_type: "bearer"                   # Authentication type (documentation)
    disabled: false                       # Enable/disable endpoint
    timeout: 30                          # Request timeout in seconds
```

### Complete Endpoint Configuration

```yaml
endpoints:
  - url: "https://api.example.com/v1"
    name: "example_service"
    version: "v1"                         # API version (optional)
    methods: ["GET", "POST", "PUT", "DELETE"]
    auth_type: "bearer"                   # bearer, api_key, basic, oauth2, none
    disabled: false
    health_check_path: "/health"          # Custom health check endpoint
    timeout: 30                          # Request timeout (1-300 seconds)
    description: "Example API service"    # Optional description
```

### Endpoint Fields Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | URL | ✅ Yes | - | Backend service URL |
| `name` | String | ✅ Yes | - | Unique endpoint identifier |
| `version` | String | No | `null` | API version (e.g., "v1", "2.0") |
| `methods` | Array | No | `["GET"]` | Allowed HTTP methods |
| `auth_type` | Enum | No | `"none"` | Expected auth type (documentation) |
| `disabled` | Boolean | No | `false` | Whether endpoint is disabled |
| `health_check_path` | String | No | `null` | Custom health check path |
| `timeout` | Integer | No | `30` | Request timeout (1-300 seconds) |

### Authentication Types

| Type | Description | Headers Expected |
|------|-------------|------------------|
| `none` | No authentication required | None |
| `bearer` | JWT/Bearer token | `Authorization: Bearer <token>` |
| `api_key` | API key authentication | `X-API-Key: <key>` |
| `basic` | Basic authentication | `Authorization: Basic <credentials>` |
| `oauth2` | OAuth2 authentication | `Authorization: Bearer <token>` |

> **Note**: The `auth_type` field is for documentation only. The orchestrator forwards all headers to backend services.

## ⚡ Circuit Breaker Configuration

Configure fault tolerance and automatic failure handling:

```yaml
circuit_breaker:
  failure_threshold: 5              # Failures before opening circuit
  reset_timeout: 60                 # Seconds before attempting reset
  half_open_max_calls: 3           # Max calls in half-open state
  fallback_strategy: "error_response"   # Fallback behavior
  fallback_response:               # Custom fallback response (optional)
    message: "Service temporarily unavailable"
    retry_after: 60
```

### Circuit Breaker Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `failure_threshold` | Integer | `5` | 1-100 | Consecutive failures to open circuit |
| `reset_timeout` | Integer | `60` | 1-3600 | Seconds before trying to reset |
| `half_open_max_calls` | Integer | `3` | 1-10 | Max calls in half-open state |
| `fallback_strategy` | Enum | `"error_response"` | See below | How to handle open circuit |

### Fallback Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `error_response` | Return 503 error | Default behavior |
| `cached_response` | Return last successful response | When stale data is acceptable |
| `default_response` | Return configured default | When you have a fallback value |

## 🏥 Health Check Configuration

Configure automatic health monitoring:

```yaml
health_check:
  enabled: true                    # Enable health monitoring
  interval: 30                     # Check interval in seconds
  timeout: 10                      # Health check timeout
  unhealthy_threshold: 3           # Failures to mark unhealthy
  healthy_threshold: 2             # Successes to mark healthy
```

### Health Check Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `enabled` | Boolean | `true` | - | Enable health monitoring |
| `interval` | Integer | `30` | 5-3600 | Seconds between checks |
| `timeout` | Integer | `10` | 1-60 | Health check timeout |
| `unhealthy_threshold` | Integer | `3` | 1-10 | Consecutive failures to mark unhealthy |
| `healthy_threshold` | Integer | `2` | 1-10 | Consecutive successes to mark healthy |

## ⚙️ Advanced Configuration

### Logging Configuration

```yaml
log_level: "INFO"                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Complete Example

```yaml
# Complete configuration example
endpoints:
  # Public API (no auth)
  - url: "https://httpbin.org/get"
    name: "httpbin_service"
    version: "v1"
    methods: ["GET"]
    auth_type: "none"
    disabled: false
    health_check_path: "/get"
    timeout: 15

  # Protected API (with auth)
  - url: "https://api.yourcompany.com/users"
    name: "user_service"
    version: "v2"
    methods: ["GET", "POST", "PUT", "DELETE"]
    auth_type: "bearer"
    disabled: false
    health_check_path: "/health"
    timeout: 30

  # Legacy API (basic auth)
  - url: "https://legacy.api.com"
    name: "legacy_service"
    methods: ["GET", "POST"]
    auth_type: "basic"
    disabled: false
    timeout: 45

# Circuit breaker for fault tolerance
circuit_breaker:
  failure_threshold: 5
  reset_timeout: 60
  half_open_max_calls: 3
  fallback_strategy: "error_response"

# Health monitoring
health_check:
  enabled: true
  interval: 30
  timeout: 10
  unhealthy_threshold: 3
  healthy_threshold: 2

# Logging
log_level: "INFO"
```

## 🔄 Validation and Reloading

### Configuration Validation

```bash
# Validate configuration file
curl -X POST "http://localhost:8000/config/validate?config_path=config/config.yaml"

# Check current configuration status
curl http://localhost:8000/config/status
```

### Hot Reloading

The service automatically reloads configuration when the file changes:

```bash
# Manual reload
curl -X POST http://localhost:8000/config/reload

# Check reload status
curl http://localhost:8000/config/status
```

### Validation Rules

| Rule | Description |
|------|-------------|
| **Unique Names** | Each endpoint must have a unique `name` |
| **Valid URLs** | All `url` fields must be valid HTTP/HTTPS URLs |
| **Valid Methods** | Only standard HTTP methods allowed |
| **Timeout Range** | Timeout must be 1-300 seconds |
| **Name Format** | Names can only contain alphanumeric, hyphens, underscores |

## 🚨 Common Configuration Issues

### Issue: Duplicate endpoint names
```yaml
# ❌ Wrong - duplicate names
endpoints:
  - name: "api_service"
    url: "https://api1.com"
  - name: "api_service"    # Duplicate!
    url: "https://api2.com"

# ✅ Correct - unique names
endpoints:
  - name: "api_service_v1"
    url: "https://api1.com"
  - name: "api_service_v2"
    url: "https://api2.com"
```

### Issue: Invalid timeout values
```yaml
# ❌ Wrong - timeout too high
endpoints:
  - name: "slow_service"
    url: "https://slow.api.com"
    timeout: 500            # Max is 300

# ✅ Correct - valid timeout
endpoints:
  - name: "slow_service"
    url: "https://slow.api.com"
    timeout: 120            # Within 1-300 range
```

### Issue: Invalid URL formats
```yaml
# ❌ Wrong - invalid URLs
endpoints:
  - name: "bad_service"
    url: "not-a-url"       # Invalid URL

# ✅ Correct - valid URLs
endpoints:
  - name: "good_service"
    url: "https://api.example.com"
```

## 📚 Next Steps

- **[Quick Start](quick-start.md)** - Get running in 5 minutes
- **[Deployment Guide](deployment.md)** - Production deployment
- **[Monitoring Guide](monitoring.md)** - Health checks and metrics
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

---

**Need help?** Check the [troubleshooting guide](troubleshooting.md) or run `curl http://localhost:8000/docs` for interactive API documentation. 