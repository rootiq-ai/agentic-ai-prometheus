#!/bin/bash

# Prometheus Agent AI - Service Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🤖 Prometheus Agent AI - Service Startup${NC}"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ Please edit .env file and add your OpenAI API key, then run this script again.${NC}"
    exit 1
fi

# Load environment variables
source .env

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY is not set in .env file${NC}"
    echo "Please edit .env file and add your OpenAI API key"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking required ports..."
ports_ok=true

if ! check_port 8000; then
    echo -e "${RED}❌ Port 8000 (API) is in use${NC}"
    ports_ok=false
fi

if ! check_port 8501; then
    echo -e "${RED}❌ Port 8501 (UI) is in use${NC}"
    ports_ok=false
fi

if ! check_port 9090; then
    echo -e "${RED}❌ Port 9090 (Prometheus) is in use${NC}"
    ports_ok=false
fi

if [ "$ports_ok" = false ]; then
    echo -e "${RED}❌ Some required ports are in use. Please free them and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required ports are available${NC}"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p config

# Create basic Prometheus config if it doesn't exist
if [ ! -f config/prometheus.yml ]; then
    echo "📝 Creating basic Prometheus configuration..."
    cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
  
  - job_name: 'prometheus-agent-api'
    static_configs:
      - targets: ['prometheus-agent-api:8000']
    metrics_path: '/metrics'
EOF
fi

# Create basic Alertmanager config if it doesn't exist
if [ ! -f config/alertmanager.yml ]; then
    echo "📝 Creating basic Alertmanager configuration..."
    cat > config/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourcompany.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'
EOF
fi

# Build and start services
echo -e "${GREEN}🚀 Building and starting services...${NC}"

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down --remove-orphans

# Build the application
echo "🔨 Building Prometheus Agent AI..."
docker-compose build

# Start services
echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "   Waiting for $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "   ${GREEN}✅ $service_name is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start within expected time${NC}"
    return 1
}

# Wait for services
wait_for_service "Prometheus" "http://localhost:9090/-/ready"
wait_for_service "API" "http://localhost:8000/health"
wait_for_service "UI" "http://localhost:8501"

echo ""
echo -e "${GREEN}🎉 Prometheus Agent AI is now running!${NC}"
echo ""
echo "📊 Services:"
echo "   • Web UI:        http://localhost:8501"
echo "   • API Docs:      http://localhost:8000/api/docs"
echo "   • Prometheus:    http://localhost:9090"
echo "   • Node Exporter: http://localhost:9100"
echo "   • cAdvisor:      http://localhost:8080"
echo "   • Alertmanager:  http://localhost:9093"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   • Open http://localhost:8501 to access the AI agent"
echo "   • Check service logs with: docker-compose logs -f [service-name]"
echo "   • Stop services with: docker-compose down"
echo ""
echo -e "${GREEN}Happy monitoring! 🤖${NC}"
