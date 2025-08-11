#!/bin/bash

# Start API Server Script for Prometheus Agent AI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Prometheus Agent AI API Server${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Please create one from .env.example${NC}"
    exit 1
fi

# Load environment variables
source .env

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY is not set in .env file${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Default values
HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-8000}
WORKERS=${API_WORKERS:-1}
RELOAD=${API_RELOAD:-false}

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo "Please stop the service using this port or change API_PORT in .env"
    exit 1
fi

echo -e "${GREEN}📋 Configuration:${NC}"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Workers: $WORKERS"
echo "   Reload: $RELOAD"
echo "   Prometheus URL: ${PROMETHEUS_URL:-http://localhost:9090}"
echo ""

# Start the API server
echo -e "${GREEN}🔄 Starting FastAPI server...${NC}"

if [ "$RELOAD" = "true" ]; then
    echo -e "${YELLOW}🔧 Running in development mode with auto-reload${NC}"
    uvicorn src.api.main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level info
else
    echo -e "${GREEN}🏭 Running in production mode${NC}"
    uvicorn src.api.main:app \
        --host $HOST \
        --port $PORT \
        --workers $WORKERS \
        --log-level info
fi
