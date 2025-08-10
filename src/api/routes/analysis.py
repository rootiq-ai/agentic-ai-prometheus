"""
Analysis API routes for Prometheus Agent AI.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from src.core.agent import PrometheusAgent
from src.api.main import get_agent

logger = structlog.get_logger()
router = APIRouter()

class HealthAnalysisRequest(BaseModel):
    time_range_hours: int = 1

class NaturalLanguageQueryRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str

class AlertInvestigationRequest(BaseModel):
    alert_name: str

class RecommendationsRequest(BaseModel):
    system_description: str = ""

@router.post("/health")
async def analyze_system_health(
    request: HealthAnalysisRequest,
    agent: PrometheusAgent = Depends(get_agent)
):
    """Analyze system health over a specified time range."""
    try:
        logger.info("Starting system health analysis", time_range_hours=request.time_range_hours)
        
        result = await agent.analyze_system_health(
            time_range_hours=request.time_range_hours
        )
        
        logger.info("System health analysis completed successfully")
        return result
        
    except Exception as e:
        logger.error("System health analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/natural-language")
async def process_natural_language_query(
    request: NaturalLanguageQueryRequest,
    agent: PrometheusAgent = Depends(get_agent)
):
    """Process a natural language query about metrics."""
    try:
        logger.info("Processing natural language query", query=request.query)
        
        result = await agent.natural_language_query(request.query)
        
        logger.info("Natural language query processed successfully")
        return result
        
    except Exception as e:
        logger.error("Natural language query processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    agent: PrometheusAgent = Depends(get_agent)
):
    """Have a conversational interaction with the AI agent."""
    try:
        logger.info("Processing chat message", message=request.message[:100])
        
        response = await agent.chat(request.message)
        
        logger.info("Chat message processed successfully")
        return {"response": response}
        
    except Exception as e:
        logger.error("Chat processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/investigate-alert")
async def investigate_alert(
    request: AlertInvestigationRequest,
    agent: PrometheusAgent = Depends(get_agent)
):
    """Investigate a specific alert and provide detailed analysis."""
    try:
        logger.info("Investigating alert", alert_name=request.alert_name)
        
        result = await agent.investigate_alert(request.alert_name)
        
        logger.info("Alert investigation completed successfully")
        return result
        
    except Exception as e:
        logger.error("Alert investigation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations")
async def get_monitoring_recommendations(
    request: RecommendationsRequest,
    agent: PrometheusAgent = Depends(get_agent)
):
    """Get AI-powered monitoring recommendations."""
    try:
        logger.info("Generating monitoring recommendations")
        
        recommendations = await agent.get_monitoring_recommendations(
            system_description=request.system_description
        )
        
        logger.info("Monitoring recommendations generated successfully")
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error("Failed to generate monitoring recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
