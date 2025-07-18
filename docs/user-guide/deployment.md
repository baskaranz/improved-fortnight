# Production Deployment Guide

This guide covers deploying the Orchestrator API in production environments.

## 🎯 Production Checklist

Before deploying to production, ensure you have:

- [ ] **Python 3.9+** installed on target servers
- [ ] **Configuration file** prepared and validated
- [ ] **SSL/TLS certificates** for HTTPS (recommended)
- [ ] **Monitoring** and alerting configured
- [ ] **Backup strategy** for configuration files
- [ ] **Log aggregation** configured
- [ ] **Resource limits** planned (CPU, memory)

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)

**Best for**: Production environments, containerized infrastructure, Kubernetes

```bash
# Production deployment with Docker Compose
docker-compose up -d orchestrator

# Or with custom configuration
docker run -d \
  --name orchestrator-api \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config:ro \
  --restart unless-stopped \
  orchestrator-api
```

**Verify deployment:**
```bash
docker ps  # Check container status
curl http://localhost:8000/health
```

### Option 2: Direct Python Deployment

**Best for**: Small to medium deployments, development staging

```bash
# Production server setup
# 1. Install dependencies
pip install -e .

# 2. Create production configuration
cp config/config.yaml config/prod-config.yaml
# Edit prod-config.yaml with production endpoints

# 3. Start with production settings
python main.py \
  --config config/prod-config.yaml \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info
```

### Option 2: Uvicorn with Multiple Workers

**Best for**: Higher load, better performance

```bash
# Install uvicorn with worker management
pip install "uvicorn[standard]" gunicorn

# Start with multiple workers
uvicorn src.orchestrator.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --access-log \
  --log-level info
```

### Option 3: Docker with Kubernetes

**Best for**: Large-scale deployments, orchestrated environments

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator-api
  template:
    metadata:
      labels:
        app: orchestrator-api
    spec:
      containers:
      - name: orchestrator-api
        image: orchestrator-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: CONFIG_PATH
          value: "/app/config/config.yaml"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: orchestrator-config
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
spec:
  selector:
    app: orchestrator-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes-deployment.yaml

# Check deployment status
kubectl get pods -l app=orchestrator-api
kubectl get service orchestrator-service
```

> **📖 Complete Docker Guide**: For comprehensive Docker setup, configuration, and troubleshooting, see [DOCKER.md](../DOCKER.md)

### Option 4: Systemd Service

**Best for**: Linux servers, automatic startup

```ini
# /etc/systemd/system/orchestrator.service
[Unit]
Description=Orchestrator API
After=network.target

[Service]
Type=simple
User=orchestrator
Group=orchestrator
WorkingDirectory=/opt/orchestrator
Environment=CONFIG_PATH=/opt/orchestrator/config/prod-config.yaml
ExecStart=/opt/orchestrator/venv/bin/python main.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable orchestrator
sudo systemctl start orchestrator
sudo systemctl status orchestrator
```

## 🔧 Production Configuration

### Configuration File

```yaml
# config/prod-config.yaml
endpoints:
  - url: "https://api.internal.company.com/users"
    name: "user_service"
    version: "v1"
    methods: ["GET", "POST", "PUT", "DELETE"]
    auth_type: "bearer"
    health_check_path: "/health"
    timeout: 30
    disabled: false

  - url: "https://orders.internal.company.com/api"
    name: "order_service"
    version: "v2"
    methods: ["GET", "POST"]
    auth_type: "bearer"
    health_check_path: "/api/health"
    timeout: 45
    disabled: false

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

### Environment Variables

```bash
# Production environment variables
export CONFIG_PATH="/opt/orchestrator/config/prod-config.yaml"
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="INFO"
export PYTHONPATH="/opt/orchestrator/src"
```

## 🔐 Security Configuration

### 1. HTTPS/TLS Setup

**Option A: Reverse Proxy (Recommended)**

```nginx
# /etc/nginx/sites-available/orchestrator
server {
    listen 443 ssl;
    server_name api.yourcompany.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option B: Direct TLS (if supported)**

```bash
# Start with TLS (requires additional setup)
uvicorn src.orchestrator.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile /path/to/private.key \
  --ssl-certfile /path/to/certificate.crt
```

### 2. Network Security

```bash
# Firewall rules (example with ufw)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # Orchestrator (if direct access needed)
sudo ufw enable
```

### 3. User Permissions

```bash
# Create dedicated user
sudo useradd --system --home /opt/orchestrator orchestrator
sudo mkdir -p /opt/orchestrator/{config,logs}
sudo chown -R orchestrator:orchestrator /opt/orchestrator
sudo chmod 750 /opt/orchestrator
sudo chmod 640 /opt/orchestrator/config/*.yaml
```

## 📊 Monitoring & Observability

### 1. Health Check Monitoring

```bash
# Basic health check script
#!/bin/bash
# /opt/orchestrator/scripts/health-check.sh

ENDPOINT="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "Orchestrator is healthy"
    exit 0
else
    echo "Orchestrator is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### 2. Log Configuration

```bash
# Configure log rotation
# /etc/logrotate.d/orchestrator
/opt/orchestrator/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    copytruncate
    notifempty
}
```

### 3. Metrics Collection

```yaml
# Add to production config for Prometheus monitoring
# config/prod-config.yaml
metrics:
  enabled: true
  port: 9090
  path: "/metrics"
```

```bash
# Monitor metrics endpoint
curl http://localhost:8000/health/status
curl http://localhost:8000/registry/stats
```

## 🔄 High Availability Setup

### Load Balancer Configuration

```nginx
# nginx load balancer
upstream orchestrator_backend {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 443 ssl;
    server_name api.yourcompany.com;

    location / {
        proxy_pass http://orchestrator_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Health Check Configuration

```yaml
# Enhanced health check for HA
health_check:
  enabled: true
  interval: 15  # More frequent checks in HA setup
  timeout: 5    # Faster timeout
  unhealthy_threshold: 2
  healthy_threshold: 1
```

## 🔧 Performance Tuning

### Resource Requirements

**Minimum (Development/Testing)**:
- CPU: 1 core
- RAM: 512MB
- Storage: 1GB

**Recommended (Production)**:
- CPU: 2-4 cores
- RAM: 2-4GB
- Storage: 10GB (for logs)

**High Traffic (Enterprise)**:
- CPU: 4-8 cores
- RAM: 4-8GB
- Storage: 50GB+ (for logs and metrics)

### Uvicorn Worker Configuration

```bash
# Calculate workers: (2 x CPU cores) + 1
WORKERS=$(python -c "import multiprocessing; print(2 * multiprocessing.cpu_count() + 1)")

uvicorn src.orchestrator.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker
```

### Configuration Optimizations

```yaml
# Performance-optimized config
circuit_breaker:
  failure_threshold: 3    # Fail faster
  reset_timeout: 30      # Recover faster
  half_open_max_calls: 1 # Conservative testing

health_check:
  enabled: true
  interval: 20           # Balanced frequency
  timeout: 5            # Quick timeout
  unhealthy_threshold: 2 # Fail fast
  healthy_threshold: 1   # Recover fast
```

## 🔄 Deployment Pipeline

### Automated Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

DEPLOY_DIR="/opt/orchestrator"
BACKUP_DIR="/opt/orchestrator/backups"
CONFIG_FILE="config/prod-config.yaml"

echo "Starting deployment..."

# 1. Create backup
mkdir -p $BACKUP_DIR
cp $DEPLOY_DIR/$CONFIG_FILE $BACKUP_DIR/config-$(date +%Y%m%d-%H%M%S).yaml

# 2. Update application
cd $DEPLOY_DIR
git pull origin main
pip install -e .

# 3. Validate configuration
python main.py --config $CONFIG_FILE --validate-only

# 4. Restart service
sudo systemctl restart orchestrator

# 5. Health check
sleep 5
if curl -f http://localhost:8000/health; then
    echo "Deployment successful!"
else
    echo "Deployment failed! Rolling back..."
    sudo systemctl stop orchestrator
    # Restore backup and restart
    exit 1
fi
```

### Zero-Downtime Deployment

```bash
# Blue-green deployment approach
# 1. Deploy to secondary instance
# 2. Health check secondary
# 3. Switch load balancer traffic
# 4. Stop primary instance
# 5. Deploy to primary
# 6. Switch back if needed
```

## 🚨 Troubleshooting Production Issues

### Common Production Issues

**Service Won't Start**:
```bash
# Check logs
journalctl -u orchestrator -f

# Check configuration
python main.py --config config/prod-config.yaml --validate-only

# Check permissions
ls -la /opt/orchestrator/
sudo systemctl status orchestrator
```

**High Memory Usage**:
```bash
# Monitor memory
ps aux | grep python
free -h

# Restart service
sudo systemctl restart orchestrator
```

**Circuit Breakers Stuck Open**:
```bash
# Check circuit breaker status
curl http://localhost:8000/health/circuit-breakers

# Reset if needed
curl -X POST http://localhost:8000/health/reset-circuit-breakers
```

### Emergency Procedures

**Service Down**:
1. Check systemd status: `sudo systemctl status orchestrator`
2. Check logs: `journalctl -u orchestrator -n 50`
3. Restart service: `sudo systemctl restart orchestrator`
4. If still failing, restore from backup configuration

**Configuration Issues**:
1. Validate config: `python main.py --config config/prod-config.yaml --validate-only`
2. Restore backup: `cp /opt/orchestrator/backups/config-*.yaml config/prod-config.yaml`
3. Reload: `curl -X POST http://localhost:8000/config/reload`

## 📈 Scaling Considerations

- **Horizontal Scaling**: Deploy multiple instances behind load balancer
- **Vertical Scaling**: Increase CPU/memory resources
- **Configuration Sharing**: Use shared storage for configuration files
- **Database Backend**: Consider external storage for large endpoint registries
- **Caching**: Implement Redis for shared state in multi-instance deployments

## 🔍 Post-Deployment Verification

```bash
# Complete health check
curl http://localhost:8000/health/status

# Verify endpoint registration
curl http://localhost:8000/registry/stats

# Test request routing
curl http://localhost:8000/orchestrator/your_service/health

# Check metrics
curl http://localhost:8000/health/summary
```

This deployment guide provides a comprehensive foundation for running the Orchestrator API in production environments with appropriate security, monitoring, and scalability considerations. 