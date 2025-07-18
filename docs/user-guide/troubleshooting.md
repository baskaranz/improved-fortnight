# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Orchestrator API.

## 🔍 Quick Diagnosis

### Service Health Check

```bash
# 1. Check if service is running
curl http://localhost:8000/health

# 2. Check system status
curl http://localhost:8000/health/status

# 3. Check endpoint registry
curl http://localhost:8000/registry/stats

# 4. Check circuit breakers
curl http://localhost:8000/health/circuit-breakers
```

**Expected healthy response:**
```json
{
  "system_status": "healthy",
  "summary": {
    "health_percentage": 100,
    "healthy_endpoints": 4,
    "total_endpoints": 4
  },
  "circuit_breaker_summary": {
    "closed_breakers": 4,
    "open_breakers": 0
  }
}
```

## 🚨 Common Issues & Solutions

### 1. Service Won't Start

**Symptoms:**
- Service exits immediately
- "Address already in use" error
- Permission denied errors
- Container exits with error

**Diagnosis:**

#### Docker Diagnosis
```bash
# Check container status
docker ps -a

# Check container logs
docker-compose logs orchestrator
# OR
docker logs orchestrator-api

# Check if port is already in use
docker ps | grep 8000
lsof -i :8000

# Check Docker daemon
docker version
docker info
```

#### Python Diagnosis
```bash
# Check if port is already in use
lsof -i :8000
netstat -tulnp | grep :8000

# Check Python version
python --version  # Should be 3.9+

# Check dependencies
pip list | grep fastapi

# Check configuration
python main.py --config config/config.yaml --help
```

**Solutions:**

#### Docker Solutions

**Container Won't Start:**
```bash
# Check Docker daemon is running
sudo systemctl start docker

# Rebuild container
docker-compose build orchestrator
docker-compose up -d orchestrator

# Check for image issues
docker images | grep orchestrator
docker build -t orchestrator-api .
```

**Port Already in Use:**
```bash
# Option 1: Kill existing container
docker stop orchestrator-api
docker rm orchestrator-api

# Option 2: Use different port
docker run -p 9000:8000 orchestrator-api
# OR edit docker-compose.yml ports section

# Option 3: Kill process using port
kill $(lsof -t -i:8000)
```

**Permission Issues:**
```bash
# Fix config file permissions
sudo chown -R 1000:1000 ./config

# Check volume mounts
docker inspect orchestrator-api | jq '.[0].Mounts'
```

#### Python Solutions

**Port Already in Use:**
```bash
# Option 1: Kill existing process
kill $(lsof -t -i:8000)

# Option 2: Use different port
python main.py --port 9000

# Option 3: Find and stop conflicting service
sudo systemctl stop conflicting-service
```

**Missing Dependencies:**
```bash
# Reinstall dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

**Permission Issues:**
```bash
# Check file permissions
ls -la config/config.yaml

# Fix permissions
chmod 644 config/config.yaml
chown $USER:$USER config/config.yaml
```

### 2. Configuration Issues

**Symptoms:**
- Configuration validation errors
- Endpoints not loading
- Hot-reload not working

**Diagnosis:**
```bash
# Validate configuration manually
python -c "
import yaml
from src.orchestrator.models import OrchestratorConfig
with open('config/config.yaml') as f:
    config_data = yaml.safe_load(f)
config = OrchestratorConfig(**config_data)
print('Configuration is valid')
"

# Check configuration status
curl http://localhost:8000/config/status

# Check configuration file watching
curl http://localhost:8000/config/endpoints
```

**Solutions:**

**Invalid YAML Syntax:**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Common YAML issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing quotes around URLs with special characters
# - Invalid list format
```

**Configuration Not Loading:**
```bash
# Check file path
ls -la config/config.yaml

# Reload configuration manually
curl -X POST http://localhost:8000/config/reload

# Check file permissions for watching
chmod 644 config/config.yaml
```

**Example valid configuration:**
```yaml
endpoints:
  - url: "https://httpbin.org/get"
    name: "httpbin_get"
    version: "v1"
    methods: ["GET"]
    auth_type: "none"
    disabled: false
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

### 3. Endpoint Routing Issues

**Symptoms:**
- 404 "No endpoint found for path"
- Requests not reaching backend services
- Wrong endpoint being matched

**Diagnosis:**
```bash
# Check registered endpoints
curl http://localhost:8000/registry/endpoints

# Check active routes
curl http://localhost:8000/router/routes

# Debug specific path routing
curl http://localhost:8000/router/debug/your_service/your_path

# Test endpoint connectivity
curl http://localhost:8000/router/test/your_endpoint_id
```

**Solutions:**

**Path Not Matching:**
```bash
# Check endpoint registration
curl http://localhost:8000/registry/endpoints/your_endpoint_id

# Verify endpoint name in config matches URL path
# URL: /orchestrator/user_service/users
# Config: name: "user_service"
```

**Endpoint Disabled or Unhealthy:**
```bash
# Check endpoint status
curl http://localhost:8000/health/endpoints/your_endpoint_id

# Enable endpoint if disabled
curl -X PUT http://localhost:8000/registry/endpoints/your_endpoint_id/status \
  -H "Content-Type: application/json" \
  -d '"active"'

# Trigger immediate health check
curl -X POST http://localhost:8000/health/check/your_endpoint_id
```

**Wrong Route Matching:**
```bash
# Clear and refresh route cache
curl -X POST http://localhost:8000/router/refresh

# Check route precedence (more specific routes should come first)
curl http://localhost:8000/router/routes | jq '.routes[] | {pattern, endpoint_id}'
```

### 4. Backend Service Connection Issues

**Symptoms:**
- 502 Bad Gateway errors
- Connection timeout errors
- Circuit breakers opening

**Diagnosis:**
```bash
# Check backend service health
curl http://localhost:8000/health/endpoints

# Test direct connectivity to backend
curl https://your-backend-service.com/health

# Check circuit breaker status
curl http://localhost:8000/health/circuit-breakers

# Check network connectivity
ping your-backend-service.com
nslookup your-backend-service.com
```

**Solutions:**

**Connection Timeouts:**
```yaml
# Increase timeout in config
endpoints:
  - url: "https://slow-service.com"
    name: "slow_service"
    timeout: 60  # Increased from 30
```

**DNS Resolution Issues:**
```bash
# Test DNS resolution
nslookup your-backend-service.com

# Add to /etc/hosts if needed
echo "10.0.1.100 your-backend-service.com" >> /etc/hosts
```

**Certificate/SSL Issues:**
```bash
# Test SSL connection
openssl s_client -connect your-backend-service.com:443

# Check certificate validity
curl -v https://your-backend-service.com
```

**Circuit Breaker Issues:**
```bash
# Check circuit breaker status
curl http://localhost:8000/health/circuit-breakers

# Reset stuck circuit breaker
curl -X POST http://localhost:8000/router/reset-circuit-breaker/your_endpoint_id

# Adjust circuit breaker sensitivity
```

```yaml
circuit_breaker:
  failure_threshold: 10  # More tolerant
  reset_timeout: 30     # Faster recovery
  half_open_max_calls: 5 # More test calls
```

### 5. Authentication Issues

**Symptoms:**
- 401 Unauthorized from backend services
- Authentication headers not forwarded
- Token expiration issues

**Diagnosis:**
```bash
# Test with curl and check headers
curl -v -H "Authorization: Bearer your-token" \
  http://localhost:8000/orchestrator/your_service/endpoint

# Check if auth header is being forwarded
curl -H "Authorization: Bearer test-token" \
  http://localhost:8000/orchestrator/httpbin_get | jq '.headers'

# Test direct backend access
curl -H "Authorization: Bearer your-token" \
  https://your-backend-service.com/endpoint
```

**Solutions:**

**Headers Not Forwarded:**
The orchestrator automatically forwards `Authorization` headers. If this isn't working:

```bash
# Check request debug info
curl http://localhost:8000/router/debug/your_service/your_path

# Verify header forwarding is working
curl -H "Authorization: Bearer test" \
  http://localhost:8000/orchestrator/httpbin_get | jq '.headers.Authorization'
```

**Token Expiration:**
```bash
# Check token validity
# The orchestrator doesn't validate tokens - it passes them through
# Verify token with your auth service directly
```

### 6. Performance Issues

**Symptoms:**
- Slow response times
- High CPU/memory usage
- Request timeouts

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" http://localhost:8000/orchestrator/your_service/endpoint

# Monitor system resources
top
free -h
df -h

# Check health summary
curl http://localhost:8000/health/summary
```

**curl-format.txt:**
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

**Solutions:**

**Slow Response Times:**
```bash
# Check if issue is with orchestrator or backend
curl -w "%{time_total}" http://localhost:8000/health  # Orchestrator health
curl -w "%{time_total}" https://your-backend.com/health  # Backend direct
```

**High Resource Usage:**
```bash
# Check for memory leaks
ps aux | grep python
pmap $(pgrep -f orchestrator)

# Restart service if needed
sudo systemctl restart orchestrator

# Consider tuning configuration
```

```yaml
health_check:
  interval: 60  # Less frequent health checks
  timeout: 5    # Shorter timeout

circuit_breaker:
  failure_threshold: 3  # Fail faster
```

### 7. Health Check Issues

**Symptoms:**
- Endpoints marked as unhealthy incorrectly
- Health checks not running
- Inconsistent health status

**Diagnosis:**
```bash
# Check health check configuration
curl http://localhost:8000/health/summary

# Check specific endpoint health
curl http://localhost:8000/health/endpoints/your_endpoint_id

# Trigger manual health check
curl -X POST http://localhost:8000/health/check/your_endpoint_id

# Check health check timing
curl http://localhost:8000/health/endpoints | jq '.endpoints[] | {endpoint_id, last_check_time, status}'
```

**Solutions:**

**Health Checks Not Running:**
```yaml
# Verify health check is enabled in config
health_check:
  enabled: true
  interval: 30
  timeout: 10
```

**False Unhealthy Status:**
```yaml
# Adjust thresholds
health_check:
  unhealthy_threshold: 5  # More tolerance
  healthy_threshold: 1    # Faster recovery
```

**Custom Health Check Path:**
```yaml
endpoints:
  - url: "https://your-service.com"
    name: "your_service"
    health_check_path: "/api/health"  # Custom path
```

## 🔧 Debugging Tools

### Enable Debug Logging

```bash
# Start with debug logging
python main.py --log-level debug

# Or set environment variable
export LOG_LEVEL=DEBUG
python main.py
```

### API Debugging Endpoints

```bash
# Get service information
curl http://localhost:8000/

# View OpenAPI documentation
curl http://localhost:8000/openapi.json | jq

# Check route debugging
curl http://localhost:8000/router/debug/service_name/path

# Test endpoint connectivity
curl http://localhost:8000/router/test/endpoint_id
```

### Log Analysis

```bash
# Monitor logs in real-time
tail -f /var/log/orchestrator/orchestrator.log

# Search for errors
grep ERROR /var/log/orchestrator/orchestrator.log

# Filter by request ID
grep "request-id-12345" /var/log/orchestrator/orchestrator.log
```

## 🚨 Emergency Procedures

### Service Recovery

**Complete Service Restart:**
```bash
# Stop service
sudo systemctl stop orchestrator

# Clear any locks or temp files
rm -f /tmp/orchestrator.*

# Start service
sudo systemctl start orchestrator

# Verify health
curl http://localhost:8000/health
```

**Configuration Reset:**
```bash
# Backup current config
cp config/config.yaml config/config.yaml.backup

# Restore default config
python main.py --create-default-config

# Test with minimal config
python main.py --config config/config.yaml
```

### Circuit Breaker Emergency Reset

```bash
# Reset all circuit breakers
curl -X POST http://localhost:8000/health/reset-all-circuit-breakers

# Or reset specific endpoint
curl -X POST http://localhost:8000/router/reset-circuit-breaker/endpoint_id
```

## 📞 Getting Help

### Information to Gather

When reporting issues, please include:

1. **Service version and environment:**
   ```bash
   python --version
   pip list | grep orchestrator
   curl http://localhost:8000/ | jq '.version'
   ```

2. **Configuration (sanitized):**
   ```bash
   cat config/config.yaml  # Remove sensitive URLs/tokens
   ```

3. **Current status:**
   ```bash
   curl http://localhost:8000/health/status
   curl http://localhost:8000/registry/stats
   ```

4. **Logs:**
   ```bash
   tail -100 /var/log/orchestrator/orchestrator.log
   ```

5. **System information:**
   ```bash
   uname -a
   free -h
   df -h
   ```

### Where to Get Help

- **Docker Issues**: Check the [Docker Guide](../DOCKER.md) for container-specific troubleshooting
- **Documentation**: Check other guides in this documentation  
- **GitHub Issues**: Create an issue with the information above
- **Community**: Join the community discussion forums

## 🔍 Prevention

### Regular Maintenance

```bash
# Weekly health check
curl http://localhost:8000/health/status

# Monitor disk space
df -h

# Check log rotation
ls -la /var/log/orchestrator/

# Update dependencies (test in dev first)
pip list --outdated
```

### Monitoring Setup

```bash
# Set up health check monitoring
*/5 * * * * /opt/orchestrator/scripts/health-check.sh

# Monitor circuit breaker status
*/15 * * * * /opt/orchestrator/scripts/circuit-breaker-check.sh

# Log rotation
0 2 * * * logrotate /etc/logrotate.d/orchestrator
```

This troubleshooting guide should help you resolve most common issues. For complex problems, don't hesitate to enable debug logging and examine the detailed logs. 