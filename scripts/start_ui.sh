#!/bin/bash

# Start UI Script for Prometheus Agent AI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎨 Starting Prometheus Agent AI Web UI${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Using default values.${NC}"
else
    source .env
fi

# Default values
PORT=${STREAMLIT_PORT:-8501}
API_URL=${API_BASE_URL:-http://localhost:8000}

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo "Please stop the service using this port or change STREAMLIT_PORT in .env"
    exit 1
fi

# Check if API is accessible
echo -e "${GREEN}🔍 Checking API connectivity...${NC}"
if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is accessible at $API_URL${NC}"
else
    echo -e "${YELLOW}⚠️  API is not accessible at $API_URL${NC}"
    echo "   Make sure the API server is running or update API_BASE_URL in .env"
    echo "   Continuing anyway - you can start the API later..."
fi

echo -e "${GREEN}📋 Configuration:${NC}"
echo "   UI Port: $PORT"
echo "   API URL: $API_URL"
echo ""

# Set environment variable for the Streamlit app
export API_BASE_URL=$API_URL

# Start Streamlit
echo -e "${GREEN}🔄 Starting Streamlit web UI...${NC}"
echo -e "${GREEN}📱 UI will be available at: http://localhost:$PORT${NC}"
echo ""

streamlit run src/ui/streamlit_app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
