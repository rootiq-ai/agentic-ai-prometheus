"""
Tests for Prometheus client functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import httpx
import pandas as pd

from src.core.prometheus_client import PrometheusClient

class TestPrometheusClient:
    """Test Prometheus client functionality."""
    
    @pytest.fixture
    def prometheus_client(self):
        """Create a Prometheus client instance for testing."""
        return PrometheusClient("http://localhost:9090")
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "up", "instance": "localhost:9090"},
                        "value": [1609459200, "1"]
                    }
                ]
            }
        }
        return mock_resp
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = PrometheusClient("http://localhost:9090")
        assert client.prometheus_url == "http://localhost:9090"
        assert client.client is not None
        assert client.session is not None
    
    def test_client_initialization_trailing_slash(self):
        """Test client initialization with trailing slash."""
        client = PrometheusClient("http://localhost:9090/")
        assert client.prometheus_url == "http://localhost:9090"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, prometheus_client):
        """Test successful health check."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.is_healthy()
            assert result is True
            mock_get.assert_called_once_with("http://localhost:9090/-/healthy")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, prometheus_client):
        """Test failed health check."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 500
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.is_healthy()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, prometheus_client):
        """Test health check with network exception."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")
            
            result = await prometheus_client.is_healthy()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_query_success(self, prometheus_client, mock_response):
        """Test successful query execution."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_get.return_value = mock_response
            
            result = await prometheus_client.query("up")
            
            assert result["resultType"] == "vector"
            assert len(result["result"]) == 1
            assert result["result"][0]["metric"]["__name__"] == "up"
            
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "query" in call_args[1]["params"]
            assert call_args[1]["params"]["query"] == "up"
    
    @pytest.mark.asyncio
    async def test_query_with_time(self, prometheus_client, mock_response):
        """Test query with specific timestamp."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_get.return_value = mock_response
            
            query_time = datetime.now()
            result = await prometheus_client.query("up", time=query_time)
            
            assert result["resultType"] == "vector"
            
            call_args = mock_get.call_args
            assert "time" in call_args[1]["params"]
            assert call_args[1]["params"]["time"] == query_time.timestamp()
    
    @pytest.mark.asyncio
    async def test_query_failure(self, prometheus_client):
        """Test query failure handling."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "error",
                "error": "Invalid query"
            }
            mock_get.return_value = mock_resp
            
            with pytest.raises(Exception) as exc_info:
                await prometheus_client.query("invalid_query")
            
            assert "Invalid query" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_http_error(self, prometheus_client):
        """Test query with HTTP error."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 400
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=mock_resp
            )
            mock_get.return_value = mock_resp
            
            with pytest.raises(Exception):
                await prometheus_client.query("up")
    
    @pytest.mark.asyncio
    async def test_range_query_success(self, prometheus_client):
        """Test successful range query."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {
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
                }
            }
            mock_get.return_value = mock_resp
            
            start = datetime.now() - timedelta(hours=1)
            end = datetime.now()
            
            result = await prometheus_client.query_range("cpu_usage", start, end, "1m")
            
            assert result["resultType"] == "matrix"
            assert len(result["result"]) == 1
            assert len(result["result"][0]["values"]) == 2
            
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["query"] == "cpu_usage"
            assert params["step"] == "1m"
            assert "start" in params
            assert "end" in params
    
    @pytest.mark.asyncio
    async def test_get_metrics_metadata(self, prometheus_client):
        """Test getting metrics metadata."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {
                    "up": [{"type": "gauge", "help": "Service availability"}],
                    "cpu_usage": [{"type": "gauge", "help": "CPU usage percentage"}]
                }
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_metrics_metadata()
            
            assert "up" in result
            assert "cpu_usage" in result
            mock_get.assert_called_once_with("http://localhost:9090/api/v1/metadata")
    
    @pytest.mark.asyncio
    async def test_get_label_names(self, prometheus_client):
        """Test getting label names."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": ["__name__", "instance", "job"]
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_label_names()
            
            assert result == ["__name__", "instance", "job"]
            mock_get.assert_called_once_with("http://localhost:9090/api/v1/labels")
    
    @pytest.mark.asyncio
    async def test_get_label_values(self, prometheus_client):
        """Test getting label values."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": ["localhost:9090", "localhost:9100"]
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_label_values("instance")
            
            assert result == ["localhost:9090", "localhost:9100"]
            mock_get.assert_called_once_with("http://localhost:9090/api/v1/label/instance/values")
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, prometheus_client):
        """Test getting active alerts."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {
                    "alerts": [
                        {
                            "labels": {"alertname": "HighCPUUsage", "severity": "warning"},
                            "annotations": {"summary": "High CPU usage"},
                            "state": "firing"
                        }
                    ]
                }
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_active_alerts()
            
            assert len(result) == 1
            assert result[0]["labels"]["alertname"] == "HighCPUUsage"
            mock_get.assert_called_once_with("http://localhost:9090/api/v1/alerts")
    
    @pytest.mark.asyncio
    async def test_get_alerting_rules(self, prometheus_client):
        """Test getting alerting rules."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {
                    "groups": [
                        {
                            "name": "example",
                            "rules": [
                                {
                                    "name": "HighCPUUsage",
                                    "type": "alerting",
                                    "query": "cpu_usage > 80",
                                    "duration": "5m"
                                },
                                {
                                    "name": "RecordingRule",
                                    "type": "recording",
                                    "query": "sum(cpu_usage)"
                                }
                            ]
                        }
                    ]
                }
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_alerting_rules()
            
            # Should only return alerting rules, not recording rules
            assert len(result) == 1
            assert result[0]["name"] == "HighCPUUsage"
            assert result[0]["type"] == "alerting"
    
    @pytest.mark.asyncio
    async def test_get_series(self, prometheus_client):
        """Test getting series metadata."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": [
                    {"__name__": "up", "instance": "localhost:9090"},
                    {"__name__": "up", "instance": "localhost:9100"}
                ]
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.get_series(["up"])
            
            assert len(result) == 2
            assert all("__name__" in series for series in result)
            
            call_args = mock_get.call_args
            assert "match[]" in call_args[1]["params"]
            assert call_args[1]["params"]["match[]"] == ["up"]
    
    @pytest.mark.asyncio
    async def test_get_series_with_time_range(self, prometheus_client):
        """Test getting series with time range."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"status": "success", "data": []}
            mock_get.return_value = mock_resp
            
            start = datetime.now() - timedelta(hours=1)
            end = datetime.now()
            
            await prometheus_client.get_series(["up"], start=start, end=end)
            
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert "start" in params
            assert "end" in params
            assert params["start"] == start.timestamp()
            assert params["end"] == end.timestamp()
    
    def test_format_query_result_to_dataframe_vector(self, prometheus_client):
        """Test formatting vector query result to DataFrame."""
        result = {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [1609459200, "1"]
                },
                {
                    "metric": {"__name__": "up", "instance": "localhost:9100"},
                    "value": [1609459200, "0"]
                }
            ]
        }
        
        df = prometheus_client.format_query_result_to_dataframe(result)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "value" in df.columns
        assert "__name__" in df.columns
        assert "instance" in df.columns
        assert df["value"].iloc[0] == 1.0
        assert df["value"].iloc[1] == 0.0
    
    def test_format_query_result_to_dataframe_matrix(self, prometheus_client):
        """Test formatting matrix query result to DataFrame."""
        result = {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": "cpu_usage", "instance": "localhost:9090"},
                    "values": [
                        [1609459200, "50.0"],
                        [1609459260, "51.0"]
                    ]
                }
            ]
        }
        
        df = prometheus_client.format_query_result_to_dataframe(result)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "value" in df.columns
        assert "__name__" in df.columns
        assert "instance" in df.columns
        assert df["value"].iloc[0] == 50.0
        assert df["value"].iloc[1] == 51.0
    
    def test_format_query_result_unsupported_type(self, prometheus_client):
        """Test formatting unsupported result type."""
        result = {
            "resultType": "scalar",
            "result": [1609459200, "42"]
        }
        
        with pytest.raises(ValueError) as exc_info:
            prometheus_client.format_query_result_to_dataframe(result)
        
        assert "Unsupported result type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_close_session(self, prometheus_client):
        """Test closing the HTTP session."""
        with patch.object(prometheus_client.session, 'aclose') as mock_close:
            await prometheus_client.close()
            mock_close.assert_called_once()

class TestPrometheusClientEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def prometheus_client(self):
        return PrometheusClient("http://localhost:9090")
    
    @pytest.mark.asyncio
    async def test_network_timeout(self, prometheus_client):
        """Test handling of network timeouts."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            
            with pytest.raises(Exception):
                await prometheus_client.query("up")
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, prometheus_client):
        """Test handling of invalid JSON responses."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = ValueError("Invalid JSON")
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            
            with pytest.raises(Exception):
                await prometheus_client.query("up")
    
    @pytest.mark.asyncio
    async def test_empty_query_result(self, prometheus_client):
        """Test handling of empty query results."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": []
                }
            }
            mock_get.return_value = mock_resp
            
            result = await prometheus_client.query("nonexistent_metric")
            
            assert result["resultType"] == "vector"
            assert result["result"] == []
    
    def test_format_empty_result_to_dataframe(self, prometheus_client):
        """Test formatting empty result to DataFrame."""
        result = {
            "resultType": "vector",
            "result": []
        }
        
        df = prometheus_client.format_query_result_to_dataframe(result)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

class TestPrometheusClientIntegration:
    """Integration tests for Prometheus client."""
    
    @pytest.mark.asyncio
    async def test_full_query_workflow(self):
        """Test complete query workflow."""
        # This would be an integration test that requires a real Prometheus instance
        # For now, we'll skip it or mock the entire workflow
        pytest.skip("Integration test requires real Prometheus instance")
    
    @pytest.mark.asyncio 
    async def test_concurrent_queries(self, prometheus_client):
        """Test concurrent query execution."""
        with patch.object(prometheus_client.session, 'get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "status": "success",
                "data": {"resultType": "vector", "result": []}
            }
            mock_get.return_value = mock_resp
            
            # Execute multiple queries concurrently
            queries = ["up", "cpu_usage", "memory_usage"]
            tasks = [prometheus_client.query(query) for query in queries]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result["resultType"] == "vector" for result in results)
            assert mock_get.call_count == 3

class TestPrometheusClientPerformance:
    """Performance tests for Prometheus client."""
    
    @pytest.mark.asyncio
    async def test_query_response_time(self, prometheus_client):
        """Test query response time is reasonable."""
        import time
        
        with patch.object(prometheus_client.session, 'get') as mock_get:
            # Simulate slow response
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "status": "success",
                    "data": {"resultType": "vector", "result": []}
                }
                return mock_resp
            
            mock_get.side_effect = slow_response
            
            start_time = time.time()
            await prometheus_client.query("up")
            end_time = time.time()
            
            # Should include the mocked delay plus processing time
            assert (end_time - start_time) >= 0.1
            assert (end_time - start_time) < 0.5  # But not too slow
