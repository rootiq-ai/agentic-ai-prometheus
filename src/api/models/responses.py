"""
Pydantic response models for Prometheus Agent AI API.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class ResponseStatus(str, Enum):
    """Response status options."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"

class AnalysisType(str, Enum):
    """Analysis type options."""
    HEALTH = "health"
    ANOMALY = "anomaly"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"

# === Base Response Models ===

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    status: ResponseStatus = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class ErrorResponse(BaseResponse):
    """Error response model."""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

class SuccessResponse(BaseResponse):
    """Success response model."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

# === Health Check Response ===

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status")
    prometheus_connected: bool = Field(..., description="Prometheus connection status")
    openai_connected: bool = Field(..., description="OpenAI connection status")
    agent_ready: bool = Field(..., description="Agent readiness status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    version: str = Field("1.0.0", description="Service version")

# === Metrics Response Models ===

class PrometheusDataPoint(BaseModel):
    """Single Prometheus data point."""
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[float, str] = Field(..., description="Data point value")

class PrometheusMetric(BaseModel):
    """Prometheus metric with metadata."""
    metric: Dict[str, str] = Field(..., description="Metric labels")
    values: Optional[List[PrometheusDataPoint]] = Field(None, description="Time series values")
    value: Optional[PrometheusDataPoint] = Field(None, description="Single value for instant queries")

class QueryResponse(BaseResponse):
    """Prometheus query response."""
    result_type: str = Field(..., description="Result type (vector, matrix, scalar)")
    result: List[PrometheusMetric] = Field(..., description="Query results")
    query: str = Field(..., description="Original query")
    execution_time_ms: Optional[float] = Field(None, description="Query execution time")

class RangeQueryResponse(QueryResponse):
    """Prometheus range query response."""
    start: datetime = Field(..., description="Query start time")
    end: datetime = Field(..., description="Query end time")
    step: str = Field(..., description="Query step")
    data_points: int = Field(..., description="Total number of data points")

class MetricsMetadataResponse(BaseResponse):
    """Metrics metadata response."""
    metadata: Dict[str, Dict[str, Any]] = Field(..., description="Metrics metadata")
    total_metrics: int = Field(..., description="Total number of metrics")

class LabelsResponse(BaseResponse):
    """Labels response."""
    labels: List[str] = Field(..., description="List of label names")
    count: int = Field(..., description="Number of labels")

class LabelValuesResponse(BaseResponse):
    """Label values response."""
    label: str = Field(..., description="Label name")
    values: List[str] = Field(..., description="List of label values")
    count: int = Field(..., description="Number of values")

class SeriesResponse(BaseResponse):
    """Series response."""
    series: List[Dict[str, str]] = Field(..., description="List of series metadata")
    count: int = Field(..., description="Number of series")

# === Alert Response Models ===

class AlertResponse(BaseModel):
    """Single alert response."""
    labels: Dict[str, str] = Field(..., description="Alert labels")
    annotations: Dict[str, str] = Field(..., description="Alert annotations")
    state: str = Field(..., description="Alert state")
    active_at: Optional[datetime] = Field(None, description="Alert activation time")
    value: Optional[str] = Field(None, description="Alert value")

class ActiveAlertsResponse(BaseResponse):
    """Active alerts response."""
    alerts: List[AlertResponse] = Field(..., description="List of active alerts")
    count: int = Field(..., description="Number of active alerts")

class AlertingRulesResponse(BaseResponse):
    """Alerting rules response."""
    rules: List[Dict[str, Any]] = Field(..., description="List of alerting rules")
    count: int = Field(..., description="Number of rules")

class AlertsSummaryResponse(BaseResponse):
    """Alerts summary response."""
    total_active_alerts: int = Field(..., description="Total number of active alerts")
    total_alerting_rules: int = Field(..., description="Total number of alerting rules")
    severity_breakdown: Dict[str, int] = Field(..., description="Alerts by severity")
    state_breakdown: Dict[str, int] = Field(..., description="Alerts by state")
    most_common_alerts: List[tuple] = Field(..., description="Most common alert names")

# === Analysis Response Models ===

class HealthAnalysisResponse(BaseResponse):
    """System health analysis response."""
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")
    time_range_hours: int = Field(..., description="Analysis time range")
    metrics_collected: List[str] = Field(..., description="Metrics analyzed")
    active_alerts_count: int = Field(..., description="Number of active alerts")
    ai_analysis: str = Field(..., description="AI-generated analysis")
    health_score: Optional[float] = Field(None, description="Overall health score (0-100)")
    anomalies_detected: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw analysis data")

class NaturalLanguageQueryResponse(BaseResponse):
    """Natural language query response."""
    original_query: str = Field(..., description="Original natural language query")
    generated_promql: str = Field(..., description="Generated PromQL query")
    results: Optional[Dict[str, Any]] = Field(None, description="Query results")
    dataframe: Optional[Dict[str, Any]] = Field(None, description="Results as DataFrame")
    ai_analysis: Optional[str] = Field(None, description="AI analysis of results")
    confidence_score: Optional[float] = Field(None, description="Query generation confidence")
    alternative_queries: List[str] = Field(default_factory=list, description="Alternative PromQL queries")

class ChatResponse(BaseResponse):
    """Chat response."""
    response: str = Field(..., description="AI response to the user's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    context_used: bool = Field(..., description="Whether metrics context was used")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")

class AlertInvestigationResponse(BaseResponse):
    """Alert investigation response."""
    alert: Dict[str, Any] = Field(..., description="Alert details")
    related_metrics: Dict[str, Any] = Field(..., description="Related metrics data")
    ai_explanation: str = Field(..., description="AI explanation of the alert")
    investigation_timestamp: datetime = Field(..., description="Investigation timestamp")
    severity_assessment: Optional[str] = Field(None, description="AI severity assessment")
    root_cause_analysis: Optional[str] = Field(None, description="Potential root causes")
    remediation_steps: List[str] = Field(default_factory=list, description="Suggested remediation steps")

class RecommendationsResponse(BaseResponse):
    """Monitoring recommendations response."""
    recommendations: str = Field(..., description="AI-generated recommendations")
    priority: str = Field("medium", description="Recommendations priority level")
    implementation_complexity: str = Field("medium", description="Implementation difficulty")
    categories: List[str] = Field(default_factory=list, description="Recommendation categories")

class AnomalyDetectionResponse(BaseResponse):
    """Anomaly detection response."""
    metric: str = Field(..., description="Analyzed metric")
    anomalies_found: bool = Field(..., description="Whether anomalies were detected")
    anomaly_periods: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomaly periods")
    total_anomalies: int = Field(..., description="Total number of anomalies")
    analysis_summary: str = Field(..., description="AI analysis summary")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

# === Dashboard Response Models ===

class DashboardResponse(BaseResponse):
    """Dashboard response."""
    id: str = Field(..., description="Dashboard ID")
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    queries: List[str] = Field(..., description="Dashboard queries")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class DashboardListResponse(BaseResponse):
    """Dashboard list response."""
    dashboards: List[DashboardResponse] = Field(..., description="List of dashboards")
    total: int = Field(..., description="Total number of dashboards")

# === Bulk Operations Response ===

class BulkQueryResult(BaseModel):
    """Single bulk query result."""
    query: str = Field(..., description="Original query")
    status: ResponseStatus = Field(..., description="Query status")
    result: Optional[Dict[str, Any]] = Field(None, description="Query result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: Optional[float] = Field(None, description="Execution time")

class BulkQueryResponse(BaseResponse):
    """Bulk query response."""
    results: List[BulkQueryResult] = Field(..., description="Results for all queries")
    total_queries: int = Field(..., description="Total number of queries")
    successful_queries: int = Field(..., description="Number of successful queries")
    failed_queries: int = Field(..., description="Number of failed queries")
    total_execution_time_ms: float = Field(..., description="Total execution time")

# === Configuration Response ===

class ConfigurationResponse(BaseResponse):
    """Configuration response."""
    prometheus_url: str = Field(..., description="Current Prometheus URL")
    openai_model: str = Field(..., description="Current OpenAI model")
    max_conversation_history: int = Field(..., description="Max conversation history")
    default_time_range_hours: int = Field(..., description="Default time range")
    api_version: str = Field(..., description="API version")

# === Export Response ===

class ExportResponse(BaseResponse):
    """Export response."""
    download_url: str = Field(..., description="Download URL for exported data")
    format: str = Field(..., description="Export format")
    file_size_bytes: int = Field(..., description="File size in bytes")
    expires_at: datetime = Field(..., description="Download link expiration")

# === Statistics Response ===

class UsageStatisticsResponse(BaseResponse):
    """Usage statistics response."""
    total_queries: int = Field(..., description="Total queries executed")
    total_chat_messages: int = Field(..., description="Total chat messages")
    avg_response_time_ms: float = Field(..., description="Average response time")
    most_used_metrics: List[str] = Field(..., description="Most queried metrics")
    uptime_hours: float = Field(..., description="Service uptime in hours")

# === WebSocket Response Models ===

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")

class StreamingQueryResponse(BaseModel):
    """Streaming query response."""
    query_id: str = Field(..., description="Query ID")
    status: str = Field(..., description="Query status")
    progress: float = Field(..., description="Query progress (0-1)")
    partial_results: Optional[Dict[str, Any]] = Field(None, description="Partial results")
    completed: bool = Field(..., description="Whether query is completed")
