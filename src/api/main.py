"""
Prometheus Agent AI - FastAPI Main Application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import structlog
import os
from dotenv import load_dotenv

from src.api.routes import metrics, alerts, analysis
from src.core.prometheus_client import PrometheusClient
from src.core.openai_client import OpenAIClient
from src.core.agent import PrometheusAgent

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Prometheus Agent AI",
    description="AI-powered Prometheus monitoring and analysis agent",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global clients
prometheus_client = None
openai_client = None
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize clients and services on startup."""
    global prometheus_client, openai_client, agent
    
    try:
        # Initialize Prometheus client
        prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        prometheus_client = PrometheusClient(prometheus_url)
        logger.info("Prometheus client initialized", url=prometheus_url)
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        openai_client = OpenAIClient(api_key=openai_api_key)
        logger.info("OpenAI client initialized")
        
        # Initialize AI agent
        agent = PrometheusAgent(prometheus_client, openai_client)
        logger.info("Prometheus AI Agent initialized")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Prometheus Agent AI")

# Dependency injection
def get_prometheus_client() -> PrometheusClient:
    if prometheus_client is None:
        raise HTTPException(status_code=500, detail="Prometheus client not initialized")
    return prometheus_client

def get_openai_client() -> OpenAIClient:
    if openai_client is None:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")
    return openai_client

def get_agent() -> PrometheusAgent:
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    return agent

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "prometheus_connected": prometheus_client is not None and await prometheus_client.is_healthy(),
        "openai_connected": openai_client is not None,
        "agent_ready": agent is not None
    }

# Include routers
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
