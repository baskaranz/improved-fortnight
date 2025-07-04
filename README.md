# Orchestrator API

A production-ready API gateway that dynamically routes requests to backend services with fault tolerance, health monitoring, and zero-downtime deployment capabilities.

## 🚀 Quick Start

```bash
# Install and run
git clone <repository-url>
cd yet-another-orch-api
pip install -e .
python main.py

# The service starts on http://localhost:8000
curl http://localhost:8000/health
```

➡️ **[Complete Quick Start Guide →](docs/user-guide/quick-start.md)**

## ✨ Key Features

- ✅ **Dynamic Routing** - Route requests to backend services based on configuration
- ✅ **Circuit Breaker Protection** - Automatic fault tolerance and recovery
- ✅ **Health Monitoring** - Real-time endpoint health checking and reporting
- ✅ **Authentication Passthrough** - Forward auth headers to backend services
- ✅ **Hot Configuration Reload** - Update settings without service restart
- ✅ **Zero-Downtime Deployment** - Production-ready deployment patterns
- ✅ **Comprehensive Monitoring** - Built-in health checks and metrics

## 📖 Documentation

### 🎯 [User Guide](docs/user-guide/) - **For Operators & DevOps**

Perfect if you want to **deploy and operate** the service:

| Guide | Description |
|-------|-------------|
| **[Quick Start](docs/user-guide/quick-start.md)** | Get running in 5 minutes |
| **[Deployment](docs/user-guide/deployment.md)** | Production deployment guide |
| **[Configuration](docs/user-guide/configuration.md)** | Complete configuration reference |
| **[Monitoring](docs/user-guide/monitoring.md)** | Health checks and observability |
| **[Troubleshooting](docs/user-guide/troubleshooting.md)** | Common issues and solutions |

### 🛠️ [Developer Guide](docs/developer-guide/) - **For Contributors & Developers**

Perfect if you want to **understand or contribute** to the codebase:

| Guide | Description |
|-------|-------------|
| **[Architecture](docs/developer-guide/architecture.md)** | System design and components |
| **[Contributing](docs/developer-guide/contributing.md)** | How to contribute code |
| **[Development Setup](docs/developer-guide/development-setup.md)** | Local development environment |
| **[Testing](docs/developer-guide/testing.md)** | Running and writing tests |

## 🏗️ Architecture Overview

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
               │         │ │Monitor  │ │Breaker  │
               └─────────┘ └─────────┘ └─────────┘
```

The Orchestrator API acts as a **dynamic API gateway** that:

1. **Receives** requests from client applications
2. **Routes** them to appropriate backend services based on configuration
3. **Monitors** backend service health continuously
4. **Protects** against failures using circuit breaker patterns
5. **Returns** responses with proper error handling

## 🔧 Configuration Example

```yaml
# config/config.yaml
endpoints:
  - url: "https://api.yourcompany.com/users"
    name: "user_service"
    methods: ["GET", "POST", "PUT", "DELETE"]
    auth_type: "bearer"
    timeout: 30

  - url: "https://api.yourcompany.com/orders"
    name: "order_service" 
    methods: ["GET", "POST"]
    auth_type: "bearer"
    timeout: 45

circuit_breaker:
  failure_threshold: 5
  reset_timeout: 60
  
health_check:
  enabled: true
  interval: 30
  timeout: 10
```

## 🌟 Use Cases

### API Gateway
Replace multiple direct service calls with a single orchestrator endpoint:
```bash
# Instead of calling multiple services directly:
curl https://users.api.com/users/123
curl https://orders.api.com/orders?user=123
curl https://notifications.api.com/send

# Call through orchestrator:
curl http://orchestrator:8000/orchestrator/user_service/users/123
curl http://orchestrator:8000/orchestrator/order_service/orders?user=123
curl http://orchestrator:8000/orchestrator/notification_service/send
```

### Microservices Routing
Route requests to different microservices based on path patterns:
```
/orchestrator/user_service/*     → https://users.internal.com/*
/orchestrator/order_service/*    → https://orders.internal.com/*
/orchestrator/inventory_service/* → https://inventory.internal.com/*
```

### Fault Tolerance
Automatic protection against service failures:
- Circuit breakers prevent cascading failures
- Health monitoring detects service issues
- Automatic failover and recovery

### Development & Testing
- Easy service mocking and testing
- Configuration-driven endpoint management
- Dynamic service registration via API

## 🚦 Current Status

- ✅ **Production Ready**: Tested with 202 passing tests (83% coverage)
- ✅ **Active Development**: Regular updates and improvements
- ✅ **Well Documented**: Comprehensive user and developer guides
- ✅ **Community Friendly**: Open to contributions and feedback

## 📊 Quick Health Check

Once running, verify the service health:

```bash
# Service status
curl http://localhost:8000/health/status

# Endpoint registry
curl http://localhost:8000/registry/stats

# Circuit breaker status
curl http://localhost:8000/health/circuit-breakers

# API documentation
open http://localhost:8000/docs
```

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation.

➡️ **[Contributing Guide →](docs/developer-guide/contributing.md)**

### Quick Contributing Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/yet-another-orch-api.git
cd yet-another-orch-api

# Set up development environment
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Create feature branch
git checkout -b feature/your-feature-name
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance async APIs
- Inspired by modern API gateway patterns and microservice architectures
- Thanks to all contributors who help improve this project

---

**Ready to get started?** Choose your path:
- 🎯 **Deploy the service** → [User Guide](docs/user-guide/)
- 🛠️ **Contribute code** → [Developer Guide](docs/developer-guide/)
- 🚀 **Quick start** → [5-minute setup](docs/user-guide/quick-start.md)