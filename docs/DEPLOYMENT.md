# Prometheus Agent AI - Deployment Guide

This guide covers different deployment strategies for Prometheus Agent AI, from local development to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker Compose)](#quick-start-docker-compose)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **CPU:** 2+ cores
- **Memory:** 4GB+ RAM (8GB+ recommended for production)
- **Storage:** 10GB+ free space
- **OS:** Linux, macOS, or Windows with WSL2

### Required Software

- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Python:** 3.11+ (for local development)
- **Git:** Latest version

### Required Services

- **OpenAI API Key:** Get from [OpenAI Platform](https://platform.openai.com/)
- **Prometheus:** Running instance or will be deployed with the stack

---

## Quick Start (Docker Compose)

The fastest way to get Prometheus Agent AI running with all dependencies.

### 1. Clone Repository

```bash
git clone <repository-url>
cd prometheus-agent-ai
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**
```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Prometheus Configuration
PROMETHEUS_URL=http://prometheus:9090

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# UI Configuration
STREAMLIT_PORT=8501
```

### 3. Deploy Stack

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run automated setup and start
./scripts/start_services.sh
```

This script will:
- ✅ Validate configuration
- ✅ Check port availability
- ✅ Create necessary directories
- ✅ Generate Prometheus configuration
- ✅ Build and start all services
- ✅ Verify service health

### 4. Access Services

After deployment completes:

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:8501 | Main Streamlit interface |
| **API Docs** | http://localhost:8000/api/docs | Interactive API documentation |
| **Prometheus** | http://localhost:9090 | Prometheus web interface |
| **Alertmanager** | http://localhost:9093 | Alert management |
| **cAdvisor** | http://localhost:8080 | Container metrics |
| **Node Exporter** | http://localhost:9100 | System metrics |

### 5. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "prometheus_connected": true,
#   "openai_connected": true,
#   "agent_ready": true
# }
```

---

## Local Development Setup

For active development and testing.

### 1. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Start External Dependencies

```bash
# Start only Prometheus stack
docker-compose up -d prometheus node-exporter cadvisor alertmanager
```

### 3. Configure Development Environment

```bash
# Copy and edit environment
cp .env.example .env

# Update for local development
export PROMETHEUS_URL=http://localhost:9090
export OPENAI_API_KEY=your_key_here
export API_RELOAD=true
```

### 4. Start Services

```bash
# Terminal 1: Start API server
./scripts/start_api.sh

# Terminal 2: Start UI
./scripts/start_ui.sh
```

### 5. Development Workflow

```bash
# Run tests
pytest src/tests/

# Code formatting
black src/
flake8 src/

# Type checking
mypy src/
```

---

## Production Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Prometheus    │    │   OpenAI API    │
│   (nginx/ALB)   │    │   Cluster       │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Prometheus      │◄──►│ Agent AI API    │◄──►│ Agent AI UI     │
│ Agent AI        │    │ (Multiple       │    │ (Static/CDN)    │
│ (Multi-instance)│    │ Instances)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  prometheus-agent-api:
    build:
      context: .
      target: production
    command: api
    ports:
      - "8000:8000"
    environment:
      - PROMETHEUS_URL=${PROMETHEUS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - API_WORKERS=4
      - API_RELOAD=false
    env_file: .env.prod
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  prometheus-agent-ui:
    build:
      context: .
      target: production
    command: ui
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://prometheus-agent-api:8000
    env_file: .env.prod
    depends_on:
      - prometheus-agent-api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - prometheus-agent-api
      - prometheus-agent-ui
    restart: unless-stopped
```

### 2. Production Environment Configuration

Create `.env.prod`:

```bash
# Production Configuration
NODE_ENV=production

# Security
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# OpenAI (Production)
OPENAI_API_KEY=your_production_openai_key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000

# Prometheus
PROMETHEUS_URL=http://your-prometheus-cluster:9090

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false

# Database (if using)
DATABASE_URL=postgresql://user:password@postgres:5432/prometheus_agent

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
```

### 3. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server prometheus-agent-api:8000;
    }

    upstream ui {
        server prometheus-agent-ui:8501;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=ui:10m rate=5r/s;

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # UI
        location / {
            limit_req zone=ui burst=10 nodelay;
            proxy_pass http://ui;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (no rate limit)
        location /health {
            proxy_pass http://api;
            access_log off;
        }
    }
}
```

### 4. Deploy to Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
```

---

## Kubernetes Deployment

### 1. Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prometheus-agent-ai

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-agent-config
  namespace: prometheus-agent-ai
data:
  PROMETHEUS_URL: "http://prometheus.monitoring.svc.cluster.local:9090"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LOG_LEVEL: "INFO"
```

### 2. Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: prometheus-agent-secrets
  namespace: prometheus-agent-ai
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  SECRET_KEY: <base64-encoded-secret>
```

### 3. API Deployment

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-agent-api
  namespace: prometheus-agent-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prometheus-agent-api
  template:
    metadata:
      labels:
        app: prometheus-agent-api
    spec:
      containers:
      - name: api
        image: prometheus-agent-ai:latest
        command: ["/app/entrypoint.sh", "api"]
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: prometheus-agent-config
        - secretRef:
            name: prometheus-agent-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
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

---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-agent-api-service
  namespace: prometheus-agent-ai
spec:
  selector:
    app: prometheus-agent-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

### 4. UI Deployment

```yaml
# k8s/ui-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-agent-ui
  namespace: prometheus-agent-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prometheus-agent-ui
  template:
    metadata:
      labels:
        app: prometheus-agent-ui
    spec:
      containers:
      - name: ui
        image: prometheus-agent-ai:latest
        command: ["/app/entrypoint.sh", "ui"]
        ports:
        - containerPort: 8501
        env:
        - name: API_BASE_URL
          value: "http://prometheus-agent-api-service:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-agent-ui-service
  namespace: prometheus-agent-ai
spec:
  selector:
    app: prometheus-agent-ui
  ports:
  - protocol: TCP
    port: 8501
    targetPort: 8501
  type: ClusterIP
```

### 5. Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prometheus-agent-ingress
  namespace: prometheus-agent-ai
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "10"
spec:
  tls:
  - hosts:
    - prometheus-agent.yourdomain.com
    secretName: prometheus-agent-tls
  rules:
  - host: prometheus-agent.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: prometheus-agent-api-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-agent-ui-service
            port:
              number: 8501
```

### 6. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n prometheus-agent-ai
kubectl get services -n prometheus-agent-ai
kubectl get ingress -n prometheus-agent-ai

# View logs
kubectl logs -f deployment/prometheus-agent-api -n prometheus-agent-ai
```

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ |
| `PROMETHEUS_URL` | Prometheus endpoint | `http://localhost:9090` | ✅ |
| `API_HOST` | API bind address | `0.0.0.0` | - |
| `API_PORT` | API port | `8000` | - |
| `STREAMLIT_PORT` | UI port | `8501` | - |
| `LOG_LEVEL` | Logging level | `INFO` | - |
| `DATABASE_URL` | Database connection | SQLite | - |

### Prometheus Configuration

Ensure your Prometheus config includes the agent:

```yaml
scrape_configs:
  - job_name: 'prometheus-agent-api'
    static_configs:
      - targets: ['prometheus-agent-api:8000']
    metrics_path: /metrics
    scrape_interval: 30s
```

---

## Monitoring & Maintenance

### Health Monitoring

```bash
# API health
curl http://localhost:8000/health

# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Container health
docker-compose ps
docker-compose logs -f prometheus-agent-api
```

### Backup & Recovery

```bash
# Backup Prometheus data
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Backup configuration
tar czf config-backup.tar.gz config/ .env

# Recovery
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar xzf /backup/prometheus-backup.tar.gz -C /
```

### Updates

```bash
# Update to latest version
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

### Log Management

```bash
# View logs
docker-compose logs -f prometheus-agent-api
docker-compose logs -f prometheus-agent-ui

# Log rotation (add to crontab)
0 0 * * * docker run --rm -v $(pwd)/logs:/logs alpine find /logs -name "*.log" -mtime +7 -delete
```

---

## Troubleshooting

### Common Issues

#### 1. OpenAI Connection Failed
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### 2. Prometheus Connection Failed
```bash
# Check Prometheus health
curl http://localhost:9090/-/healthy

# Check network connectivity
docker-compose exec prometheus-agent-api curl http://prometheus:9090/api/v1/query?query=up
```

#### 3. UI Not Loading
```bash
# Check UI logs
docker-compose logs prometheus-agent-ui

# Check API connectivity
curl http://localhost:8000/health
```

#### 4. High Memory Usage
```bash
# Check container memory
docker stats

# Restart services
docker-compose restart prometheus-agent-api
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run in development mode
export API_RELOAD=true

# Access container shell
docker-compose exec prometheus-agent-api bash
```

### Performance Tuning

```bash
# Increase API workers
export API_WORKERS=8

# Adjust OpenAI parameters
export OPENAI_MAX_TOKENS=1500
export OPENAI_TEMPERATURE=0.3

# Configure Prometheus retention
prometheus --storage.tsdb.retention.time=30d
```

---

## Security Considerations

### Production Security Checklist

- [ ] **API Keys**: Store in secure secret management
- [ ] **HTTPS**: Enable SSL/TLS encryption
- [ ] **Firewall**: Restrict access to necessary ports
- [ ] **Authentication**: Implement API authentication
- [ ] **Rate Limiting**: Configure request limits
- [ ] **Monitoring**: Set up security monitoring
- [ ] **Updates**: Keep dependencies updated
- [ ] **Backups**: Regular encrypted backups

### Network Security

```bash
# Create isolated network
docker network create prometheus-network

# Use in docker-compose
networks:
  default:
    external:
      name: prometheus-network
```

---

For additional support, check the [troubleshooting section](./USAGE.md#troubleshooting) or create an issue in the repository.
