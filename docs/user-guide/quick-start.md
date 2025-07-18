# Quick Start Guide

Get the Orchestrator API running in your environment in **5 minutes**.

## 🔧 Prerequisites

### Option 1: Docker (Recommended)
- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)

### Option 2: Python
- Python 3.9 or higher
- pip (Python package installer)  
- Virtual environment (recommended)

## 🚀 Step 1: Install

### Docker Installation (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd yet-another-orch-api

# Start with Docker Compose
docker-compose up -d orchestrator
```

**Verify installation:**
```bash
docker ps  # Should show orchestrator-api container running
curl http://localhost:8000/health
```

### Python Installation

```bash
# Clone the repository
git clone <repository-url>
cd yet-another-orch-api

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the service
pip install -e .
```

**Verify installation:**
```bash
python main.py --help
```

## ⚙️ Step 2: Start the Service

### Docker

```bash
# Production mode
docker-compose up -d orchestrator

# Development mode with hot reload
docker-compose --profile dev up -d orchestrator-dev

# Using Make (if available)
make up      # Production
make up-dev  # Development
```

### Python

```bash
# Start with default configuration
python main.py

# The service starts on http://localhost:8000
```

You should see output like:
```
Starting Orchestrator API server...
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## ✅ Step 3: Verify It's Working

**Check basic health:**
```bash
curl http://localhost:8000/health
```

**View the interactive API documentation:**
Open http://localhost:8000/docs in your browser

**Check system status:**
```bash
curl http://localhost:8000/health/status
```

You should see the service is healthy and monitoring configured endpoints.

## 🎯 Step 4: Test Endpoint Routing

The service comes with pre-configured test endpoints. Try routing some requests:

```bash
# Route to httpbin service
curl http://localhost:8000/orchestrator/httpbin_get

# Route to JSONPlaceholder service  
curl http://localhost:8000/orchestrator/jsonplaceholder_posts
```

## 📊 Step 5: Monitor Health

**View all endpoint health:**
```bash
curl http://localhost:8000/health/endpoints
```

**Check circuit breaker status:**
```bash
curl http://localhost:8000/health/circuit-breakers
```

**View registry statistics:**
```bash
curl http://localhost:8000/registry/stats
```

## 🔧 Configuration Options

### Docker Configuration

```bash
# Custom port
docker run -d -p 9000:8000 orchestrator-api

# Custom configuration file
docker run -d -p 8000:8000 \
  -v /path/to/your/config.yaml:/app/config/config.yaml:ro \
  orchestrator-api

# Environment variables
docker run -d -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e PORT=8000 \
  orchestrator-api

# Using docker-compose with custom settings
export LOG_LEVEL=debug
export PORT=9000
docker-compose up -d orchestrator
```

### Python Configuration

```bash
# Custom Port
python main.py --port 9000

# Custom Configuration File
python main.py --config /path/to/your/config.yaml

# Debug Mode
python main.py --log-level debug

# Production Mode
python main.py --host 0.0.0.0 --port 8000 --log-level info
```

## 🔐 Adding Your Own Services

### Option 1: Configuration File

Edit `config/config.yaml`:
```yaml
endpoints:
  - url: "https://your-api.com/v1"
    name: "your_service"
    version: "v1" 
    methods: ["GET", "POST"]
    auth_type: "bearer"  # Documentation only
    disabled: false
    timeout: 30
```

**Reload configuration:**
```bash
curl -X POST http://localhost:8000/config/reload
```

### Option 2: Dynamic Registration via API

```bash
curl -X POST http://localhost:8000/registry/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "url": "https://your-api.com/v1",
      "name": "your_service", 
      "methods": ["GET", "POST"],
      "auth_type": "bearer"
    }
  }'
```

**Test your new service:**
```bash
curl http://localhost:8000/orchestrator/your_service/endpoint
```

## 🚨 Common Issues

### Docker Issues

**Container won't start:**
```bash
# Check container logs
docker-compose logs orchestrator

# Check if port is in use
docker ps | grep 8000

# Use different port
docker run -p 9000:8000 orchestrator-api
```

**Container runs but service unreachable:**
```bash
# Check container status
docker ps

# Check container health
docker inspect orchestrator-api | jq '.[0].State.Health'

# Test from inside container
docker exec orchestrator-api curl http://localhost:8000/health
```

**Configuration not loading:**
```bash
# Check volume mount
docker inspect orchestrator-api | jq '.[0].Mounts'

# Fix permissions
sudo chown -R 1000:1000 ./config
```

### Python Issues

**Port Already in Use:**
```bash
# Check what's using the port
lsof -i :8000

# Use a different port
python main.py --port 9000
```

**Service Not Starting:**
```bash
# Check Python version
python --version  # Should be 3.9+

# Check dependencies
pip install -e .
```

### General Issues

**Can't Reach Backend Services:**
```bash
# Check endpoint health
curl http://localhost:8000/health/endpoints/your_service

# Check circuit breaker status
curl http://localhost:8000/health/circuit-breakers
```

## 📈 Next Steps

**Using Docker?** → [Docker Documentation](../DOCKER.md)

**Ready for production?** → [Deployment Guide](deployment.md)

**Need to configure endpoints?** → [Configuration Reference](configuration.md)

**Want to set up monitoring?** → [Monitoring Guide](monitoring.md)

**Having issues?** → [Troubleshooting Guide](troubleshooting.md)

## 🆘 Getting Help

- **Common problems**: See [Troubleshooting](troubleshooting.md)
- **Configuration issues**: Check [Configuration Guide](configuration.md) 
- **API reference**: Open http://localhost:8000/docs
- **Bug reports**: Create an issue on GitHub 