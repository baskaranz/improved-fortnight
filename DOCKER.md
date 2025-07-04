# Docker Setup for Orchestrator API

This guide explains how to run the Orchestrator API using Docker for both development and production environments.

## 🐳 Quick Start

### Prerequisites
- Docker Engine 20.10+ 
- Docker Compose 2.0+
- Make (optional, for convenience commands)

### Run with Docker Compose (Recommended)

```bash
# Production mode
docker-compose up -d orchestrator

# Development mode with hot reload
docker-compose --profile dev up -d orchestrator-dev
```

### Run with Make (Convenience)

```bash
# See all available commands
make help

# Quick setup for development
make setup

# Production mode
make up

# Development mode
make up-dev
```

## 🚀 Production Deployment

### Option 1: Docker Compose
```bash
# Build and run
docker-compose up -d orchestrator

# Check status
docker-compose ps
docker-compose logs orchestrator
```

### Option 2: Direct Docker Run
```bash
# Build image
docker build -t orchestrator-api .

# Run container
docker run -d \
  --name orchestrator-api \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config:ro \
  --restart unless-stopped \
  orchestrator-api
```

### Option 3: Custom Configuration
```bash
# Run with custom config file
docker run -d \
  --name orchestrator-api \
  -p 8000:8000 \
  -v /path/to/your/config.yaml:/app/config/config.yaml:ro \
  -e LOG_LEVEL=info \
  orchestrator-api
```

## 🛠️ Development Setup

### Hot Reload Development
```bash
# Start development environment with hot reload
make run-dev
# OR
docker-compose --profile dev up -d orchestrator-dev
```

This mounts your source code into the container for instant reload on changes.

### Running Tests
```bash
# Run tests in container
make test
# OR  
docker-compose exec orchestrator python -m pytest tests/ -v
```

### Access Container Shell
```bash
# Open shell in running container
make shell
# OR
docker-compose exec orchestrator /bin/bash
```

## 🔧 Configuration

### Environment Variables

The container accepts these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `8000` | Port to bind to |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error, critical) |
| `CONFIG_PATH` | `/app/config/config.yaml` | Path to configuration file |
| `RELOAD` | `false` | Enable auto-reload for development |

### Custom Configuration File

Mount your custom configuration file:

```bash
# Using docker-compose
version: '3.8'
services:
  orchestrator:
    image: orchestrator-api
    ports:
      - "8000:8000"
    volumes:
      - /path/to/your/config.yaml:/app/config/config.yaml:ro
    environment:
      - LOG_LEVEL=info

# Using direct docker run
docker run -d \
  -p 8000:8000 \
  -v /path/to/your/config.yaml:/app/config/config.yaml:ro \
  orchestrator-api
```

## 📊 Health Monitoring

### Built-in Health Checks

The container includes health checks:

```bash
# Check container health
docker ps  # Look for "healthy" status

# Manual health check
curl http://localhost:8000/health
```

### Monitoring Endpoints

Once running, access these endpoints:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Endpoint Status**: http://localhost:8000/health/endpoints
- **Registry Stats**: http://localhost:8000/registry/stats

## 🔌 Dynamic Endpoint Registration

The containerized orchestrator supports dynamic endpoint registration:

### Via API
```bash
# Register a new endpoint
curl -X POST http://localhost:8000/registry/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "url": "https://api.example.com/v1",
      "name": "example_api",
      "methods": ["GET", "POST"],
      "auth_type": "bearer",
      "timeout": 30
    }
  }'

# Test the new endpoint
curl http://localhost:8000/orchestrator/example_api/users
```

### Via Configuration File
```yaml
# config/config.yaml
endpoints:
  - url: "https://api.example.com/v1"
    name: "example_api"
    methods: ["GET", "POST"]
    auth_type: "bearer"
    timeout: 30
```

Then reload configuration:
```bash
curl -X POST http://localhost:8000/config/reload
```

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs orchestrator

# Common issues:
# 1. Port 8000 already in use
docker run -p 9000:8000 orchestrator-api

# 2. Permission issues with mounted volumes
sudo chown -R 1000:1000 ./config
```

### Health Check Failures
```bash
# Check if service is responding
curl -f http://localhost:8000/health

# Check container logs
docker-compose logs orchestrator

# Restart container
docker-compose restart orchestrator
```

### Development Hot Reload Not Working
```bash
# Ensure you're using the dev profile
docker-compose --profile dev up -d orchestrator-dev

# Check volume mounts
docker-compose exec orchestrator-dev ls -la /app
```

## 📈 Scaling and Production Tips

### Horizontal Scaling
```bash
# Scale to multiple instances
docker-compose up -d --scale orchestrator=3

# Use a load balancer (nginx, traefik, etc.)
# Each instance will bind to different ports automatically
```

### Production Optimization
```bash
# Use specific image tags
docker build -t orchestrator-api:v1.0.0 .

# Limit container resources
docker run -d \
  --name orchestrator-api \
  --memory=512m \
  --cpus=1.0 \
  -p 8000:8000 \
  orchestrator-api:v1.0.0

# Use restart policies
docker run -d \
  --restart unless-stopped \
  orchestrator-api:v1.0.0
```

### Security Considerations

The Docker image includes security best practices:
- ✅ Non-root user (orchestrator:orchestrator)
- ✅ Minimal base image (python:3.11-slim)
- ✅ No unnecessary packages
- ✅ Proper file permissions

## 🔧 Customization

### Custom Dockerfile
If you need to customize the container:

```dockerfile
# Extend the base image
FROM orchestrator-api:latest

# Add custom packages
USER root
RUN apt-get update && apt-get install -y your-package
USER orchestrator

# Add custom configuration
COPY custom-config.yaml /app/config/
```

### Environment-Specific Configs
```bash
# development.yml
version: '3.8'
services:
  orchestrator:
    extends:
      file: docker-compose.yml
      service: orchestrator
    environment:
      - LOG_LEVEL=debug
      - RELOAD=true

# Use specific compose file
docker-compose -f development.yml up -d
```

## 📝 Common Commands Reference

```bash
# Build
make build
docker-compose build

# Run production
make run
docker-compose up -d orchestrator

# Run development  
make run-dev
docker-compose --profile dev up -d

# Stop
make stop
docker-compose down

# View logs
make logs
docker-compose logs -f orchestrator

# Health check
make health
curl http://localhost:8000/health

# Clean up
make clean
docker-compose down --rmi all --volumes
```

For more detailed configuration options, see [Configuration Guide](docs/user-guide/configuration.md). 