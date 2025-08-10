"""
Metrics API routes for Prometheus Agent AI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import structlog

from src.core.prometheus_client import PrometheusClient
from src.api.main import get_prometheus_client

logger = structlog.get_logger()
router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    time: Optional[datetime] = None

class RangeQueryRequest(BaseModel):
    query: str
    start: datetime
    end: datetime
    step: str = "1m"

@router.post("/query")
async def execute_query(
    request: QueryRequest,
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Execute a PromQL query."""
    try:
        logger.info("Executing PromQL query", query=request.query)
        
        result = await prometheus.query(
            query=request.query,
            time=request.time
        )
        
        logger.info("PromQL query executed successfully")
        return {"result": result, "query": request.query}
        
    except Exception as e:
        logger.error("PromQL query execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query_range")
async def execute_range_query(
    request: RangeQueryRequest,
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Execute a PromQL range query."""
    try:
        logger.info("Executing PromQL range query", query=request.query)
        
        result = await prometheus.query_range(
            query=request.query,
            start=request.start,
            end=request.end,
            step=request.step
        )
        
        # Convert to DataFrame for additional processing
        df = prometheus.format_query_result_to_dataframe(result)
        
        logger.info("PromQL range query executed successfully")
        return {
            "result": result,
            "query": request.query,
            "dataframe": df.to_dict() if not df.empty else None,
            "metadata": {
                "start": request.start.isoformat(),
                "end": request.end.isoformat(),
                "step": request.step,
                "data_points": len(df) if not df.empty else 0
            }
        }
        
    except Exception as e:
        logger.error("PromQL range query execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata")
async def get_metrics_metadata(
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get metadata for all available metrics."""
    try:
        logger.info("Fetching metrics metadata")
        
        metadata = await prometheus.get_metrics_metadata()
        
        logger.info("Metrics metadata fetched successfully")
        return {"metadata": metadata}
        
    except Exception as e:
        logger.error("Failed to fetch metrics metadata", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/labels")
async def get_label_names(
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get all label names."""
    try:
        logger.info("Fetching label names")
        
        labels = await prometheus.get_label_names()
        
        logger.info("Label names fetched successfully", count=len(labels))
        return {"labels": labels, "count": len(labels)}
        
    except Exception as e:
        logger.error("Failed to fetch label names", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/labels/{label}/values")
async def get_label_values(
    label: str,
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get all values for a specific label."""
    try:
        logger.info("Fetching label values", label=label)
        
        values = await prometheus.get_label_values(label)
        
        logger.info("Label values fetched successfully", label=label, count=len(values))
        return {"label": label, "values": values, "count": len(values)}
        
    except Exception as e:
        logger.error("Failed to fetch label values", label=label, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/series")
async def get_series(
    match: List[str] = Query(..., description="Series selectors"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get time series matching the provided selectors."""
    try:
        logger.info("Fetching series", match=match)
        
        series = await prometheus.get_series(
            match=match,
            start=start,
            end=end
        )
        
        logger.info("Series fetched successfully", count=len(series))
        return {"series": series, "count": len(series)}
        
    except Exception as e:
        logger.error("Failed to fetch series", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/common")
async def get_common_metrics(
    hours: int = Query(1, description="Hours of data to analyze"),
    prometheus: PrometheusClient = Depends(get_prometheus_client)
):
    """Get commonly used metrics for quick access."""
    try:
        logger.info("Fetching common metrics", hours=hours)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        common_queries = {
            "up": "up",
            "cpu_usage": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "memory_usage": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "disk_usage": "100 - ((node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100)",
            "http_requests_rate": "rate(http_requests_total[5m])",
            "http_request_duration": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        }
        
        results = {}
        
        for name, query in common_queries.items():
            try:
                result = await prometheus.query_range(
                    query=query,
                    start=start_time,
                    end=end_time,
                    step="1m"
                )
                
                if result["result"]:
                    results[name] = {
                        "query": query,
                        "data": result,
                        "has_data": True
                    }
                else:
                    results[name] = {
                        "query": query,
                        "data": None,
                        "has_data": False
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {name}", error=str(e))
                results[name] = {
                    "query": query,
                    "error": str(e),
                    "has_data": False
                }
        
        available_metrics = [name for name, data in results.items() if data.get("has_data")]
        
        logger.info("Common metrics fetched", available_count=len(available_metrics))
        return {
            "metrics": results,
            "available_metrics": available_metrics,
            "time_range": f"{hours} hours"
        }
        
    except Exception as e:
        logger.error("Failed to fetch common metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
