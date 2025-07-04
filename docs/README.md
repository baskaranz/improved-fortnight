# Orchestrator API Documentation

A scalable and extensible API gateway that dynamically routes requests to attached API endpoints based on configuration.

## 📖 Documentation for Different Audiences

### 🚀 [User Guide](user-guide/) - For Operators & DevOps

**Start here if you want to:**
- Deploy the orchestrator in production
- Configure endpoints and routing
- Monitor system health and performance
- Troubleshoot operational issues

**Quick Links:**
- [🏃 Quick Start](user-guide/quick-start.md) - Get running in 5 minutes
- [⚙️ Configuration](user-guide/configuration.md) - Configuration reference
- [🔧 Deployment](user-guide/deployment.md) - Production deployment guide
- [📊 Monitoring](user-guide/monitoring.md) - Health checks and metrics
- [❓ Troubleshooting](user-guide/troubleshooting.md) - Common issues and solutions

### 🛠️ [Developer Guide](developer-guide/) - For Contributors

**Start here if you want to:**
- Contribute code to the project
- Understand the architecture
- Add new features or fix bugs
- Run tests and development workflows

**Quick Links:**
- [🏗️ Development Setup](developer-guide/development-setup.md) - Local dev environment
- [🏛️ Architecture](developer-guide/architecture.md) - Technical architecture
- [🧪 Testing](developer-guide/testing.md) - Running and writing tests
- [🤝 Contributing](developer-guide/contributing.md) - How to contribute
- [📋 Design Decisions](developer-guide/design-decisions.md) - Why we built it this way

## 🆘 Need Help?

- **Users/Operators**: Check the [User Guide troubleshooting](user-guide/troubleshooting.md)
- **Developers**: Check the [Developer Guide](developer-guide/) or [Contributing Guide](developer-guide/contributing.md)
- **Issues**: [Create an issue](https://github.com/your-org/yet-another-orch-api/issues) on GitHub

## 🚀 Quick Overview

The Orchestrator API is a FastAPI-based service that:

- **Routes requests** dynamically to registered backend services
- **Monitors health** of all endpoints with circuit breaker protection
- **Manages configuration** with hot-reloading and file watching
- **Provides authentication passthrough** to backend services
- **Offers comprehensive APIs** for management and monitoring

## 📋 System Requirements

- Python 3.9+
- FastAPI
- HTTPX for async HTTP requests
- YAML configuration support

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details. 