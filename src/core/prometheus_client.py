"""
Prometheus Client for querying metrics and managing alerts.
"""

import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog
from prometheus_api_client import PrometheusConnect

logger = structlog.get_logger()

class PrometheusClient:
    """Client for interacting with Prometheus."""
    
    def __init__(self, prometheus_url: str):
        """Initialize Prometheus client.
        
        Args:
            prometheus_url: URL of the Prometheus server
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.client = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def is_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = await self.session.get(f"{self.prometheus_url}/-/healthy")
            return response.status_code == 200
        except Exception as e:
            logger.error("Prometheus health check failed", error=str(e))
            return False
    
    async def query(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        """Execute a PromQL query.
        
        Args:
            query: PromQL query string
            time: Optional timestamp for the query
            
        Returns:
            Query result
        """
        try:
            params = {"query": query}
            if time:
                params["time"] = time.timestamp()
                
            response = await self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Query execution failed", query=query, error=str(e))
            raise
    
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Dict[str, Any]:
        """Execute a PromQL range query.
        
        Args:
            query: PromQL query string
            start: Start time
            end: End time
            step: Query resolution step
            
        Returns:
            Range query result
        """
        try:
            params = {
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step
            }
            
            response = await self.session.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Range query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Range query execution failed", query=query, error=str(e))
            raise
    
    async def get_metrics_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all available metrics."""
        try:
            response = await self.session.get(f"{self.prometheus_url}/api/v1/metadata")
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Metadata query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Failed to get metrics metadata", error=str(e))
            raise
    
    async def get_label_names(self) -> List[str]:
        """Get all label names."""
        try:
            response = await self.session.get(f"{self.prometheus_url}/api/v1/labels")
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Labels query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Failed to get label names", error=str(e))
            raise
    
    async def get_label_values(self, label: str) -> List[str]:
        """Get all values for a specific label.
        
        Args:
            label: Label name
            
        Returns:
            List of label values
        """
        try:
            response = await self.session.get(
                f"{self.prometheus_url}/api/v1/label/{label}/values"
            )
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Label values query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Failed to get label values", label=label, error=str(e))
            raise
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        try:
            response = await self.session.get(f"{self.prometheus_url}/api/v1/alerts")
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Alerts query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]["alerts"]
            
        except Exception as e:
            logger.error("Failed to get active alerts", error=str(e))
            raise
    
    async def get_alerting_rules(self) -> List[Dict[str, Any]]:
        """Get all alerting rules."""
        try:
            response = await self.session.get(f"{self.prometheus_url}/api/v1/rules")
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Rules query failed: {result.get('error', 'Unknown error')}")
                
            rules = []
            for group in result["data"]["groups"]:
                for rule in group["rules"]:
                    if rule["type"] == "alerting":
                        rules.append(rule)
            
            return rules
            
        except Exception as e:
            logger.error("Failed to get alerting rules", error=str(e))
            raise
    
    async def get_series(
        self,
        match: List[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get time series matching the provided selectors.
        
        Args:
            match: List of series selectors
            start: Start time (optional)
            end: End time (optional)
            
        Returns:
            List of series metadata
        """
        try:
            params = {"match[]": match}
            if start:
                params["start"] = start.timestamp()
            if end:
                params["end"] = end.timestamp()
                
            response = await self.session.get(
                f"{self.prometheus_url}/api/v1/series",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            if result["status"] != "success":
                raise Exception(f"Series query failed: {result.get('error', 'Unknown error')}")
                
            return result["data"]
            
        except Exception as e:
            logger.error("Failed to get series", match=match, error=str(e))
            raise
    
    def format_query_result_to_dataframe(self, result: Dict[str, Any]) -> pd.DataFrame:
        """Convert Prometheus query result to pandas DataFrame.
        
        Args:
            result: Query result from Prometheus
            
        Returns:
            DataFrame with the results
        """
        if result["resultType"] == "matrix":
            data = []
            for series in result["result"]:
                metric = series["metric"]
                for timestamp, value in series["values"]:
                    row = {"timestamp": pd.to_datetime(timestamp, unit='s'), "value": float(value)}
                    row.update(metric)
                    data.append(row)
            return pd.DataFrame(data)
        
        elif result["resultType"] == "vector":
            data = []
            for series in result["result"]:
                metric = series["metric"]
                timestamp, value = series["value"]
                row = {"timestamp": pd.to_datetime(timestamp, unit='s'), "value": float(value)}
                row.update(metric)
                data.append(row)
            return pd.DataFrame(data)
        
        else:
            raise ValueError(f"Unsupported result type: {result['resultType']}")
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()
