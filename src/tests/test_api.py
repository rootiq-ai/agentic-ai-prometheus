"""
Tests for Prometheus Agent AI API endpoints.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.api.main import app
from src.core.prometheus_client import PrometheusClient
from src.core.openai_client import OpenAIClient
from src.core.agent import PrometheusAgent

# Test client
client = TestClient(app)

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "prometheus_connected" in data
        assert "openai_connected" in data
        assert "agent_ready" in data

class TestMetricsEndpoints:
    """Test metrics-related endpoints."""
    
    @patch('src.api.main.get_prometheus_client')
    def test_execute_query_success(self, mock_get_client):
        """Test successful PromQL query execution."""
        # Mock Prometheus client
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(return_value={
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [1609459200, "1"]
                }
            ]
        })
        mock_get_client.return_value = mock_client
        
        # Test query
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "query" in data
        assert data["query"] == "up"
    
    @patch('src.api.main.get_prometheus_client')
    def test_execute_query_invalid(self, mock_get_client):
        """Test invalid PromQL query."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(side_effect=Exception("Invalid query"))
        mock_get_client.return_value = mock_client
        
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "invalid_query("}
        )
        
        assert response.status_code == 500
    
    @patch('src.api.main.get_prometheus_client')
    def test_range_query(self, mock_get_client):
        """Test range query execution."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query_range = AsyncMock(return_value={
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": "cpu_usage"},
                    "values": [
                        [1609459200, "50.0"],
                        [1609459260, "51.0"]
                    ]
                }
            ]
        })
        mock_client.format_query_result_to_dataframe = Mock(return_value=Mock())
        mock_get_client.return_value = mock_client
        
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        response = client.post(
            "/api/v1/metrics/query_range",
            json={
                "query": "cpu_usage",
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "step": "1m"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "metadata" in data
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_metrics_metadata(self, mock_get_client):
        """Test getting metrics metadata."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.get_metrics_metadata = AsyncMock(return_value={
            "up": {"type": "gauge", "help": "Service availability"},
            "cpu_usage": {"type": "gauge", "help": "CPU usage percentage"}
        })
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/metrics/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "up" in data["metadata"]
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_label_names(self, mock_get_client):
        """Test getting label names."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.get_label_names = AsyncMock(return_value=["__name__", "instance", "job"])
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/metrics/labels")
        
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "count" in data
        assert isinstance(data["labels"], list)
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_label_values(self, mock_get_client):
        """Test getting label values."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.get_label_values = AsyncMock(return_value=["localhost:9090", "localhost:9100"])
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/metrics/labels/instance/values")
        
        assert response.status_code == 200
        data = response.json()
        assert "values" in data
        assert "label" in data
        assert data["label"] == "instance"

class TestAlertsEndpoints:
    """Test alerts-related endpoints."""
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_active_alerts(self, mock_get_client):
        """Test getting active alerts."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.get_active_alerts = AsyncMock(return_value=[
            {
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity": "warning",
                    "instance": "localhost:9090"
                },
                "annotations": {
                    "summary": "High CPU usage detected",
                    "description": "CPU usage is above 80%"
                },
                "state": "firing",
                "activeAt": "2024-01-01T12:00:00Z"
            }
        ])
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/alerts/active")
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "count" in data
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["labels"]["alertname"] == "HighCPUUsage"
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_alerting_rules(self, mock_get_client):
        """Test getting alerting rules."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.get_alerting_rules = AsyncMock(return_value=[
            {
                "name": "HighCPUUsage",
                "query": "cpu_usage > 80",
                "duration": "5m",
                "labels": {"severity": "warning"},
                "annotations": {"summary": "High CPU usage"}
            }
        ])
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/alerts/rules")
        
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "count" in data
    
    @patch('src.api.main.get_prometheus_client')
    def test_get_alerts_summary(self, mock_get_client):
        """Test getting alerts summary."""
        mock_client = Mock(spec=PrometheusClient)
        
        # Mock active alerts
        mock_client.get_active_alerts = AsyncMock(return_value=[
            {"labels": {"severity": "critical", "alertname": "ServiceDown"}},
            {"labels": {"severity": "warning", "alertname": "HighCPU"}},
            {"labels": {"severity": "warning", "alertname": "HighMemory"}}
        ])
        
        # Mock alerting rules
        mock_client.get_alerting_rules = AsyncMock(return_value=[
            {"name": "ServiceDown"},
            {"name": "HighCPU"},
            {"name": "HighMemory"}
        ])
        
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/alerts/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_active_alerts" in data
        assert "severity_breakdown" in data
        assert "most_common_alerts" in data
        assert data["total_active_alerts"] == 3
        assert data["severity_breakdown"]["critical"] == 1
        assert data["severity_breakdown"]["warning"] == 2

class TestAnalysisEndpoints:
    """Test AI analysis endpoints."""
    
    @patch('src.api.main.get_agent')
    def test_system_health_analysis(self, mock_get_agent):
        """Test system health analysis."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.analyze_system_health = AsyncMock(return_value={
            "status": "success",
            "analysis_timestamp": datetime.now().isoformat(),
            "time_range_hours": 1,
            "metrics_collected": ["up", "cpu_usage"],
            "active_alerts_count": 2,
            "ai_analysis": "System is experiencing moderate load with 2 active alerts.",
            "raw_data": {}
        })
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/health",
            json={"time_range_hours": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "ai_analysis" in data
        assert data["time_range_hours"] == 1
    
    @patch('src.api.main.get_agent')
    def test_natural_language_query(self, mock_get_agent):
        """Test natural language query processing."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.natural_language_query = AsyncMock(return_value={
            "status": "success",
            "original_query": "Show me CPU usage",
            "generated_promql": "cpu_usage",
            "results": {"result": []},
            "ai_analysis": "CPU usage is currently normal."
        })
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/natural-language",
            json={"query": "Show me CPU usage"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["original_query"] == "Show me CPU usage"
        assert "generated_promql" in data
    
    @patch('src.api.main.get_agent')
    def test_chat_with_agent(self, mock_get_agent):
        """Test chat functionality."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.chat = AsyncMock(return_value="Hello! I can help you with your Prometheus metrics.")
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/chat",
            json={"message": "Hello, can you help me?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "Hello!" in data["response"]
    
    @patch('src.api.main.get_agent')
    def test_investigate_alert(self, mock_get_agent):
        """Test alert investigation."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.investigate_alert = AsyncMock(return_value={
            "status": "success",
            "alert": {"labels": {"alertname": "HighCPUUsage"}},
            "related_metrics": {},
            "ai_explanation": "This alert indicates high CPU usage.",
            "investigation_timestamp": datetime.now().isoformat()
        })
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/investigate-alert",
            json={"alert_name": "HighCPUUsage"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "ai_explanation" in data
    
    @patch('src.api.main.get_agent')
    def test_get_monitoring_recommendations(self, mock_get_agent):
        """Test monitoring recommendations."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.get_monitoring_recommendations = AsyncMock(
            return_value="Consider adding alerts for disk usage and network latency."
        )
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/recommendations",
            json={"system_description": "Web application with database"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "disk usage" in data["recommendations"]

class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request."""
        response = client.post(
            "/api/v1/metrics/query",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        response = client.post(
            "/api/v1/metrics/query",
            json={}  # Missing required 'query' field
        )
        
        assert response.status_code == 422
    
    @patch('src.api.main.get_prometheus_client')
    def test_prometheus_connection_error(self, mock_get_client):
        """Test handling of Prometheus connection errors."""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(side_effect=ConnectionError("Connection failed"))
        mock_get_client.return_value = mock_client
        
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"}
        )
        
        assert response.status_code == 500
    
    @patch('src.api.main.get_agent')
    def test_openai_api_error(self, mock_get_agent):
        """Test handling of OpenAI API errors."""
        mock_agent = Mock(spec=PrometheusAgent)
        mock_agent.chat = AsyncMock(side_effect=Exception("OpenAI API error"))
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/v1/analysis/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 500

class TestRequestValidation:
    """Test request validation."""
    
    def test_query_validation(self):
        """Test PromQL query validation."""
        # Empty query
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": ""}
        )
        assert response.status_code == 422
        
        # Valid query
        with patch('src.api.main.get_prometheus_client') as mock_get_client:
            mock_client = Mock(spec=PrometheusClient)
            mock_client.query = AsyncMock(return_value={"resultType": "vector", "result": []})
            mock_get_client.return_value = mock_client
            
            response = client.post(
                "/api/v1/metrics/query",
                json={"query": "up"}
            )
            assert response.status_code == 200
    
    def test_time_range_validation(self):
        """Test time range validation for range queries."""
        start_time = datetime.now()
        end_time = start_time - timedelta(hours=1)  # End before start (invalid)
        
        response = client.post(
            "/api/v1/metrics/query_range",
            json={
                "query": "up",
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "step": "1m"
            }
        )
        
        assert response.status_code == 422
    
    def test_health_analysis_validation(self):
        """Test health analysis request validation."""
        # Invalid time range (too large)
        response = client.post(
            "/api/v1/analysis/health",
            json={"time_range_hours": 999}
        )
        assert response.status_code == 422
        
        # Valid request
        with patch('src.api.main.get_agent') as mock_get_agent:
            mock_agent = Mock(spec=PrometheusAgent)
            mock_agent.analyze_system_health = AsyncMock(return_value={"status": "success"})
            mock_get_agent.return_value = mock_agent
            
            response = client.post(
                "/api/v1/analysis/health",
                json={"time_range_hours": 24}
            )
            assert response.status_code == 200

# Async test helpers
@pytest.mark.asyncio
async def test_async_operations():
    """Test async operations work correctly."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200

# Integration test setup
@pytest.fixture
def test_app():
    """Create test app instance."""
    return app

@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)

# Performance tests
class TestPerformance:
    """Test API performance characteristics."""
    
    def test_health_check_performance(self):
        """Test health check response time."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    @patch('src.api.main.get_prometheus_client')
    def test_concurrent_requests(self, mock_get_client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(return_value={"resultType": "vector", "result": []})
        mock_get_client.return_value = mock_client
        
        results = []
        
        def make_request():
            response = client.post("/api/v1/metrics/query", json={"query": "up"})
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Verify all requests succeeded
        assert all(status == 200 for status in results)
        assert len(results) == 10
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
