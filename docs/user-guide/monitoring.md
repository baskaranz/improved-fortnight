# Monitoring Guide

Comprehensive guide for monitoring, health checks, and observability of the Orchestrator API.

## 📋 Table of Contents

- [Health Monitoring Overview](#health-monitoring-overview)
- [Health Check Endpoints](#health-check-endpoints)
- [Circuit Breaker Monitoring](#circuit-breaker-monitoring)
- [Registry Monitoring](#registry-monitoring)
- [Performance Monitoring](#performance-monitoring)
- [Log Monitoring](#log-monitoring)
- [Alerting](#alerting)
- [Troubleshooting with Monitoring](#troubleshooting-with-monitoring)

## 🏥 Health Monitoring Overview

The Orchestrator API provides comprehensive health monitoring for:
- **System Health** - Overall service status
- **Endpoint Health** - Individual backend service status
- **Circuit Breaker Status** - Fault tolerance monitoring
- **Registry Status** - Endpoint registration monitoring

### Health Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Health Checker │────│  Circuit Breaker │────│   Registry      │
│                 │    │   Manager        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                   ┌─────────────────────────┐
                   │    Health Endpoints     │
                   │  /health/*             │
                   └─────────────────────────┘
```

## 🔍 Health Check Endpoints

### System Health Overview

```bash
# Quick system health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/health/status
```

**Response Example:**
```json
{
  "system_status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "summary": {
    "total_endpoints": 5,
    "healthy_endpoints": 4,
    "unhealthy_endpoints": 1,
    "health_percentage": 80.0,
    "average_response_time": 0.234
  },
  "circuit_breaker_summary": {
    "total_circuit_breakers": 5,
    "open_breakers": 1,
    "half_open_breakers": 0,
    "closed_breakers": 4,
    "health_percentage": 80.0
  }
}
```

### Individual Endpoint Health

```bash
# List all endpoint health status
curl http://localhost:8000/health/endpoints

# Get specific endpoint health
curl http://localhost:8000/health/endpoints/user_service

# Trigger immediate health check
curl -X POST http://localhost:8000/health/check/user_service
```

**Individual Endpoint Response:**
```json
{
  "endpoint_id": "user_service",
  "status": "active",
  "last_check_time": "2024-01-01T12:00:00Z",
  "response_time": 0.123,
  "error_message": null,
  "consecutive_failures": 0,
  "consecutive_successes": 5,
  "circuit_breaker": {
    "state": "closed",
    "failure_count": 0,
    "last_failure_time": null,
    "last_success_time": "2024-01-01T12:00:00Z"
  }
}
```

### Unhealthy Endpoints

```bash
# Get all unhealthy endpoints
curl http://localhost:8000/health/unhealthy
```

### Health Summary

```bash
# Get comprehensive health summary
curl http://localhost:8000/health/summary
```

## ⚡ Circuit Breaker Monitoring

Monitor fault tolerance and automatic failure handling:

### All Circuit Breakers

```bash
# Get all circuit breaker status
curl http://localhost:8000/health/circuit-breakers
```

**Response Example:**
```json
{
  "summary": {
    "total_circuit_breakers": 5,
    "open_breakers": 1,
    "half_open_breakers": 0,
    "closed_breakers": 4,
    "health_percentage": 80.0
  },
  "circuit_breakers": [
    {
      "endpoint_id": "user_service",
      "state": "closed",
      "failure_count": 0,
      "last_failure_time": null,
      "last_success_time": "2024-01-01T12:00:00Z",
      "state_changed_time": "2024-01-01T11:30:00Z",
      "half_open_calls": 0,
      "config": {
        "failure_threshold": 5,
        "reset_timeout": 60,
        "half_open_max_calls": 3,
        "fallback_strategy": "error_response"
      }
    }
  ]
}
```

### Open Circuit Breakers

```bash
# Get only open circuit breakers (failing services)
curl http://localhost:8000/health/circuit-breakers/open
```

### Circuit Breaker States

| State | Description | Actions |
|-------|-------------|---------|
| **Closed** | ✅ Normal operation | Requests flow through |
| **Open** | ❌ Failing fast | Requests rejected immediately |
| **Half-Open** | 🔄 Testing recovery | Limited requests allowed |

## 📊 Registry Monitoring

Monitor endpoint registration and management:

### Registry Statistics

```bash
# Get registry statistics
curl http://localhost:8000/registry/stats
```

**Response Example:**
```json
{
  "registry_stats": {
    "total": 5,
    "active": 4,
    "inactive": 0,
    "disabled": 1,
    "unhealthy": 1
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Endpoint Details

```bash
# List all registered endpoints
curl http://localhost:8000/registry/endpoints

# Get specific endpoint details
curl http://localhost:8000/registry/endpoints/user_service
```

### Route Monitoring

```bash
# List active routes
curl http://localhost:8000/router/routes

# Test endpoint connectivity
curl http://localhost:8000/router/test/user_service

# Debug route resolution
curl http://localhost:8000/router/debug/user_service/users/123
```

## 📈 Performance Monitoring

### Response Time Monitoring

Monitor response times through health checks:

```bash
# Health summary includes average response time
curl http://localhost:8000/health/summary | jq '.summary.average_response_time'
```

### Request Monitoring

All requests include performance headers:

```bash
# Make a request and check headers
curl -v http://localhost:8000/orchestrator/user_service/users

# Response headers include:
# X-Response-Time: 0.234s
# X-Request-ID: 12345678-1234-1234-1234-123456789abc
# X-Endpoint-ID: user_service
```

### Configuration Monitoring

```bash
# Check configuration status
curl http://localhost:8000/config/status
```

**Configuration Status:**
```json
{
  "loaded": true,
  "version": "1.0.0",
  "config_path": "config/config.yaml",
  "endpoints_count": 5,
  "last_reload_error": null,
  "watching": true
}
```

## 📋 Log Monitoring

### Log Levels

Configure logging for different levels of detail:

```bash
# Start with different log levels
python main.py --log-level debug    # Detailed debugging
python main.py --log-level info     # Standard information
python main.py --log-level warning  # Warnings and errors only
python main.py --log-level error    # Errors only
```

### Key Log Messages

Monitor these important log patterns:

#### Service Startup
```
INFO - Starting orchestrator service...
INFO - Loaded configuration with 5 endpoints
INFO - Registered 5 endpoints
INFO - Health checker started with 30s interval
INFO - Orchestrator service started successfully
```

#### Health Check Events
```
INFO - Endpoint user_service health changed: active -> unhealthy
WARNING - Health check timeout for user_service
ERROR - Health check error for user_service: Connection refused
```

#### Circuit Breaker Events
```
WARNING - Circuit breaker opened for user_service (failures: 5)
INFO - Circuit breaker transitioned to half-open for user_service
INFO - Circuit breaker closed for user_service
```

#### Request Routing
```
INFO - Routed GET /users to user_service (200) in 0.234s
ERROR - Orchestration error for user_service: Connection timeout
```

### Log Aggregation

For production deployments, consider centralized logging:

```bash
# JSON structured logging (configure in production)
python main.py --log-format json

# Send logs to centralized system
python main.py 2>&1 | fluentd
python main.py 2>&1 | logstash
```

## 🚨 Alerting

### Health-Based Alerting

Set up alerts based on health endpoints:

#### Critical Alerts
```bash
# System unhealthy (< 50% endpoints healthy)
curl -s http://localhost:8000/health/status | jq '.summary.health_percentage < 50'

# All endpoints down
curl -s http://localhost:8000/health/status | jq '.summary.healthy_endpoints == 0'

# Circuit breakers all open
curl -s http://localhost:8000/health/circuit-breakers | jq '.summary.open_breakers == .summary.total_circuit_breakers'
```

#### Warning Alerts
```bash
# Single endpoint unhealthy
curl -s http://localhost:8000/health/unhealthy | jq '.count > 0'

# High response times
curl -s http://localhost:8000/health/summary | jq '.summary.average_response_time > 1.0'

# Circuit breaker opened
curl -s http://localhost:8000/health/circuit-breakers | jq '.summary.open_breakers > 0'
```

### Monitoring Script Example

```bash
#!/bin/bash
# Simple monitoring script

ORCHESTRATOR_URL="http://localhost:8000"

# Check system health
HEALTH=$(curl -s "$ORCHESTRATOR_URL/health/status" | jq -r '.system_status')
HEALTH_PCT=$(curl -s "$ORCHESTRATOR_URL/health/status" | jq -r '.summary.health_percentage')

if [ "$HEALTH" != "healthy" ] || [ "$(echo "$HEALTH_PCT < 80" | bc)" -eq 1 ]; then
    echo "ALERT: System unhealthy - Status: $HEALTH, Health: $HEALTH_PCT%"
    # Send alert notification
fi

# Check for open circuit breakers
OPEN_BREAKERS=$(curl -s "$ORCHESTRATOR_URL/health/circuit-breakers" | jq -r '.summary.open_breakers')

if [ "$OPEN_BREAKERS" -gt 0 ]; then
    echo "WARNING: $OPEN_BREAKERS circuit breakers are open"
    # Send warning notification
fi
```

## 🔧 Troubleshooting with Monitoring

### Debug Unhealthy Services

```bash
# 1. Check which services are unhealthy
curl http://localhost:8000/health/unhealthy

# 2. Get detailed status for specific service
curl http://localhost:8000/health/endpoints/problem_service

# 3. Test connectivity directly
curl http://localhost:8000/router/test/problem_service

# 4. Debug routing
curl http://localhost:8000/router/debug/problem_service/test/path

# 5. Check circuit breaker state
curl http://localhost:8000/health/circuit-breakers | jq '.circuit_breakers[] | select(.endpoint_id == "problem_service")'
```

### Monitor Recovery

```bash
# Trigger immediate health check
curl -X POST http://localhost:8000/health/check/problem_service

# Monitor health percentage improvement
watch -n 5 'curl -s http://localhost:8000/health/status | jq .summary.health_percentage'

# Watch circuit breaker recovery
watch -n 5 'curl -s http://localhost:8000/health/circuit-breakers | jq .summary'
```

### Performance Investigation

```bash
# Check average response times
curl http://localhost:8000/health/summary | jq '.summary.average_response_time'

# Test specific endpoint performance
time curl http://localhost:8000/router/test/slow_service

# Check for timeout issues in logs
grep -i timeout /var/log/orchestrator.log
```

## 📊 Monitoring Dashboard Examples

### Simple Dashboard Commands

```bash
# Create a simple monitoring dashboard
watch -n 2 '
echo "=== Orchestrator Health Dashboard ==="
echo "System Status: $(curl -s http://localhost:8000/health/status | jq -r .system_status)"
echo "Health Percentage: $(curl -s http://localhost:8000/health/status | jq -r .summary.health_percentage)%"
echo "Active Endpoints: $(curl -s http://localhost:8000/registry/stats | jq -r .registry_stats.active)"
echo "Open Circuit Breakers: $(curl -s http://localhost:8000/health/circuit-breakers | jq -r .summary.open_breakers)"
echo "Average Response Time: $(curl -s http://localhost:8000/health/summary | jq -r .summary.average_response_time)s"
echo "=================================="
'
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh - Comprehensive health check

ORCHESTRATOR_URL="http://localhost:8000"

echo "🏥 Orchestrator Health Check Report"
echo "=================================="

# System Status
echo "📊 System Status:"
curl -s "$ORCHESTRATOR_URL/health/status" | jq '{
  status: .system_status,
  health_percentage: .summary.health_percentage,
  total_endpoints: .summary.total_endpoints,
  healthy_endpoints: .summary.healthy_endpoints,
  avg_response_time: .summary.average_response_time
}'

echo ""
echo "⚡ Circuit Breaker Status:"
curl -s "$ORCHESTRATOR_URL/health/circuit-breakers" | jq '.summary'

echo ""
echo "📋 Registry Status:"
curl -s "$ORCHESTRATOR_URL/registry/stats" | jq '.registry_stats'

# Unhealthy Endpoints
echo ""
echo "🚨 Unhealthy Endpoints:"
UNHEALTHY=$(curl -s "$ORCHESTRATOR_URL/health/unhealthy" | jq -r '.count')
if [ "$UNHEALTHY" -gt 0 ]; then
    curl -s "$ORCHESTRATOR_URL/health/unhealthy" | jq '.unhealthy_endpoints[]'
else
    echo "✅ All endpoints are healthy"
fi
```

## 📚 Next Steps

- **[Configuration](configuration.md)** - Configure health check settings
- **[Deployment](deployment.md)** - Production monitoring setup
- **[Troubleshooting](troubleshooting.md)** - Diagnose and fix issues
- **[Quick Start](quick-start.md)** - Get started with monitoring

---

**Need help?** Check the [troubleshooting guide](troubleshooting.md) or view live documentation at `http://localhost:8000/docs`. 