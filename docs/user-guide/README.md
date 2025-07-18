# User Guide - Orchestrator API

**For Operators, DevOps Engineers, and Service Administrators**

Welcome! This guide will help you deploy, configure, and operate the Orchestrator API in your environment.

## What is the Orchestrator API?

The Orchestrator API is a **production-ready API gateway** that dynamically routes requests to your backend services with:

- ✅ **Zero-downtime deployment** with health monitoring
- ✅ **Circuit breaker protection** for fault tolerance  
- ✅ **Authentication passthrough** to backend services
- ✅ **Dynamic service registration** via REST API or configuration
- ✅ **Real-time monitoring** and health dashboards
- ✅ **Hot configuration reloading** without service restart

## 🏃 Quick Start (5 minutes)

### Option 1: Docker (Recommended)
```bash
git clone <repository-url>
cd yet-another-orch-api
docker-compose up -d orchestrator
```

### Option 2: Python
```bash
git clone <repository-url>
cd yet-another-orch-api
pip install -e .
python main.py
```

**Verify it's working:**
```bash
curl http://localhost:8000/health
```

**View the API documentation:**
Open http://localhost:8000/docs in your browser

➡️ **[Continue with detailed Quick Start →](quick-start.md)**

## 📋 Documentation Contents

| Guide | Description | When to Use |
|-------|-------------|-------------|
| **[Quick Start](quick-start.md)** | Get running in 5 minutes | First time setup |
| **[Configuration](configuration.md)** | Complete configuration reference | Setting up endpoints |
| **[Deployment](deployment.md)** | Production deployment guide | Going to production |
| **[API Reference](api-reference.md)** | REST API documentation | Integration work |
| **[Monitoring](monitoring.md)** | Health checks and metrics | Operations & monitoring |
| **[Troubleshooting](troubleshooting.md)** | Common issues and solutions | When things go wrong |
| **[Examples](examples/)** | Real-world configuration examples | Inspiration & templates |

## 🎯 Common Use Cases

### API Gateway
Route requests to multiple backend services through a single entry point:
```bash
# All requests go through the orchestrator
curl http://orchestrator:8000/orchestrator/user-service/users
curl http://orchestrator:8000/orchestrator/order-service/orders
```

### Service Discovery
Dynamically register/unregister services without configuration changes:
```bash
# Register a new service
curl -X POST http://orchestrator:8000/registry/endpoints \
  -H "Content-Type: application/json" \
  -d '{"config": {"url": "http://new-service:8080", "name": "new_service"}}'
```

### Health Monitoring
Monitor all your backend services from one dashboard:
```bash
# Check overall system health
curl http://orchestrator:8000/health/status

# Check specific service health
curl http://orchestrator:8000/health/endpoints/user-service
```

### Circuit Breaker Protection
Automatic fault tolerance when backend services fail:
```bash
# View circuit breaker status
curl http://orchestrator:8000/health/circuit-breakers
```

## 💡 Key Concepts

| Concept | Description |
|---------|-------------|
| **Endpoint** | A backend service that the orchestrator routes to |
| **Registry** | Internal database of all registered endpoints |
| **Health Check** | Automated monitoring of endpoint availability |
| **Circuit Breaker** | Fault tolerance mechanism that prevents cascading failures |
| **Route** | URL pattern that maps to a specific endpoint |

## 🔧 Production Considerations

- **Security**: Configure authentication and HTTPS
- **Monitoring**: Set up health check alerts
- **Scaling**: Run multiple orchestrator instances behind a load balancer
- **Backup**: Keep configuration files in version control

## 🆘 Getting Help

- **Common issues**: Check [Troubleshooting](troubleshooting.md)
- **Configuration problems**: See [Configuration Guide](configuration.md)
- **Performance issues**: Review [Monitoring Guide](monitoring.md)
- **Bug reports**: Create an issue on GitHub

## 📈 Next Steps

1. **New to the service?** → [Quick Start](quick-start.md)
2. **Ready for production?** → [Deployment Guide](deployment.md)  
3. **Need to configure endpoints?** → [Configuration Reference](configuration.md)
4. **Want to monitor health?** → [Monitoring Guide](monitoring.md) 