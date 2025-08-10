"""
Alerts API routes for Prometheus Agent AI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import structlog

from src.core.prometheus_client import PrometheusClient
from src.api.main import get_prometheus_client

logger = structlog.get_logger()
router = APIRouter()

@router.get("/active")
async def get_active_alerts(
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get all currently active alerts."""
    try:
        logger.info("Fetching active alerts")
        
        alerts = await prometheus.get_active_alerts()
        
        logger.info("Active alerts fetched successfully", count=len(alerts))
        return {"alerts": alerts, "count": len(alerts)}
        
    except Exception as e:
        logger.error("Failed to fetch active alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rules")
async def get_alerting_rules(
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get all alerting rules."""
    try:
        logger.info("Fetching alerting rules")
        
        rules = await prometheus.get_alerting_rules()
        
        logger.info("Alerting rules fetched successfully", count=len(rules))
        return {"rules": rules, "count": len(rules)}
        
    except Exception as e:
        logger.error("Failed to fetch alerting rules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_alert_history(
    alert_name: Optional[str] = Query(None, description="Filter by alert name"),
    hours: int = Query(24, description="Hours of history to fetch"),
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get alert history for a specified time range."""
    try:
        logger.info("Fetching alert history", alert_name=alert_name, hours=hours)
        
        # Note: This would require additional implementation to track alert history
        # For now, we'll return current alerts with a note about historical data
        
        current_alerts = await prometheus.get_active_alerts()
        
        if alert_name:
            filtered_alerts = [
                alert for alert in current_alerts 
                if alert.get("labels", {}).get("alertname") == alert_name
            ]
        else:
            filtered_alerts = current_alerts
        
        logger.info("Alert history fetched", count=len(filtered_alerts))
        return {
            "alerts": filtered_alerts,
            "count": len(filtered_alerts),
            "note": "Currently showing active alerts only. Historical alert tracking requires additional setup."
        }
        
    except Exception as e:
        logger.error("Failed to fetch alert history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_alerts_summary(
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get a summary of alert status."""
    try:
        logger.info("Generating alerts summary")
        
        active_alerts = await prometheus.get_active_alerts()
        alerting_rules = await prometheus.get_alerting_rules()
        
        # Categorize alerts by severity
        severity_counts = {}
        for alert in active_alerts:
            severity = alert.get("labels", {}).get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Get alert states
        state_counts = {}
        for alert in active_alerts:
            state = alert.get("state", "unknown")
            state_counts[state] = state_counts.get(state, 0) + 1
        
        summary = {
            "total_active_alerts": len(active_alerts),
            "total_alerting_rules": len(alerting_rules),
            "severity_breakdown": severity_counts,
            "state_breakdown": state_counts,
            "most_common_alerts": [],  # Could be enhanced with aggregation logic
        }
        
        # Find most common alert names
        alert_names = {}
        for alert in active_alerts:
            name = alert.get("labels", {}).get("alertname", "unknown")
            alert_names[name] = alert_names.get(name, 0) + 1
        
        summary["most_common_alerts"] = sorted(
            alert_names.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        logger.info("Alerts summary generated successfully")
        return summary
        
    except Exception as e:
        logger.error("Failed to generate alerts summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
