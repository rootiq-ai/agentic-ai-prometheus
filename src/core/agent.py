"""
Prometheus Agent AI - Core agent that combines Prometheus monitoring with AI analysis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
import pandas as pd

from .prometheus_client import PrometheusClient
from .openai_client import OpenAIClient

logger = structlog.get_logger()

class PrometheusAgent:
    """AI-powered Prometheus monitoring agent."""
    
    def __init__(self, prometheus_client: PrometheusClient, openai_client: OpenAIClient):
        """Initialize the Prometheus Agent.
        
        Args:
            prometheus_client: Prometheus client instance
            openai_client: OpenAI client instance
        """
        self.prometheus = prometheus_client
        self.openai = openai_client
        self.conversation_history = []
        
    async def analyze_system_health(self, time_range_hours: int = 1) -> Dict[str, Any]:
        """Perform a comprehensive system health analysis.
        
        Args:
            time_range_hours: Hours of historical data to analyze
            
        Returns:
            System health analysis results
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Collect key system metrics
            metrics_to_analyze = [
                "up",  # Service availability
                "cpu_usage_percent",
                "memory_usage_percent", 
                "disk_usage_percent",
                "http_requests_total",
                "http_request_duration_seconds",
                "process_resident_memory_bytes",
                "go_memstats_alloc_bytes"
            ]
            
            collected_data = {}
            
            for metric in metrics_to_analyze:
                try:
                    # Try to get the metric data
                    result = await self.prometheus.query_range(
                        query=metric,
                        start=start_time,
                        end=end_time,
                        step="1m"
                    )
                    if result["result"]:
                        collected_data[metric] = result
                except Exception as e:
                    logger.warning(f"Could not collect metric {metric}", error=str(e))
                    continue
            
            # Get active alerts
            active_alerts = await self.prometheus.get_active_alerts()
            
            # Prepare data for AI analysis
            analysis_data = {
                "metrics": collected_data,
                "alerts": active_alerts,
                "time_range": f"{time_range_hours} hours",
                "analysis_timestamp": end_time.isoformat()
            }
            
            # Get AI analysis
            ai_analysis = await self.openai.analyze_metrics(
                metrics_data=analysis_data,
                context=f"System health analysis for the last {time_range_hours} hours"
            )
            
            return {
                "status": "success",
                "analysis_timestamp": end_time.isoformat(),
                "time_range_hours": time_range_hours,
                "metrics_collected": list(collected_data.keys()),
                "active_alerts_count": len(active_alerts),
                "ai_analysis": ai_analysis,
                "raw_data": {
                    "metrics": collected_data,
                    "alerts": active_alerts
                }
            }
            
        except Exception as e:
            logger.error("System health analysis failed", error=str(e))
            raise
    
    async def investigate_alert(self, alert_name: str) -> Dict[str, Any]:
        """Investigate a specific alert and provide detailed analysis.
        
        Args:
            alert_name: Name of the alert to investigate
            
        Returns:
            Alert investigation results
        """
        try:
            # Get current alerts
            active_alerts = await self.prometheus.get_active_alerts()
            
            # Find the specific alert
            target_alert = None
            for alert in active_alerts:
                if alert.get("labels", {}).get("alertname") == alert_name:
                    target_alert = alert
                    break
            
            if not target_alert:
                return {
                    "status": "not_found",
                    "message": f"Alert '{alert_name}' not found in active alerts"
                }
            
            # Get related metrics based on alert labels
            related_metrics = await self._get_related_metrics(target_alert)
            
            # Get AI explanation
            explanation = await self.openai.explain_alert(
                alert_data=target_alert,
                metrics_context=related_metrics
            )
            
            return {
                "status": "success",
                "alert": target_alert,
                "related_metrics": related_metrics,
                "ai_explanation": explanation,
                "investigation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Alert investigation failed", alert_name=alert_name, error=str(e))
            raise
    
    async def natural_language_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query and return results.
        
        Args:
            query: Natural language query about metrics
            
        Returns:
            Query results and analysis
        """
        try:
            # Get available metrics
            metadata = await self.prometheus.get_metrics_metadata()
            available_metrics = list(metadata.keys()) if isinstance(metadata, dict) else []
            
            # Generate PromQL query
            promql_query = await self.openai.generate_promql_query(
                natural_language_query=query,
                available_metrics=available_metrics
            )
            
            # Execute the generated query
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=1)  # Default 1 hour range
                
                if "rate(" in promql_query or "increase(" in promql_query:
                    # Range query for rate/increase functions
                    result = await self.prometheus.query_range(
                        query=promql_query,
                        start=start_time,
                        end=end_time,
                        step="1m"
                    )
                else:
                    # Instant query for current values
                    result = await self.prometheus.query(promql_query)
                
                # Convert to DataFrame for easier analysis
                if result["result"]:
                    df = self.prometheus.format_query_result_to_dataframe(result)
                    
                    # Get AI analysis of the results
                    analysis = await self.openai.analyze_metrics(
                        metrics_data={"query_result": result, "dataframe_summary": df.describe().to_dict()},
                        context=f"Results for natural language query: '{query}'"
                    )
                    
                    return {
                        "status": "success",
                        "original_query": query,
                        "generated_promql": promql_query,
                        "results": result,
                        "dataframe": df.to_dict(),
                        "ai_analysis": analysis
                    }
                else:
                    return {
                        "status": "no_results",
                        "original_query": query,
                        "generated_promql": promql_query,
                        "message": "Query executed successfully but returned no results"
                    }
                    
            except Exception as query_error:
                return {
                    "status": "query_error",
                    "original_query": query,
                    "generated_promql": promql_query,
                    "error": str(query_error),
                    "message": "Generated PromQL query failed to execute"
                }
                
        except Exception as e:
            logger.error("Natural language query processing failed", query=query, error=str(e))
            raise
    
    async def chat(self, user_message: str) -> str:
        """Have a conversational interaction with the agent.
        
        Args:
            user_message: User's message
            
        Returns:
            Agent's response
        """
        try:
            # Get current system summary
            current_summary = await self._get_current_system_summary()
            
            # Process chat message
            response = await self.openai.chat_with_metrics(
                user_message=user_message,
                conversation_history=self.conversation_history,
                current_metrics_summary=current_summary
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return response
            
        except Exception as e:
            logger.error("Chat processing failed", error=str(e))
            raise
    
    async def get_monitoring_recommendations(self, system_description: str = "") -> str:
        """Get AI-powered monitoring recommendations.
        
        Args:
            system_description: Description of the system being monitored
            
        Returns:
            Monitoring recommendations
        """
        try:
            # Get current metrics
            metadata = await self.prometheus.get_metrics_metadata()
            current_metrics = list(metadata.keys()) if isinstance(metadata, dict) else []
            
            recommendations = await self.openai.suggest_monitoring_improvements(
                current_metrics=current_metrics,
                system_description=system_description or "Generic system monitoring setup"
            )
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to get monitoring recommendations", error=str(e))
            raise
    
    async def _get_related_metrics(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics related to an alert for additional context.
        
        Args:
            alert: Alert information
            
        Returns:
            Related metrics data
        """
        try:
            related_metrics = {}
            labels = alert.get("labels", {})
            
            # Common related metrics based on alert type
            if "instance" in labels:
                instance = labels["instance"]
                
                # Get basic instance metrics
                basic_queries = [
                    f'up{{instance="{instance}"}}',
                    f'cpu_usage_percent{{instance="{instance}"}}',
                    f'memory_usage_percent{{instance="{instance}"}}'
                ]
                
                for query in basic_queries:
                    try:
                        result = await self.prometheus.query(query)
                        if result["result"]:
                            metric_name = query.split("{")[0]
                            related_metrics[metric_name] = result
                    except:
                        continue
            
            return related_metrics
            
        except Exception as e:
            logger.warning("Failed to get related metrics", error=str(e))
            return {}
    
    async def _get_current_system_summary(self) -> str:
        """Get a brief summary of current system state.
        
        Returns:
            System summary string
        """
        try:
            # Get basic system info
            up_query_result = await self.prometheus.query("up")
            active_alerts = await self.prometheus.get_active_alerts()
            
            total_services = len(up_query_result.get("result", []))
            up_services = len([r for r in up_query_result.get("result", []) if float(r["value"][1]) == 1])
            alert_count = len(active_alerts)
            
            summary = f"System Status: {up_services}/{total_services} services up, {alert_count} active alerts"
            return summary
            
        except Exception as e:
            logger.warning("Failed to get system summary", error=str(e))
            return "System status unavailable"
