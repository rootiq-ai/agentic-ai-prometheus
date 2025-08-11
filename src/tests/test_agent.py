"""
Tests for Prometheus Agent AI functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import pandas as pd

from src.core.agent import PrometheusAgent
from src.core.prometheus_client import PrometheusClient
from src.core.openai_client import OpenAIClient

class TestPrometheusAgent:
    """Test Prometheus Agent AI functionality."""
    
    @pytest.fixture
    def mock_prometheus_client(self):
        """Create mock Prometheus client."""
        client = Mock(spec=PrometheusClient)
        client.query = AsyncMock()
        client.query_range = AsyncMock()
        client.get_active_alerts = AsyncMock()
        client.get_metrics_metadata = AsyncMock()
        client.format_query_result_to_dataframe = Mock()
        return client
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        client = Mock(spec=OpenAIClient)
        client.analyze_metrics = AsyncMock()
        client.generate_promql_query = AsyncMock()
        client.explain_alert = AsyncMock()
        client.suggest_monitoring_improvements = AsyncMock()
        client.chat_with_metrics = AsyncMock()
        return client
    
    @pytest.fixture
    def agent(self, mock_prometheus_client, mock_openai_client):
        """Create Prometheus Agent instance."""
        return PrometheusAgent(mock_prometheus_client, mock_openai_client)
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_prometheus_client, mock_openai_client):
        """Test agent initialization."""
        agent = PrometheusAgent(mock_prometheus_client, mock_openai_client)
        
        assert agent.prometheus == mock_prometheus_client
        assert agent.openai == mock_openai_client
        assert agent.conversation_history == []
    
    @pytest.mark.asyncio
    async def test_analyze_system_health_success(self, agent, mock_prometheus_client, mock_openai_client):
        """Test successful system health analysis."""
        # Mock Prometheus responses
        mock_prometheus_client.query_range.return_value = {
            "result": [
                {
                    "metric": {"__name__": "up"},
                    "values": [[1609459200, "1"], [1609459260, "1"]]
                }
            ]
        }
        mock_prometheus_client.get_active_alerts.return_value = [
            {
                "labels": {"alertname": "TestAlert", "severity": "warning"},
                "annotations": {"summary": "Test alert"}
            }
        ]
        
        # Mock OpenAI response
        mock_openai_client.analyze_metrics.return_value = "System is healthy with 1 active alert."
        
        result = await agent.analyze_system_health(time_range_hours=1)
        
        assert result["status"] == "success"
        assert result["time_range_hours"] == 1
        assert "ai_analysis" in result
        assert result["active_alerts_count"] == 1
        assert "analysis_timestamp" in result
        
        # Verify calls were made
        assert mock_prometheus_client.query_range.called
        assert mock_prometheus_client.get_active_alerts.called
        assert mock_openai_client.analyze_metrics.called
    
    @pytest.mark.asyncio
    async def test_analyze_system_health_no_data(self, agent, mock_prometheus_client, mock_openai_client):
        """Test system health analysis with no data."""
        # Mock empty responses
        mock_prometheus_client.query_range.return_value = {"result": []}
        mock_prometheus_client.get_active_alerts.return_value = []
        mock_openai_client.analyze_metrics.return_value = "No data available for analysis."
        
        result = await agent.analyze_system_health(time_range_hours=1)
        
        assert result["status"] == "success"
        assert result["active_alerts_count"] == 0
        assert len(result["metrics_collected"]) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_system_health_error(self, agent, mock_prometheus_client, mock_openai_client):
        """Test system health analysis with error."""
        # Mock Prometheus error
        mock_prometheus_client.query_range.side_effect = Exception("Prometheus connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await agent.analyze_system_health(time_range_hours=1)
        
        assert "Prometheus connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_investigate_alert_found(self, agent, mock_prometheus_client, mock_openai_client):
        """Test alert investigation when alert is found."""
        # Mock active alerts
        mock_prometheus_client.get_active_alerts.return_value = [
            {
                "labels": {"alertname": "HighCPUUsage", "severity": "critical"},
                "annotations": {"summary": "CPU usage is high"},
                "state": "firing"
            }
        ]
        
        # Mock related metrics
        mock_prometheus_client.query.return_value = {
            "result": [{"metric": {"instance": "localhost"}, "value": [1609459200, "85"]}]
        }
        
        # Mock AI explanation
        mock_openai_client.explain_alert.return_value = "High CPU usage indicates system overload."
        
        result = await agent.investigate_alert("HighCPUUsage")
        
        assert result["status"] == "success"
        assert result["alert"]["labels"]["alertname"] == "HighCPUUsage"
        assert "ai_explanation" in result
        assert "related_metrics" in result
        assert "investigation_timestamp" in result
        
        mock_openai_client.explain_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_investigate_alert_not_found(self, agent, mock_prometheus_client, mock_openai_client):
        """Test alert investigation when alert is not found."""
        # Mock empty alerts
        mock_prometheus_client.get_active_alerts.return_value = []
        
        result = await agent.investigate_alert("NonexistentAlert")
        
        assert result["status"] == "not_found"
        assert "not found in active alerts" in result["message"]
        
        # Should not call OpenAI if alert not found
        mock_openai_client.explain_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_natural_language_query_success(self, agent, mock_prometheus_client, mock_openai_client):
        """Test successful natural language query processing."""
        # Mock metadata
        mock_prometheus_client.get_metrics_metadata.return_value = {
            "cpu_usage": {"type": "gauge"},
            "memory_usage": {"type": "gauge"}
        }
        
        # Mock PromQL generation
        mock_openai_client.generate_promql_query.return_value = "cpu_usage"
        
        # Mock query execution
        mock_prometheus_client.query.return_value = {
            "result": [{"metric": {"instance": "localhost"}, "value": [1609459200, "50"]}]
        }
        
        # Mock DataFrame conversion
        mock_df = pd.DataFrame({"timestamp": [datetime.now()], "value": [50.0]})
        mock_prometheus_client.format_query_result_to_dataframe.return_value = mock_df
        
        # Mock AI analysis
        mock_openai_client.analyze_metrics.return_value = "CPU usage is normal at 50%."
        
        result = await agent.natural_language_query("Show me CPU usage")
        
        assert result["status"] == "success"
        assert result["original_query"] == "Show me CPU usage"
        assert result["generated_promql"] == "cpu_usage"
        assert "ai_analysis" in result
        assert "results" in result
        
        mock_openai_client.generate_promql_query.assert_called_once()
        mock_prometheus_client.query.assert_called_once_with("cpu_usage")
    
    @pytest.mark.asyncio
    async def test_natural_language_query_no_results(self, agent, mock_prometheus_client, mock_openai_client):
        """Test natural language query with no results."""
        # Mock metadata
        mock_prometheus_client.get_metrics_metadata.return_value = {"cpu_usage": {"type": "gauge"}}
        
        # Mock PromQL generation
        mock_openai_client.generate_promql_query.return_value = "nonexistent_metric"
        
        # Mock empty query result
        mock_prometheus_client.query.return_value = {"result": []}
        
        result = await agent.natural_language_query("Show me nonexistent metric")
        
        assert result["status"] == "no_results"
        assert result["generated_promql"] == "nonexistent_metric"
        assert "no results" in result["message"]
    
    @pytest.mark.asyncio
    async def test_natural_language_query_execution_error(self, agent, mock_prometheus_client, mock_openai_client):
        """Test natural language query with execution error."""
        # Mock metadata
        mock_prometheus_client.get_metrics_metadata.return_value = {"cpu_usage": {"type": "gauge"}}
        
        # Mock PromQL generation
        mock_openai_client.generate_promql_query.return_value = "invalid_query("
        
        # Mock query execution error
        mock_prometheus_client.query.side_effect = Exception("Invalid PromQL syntax")
        
        result = await agent.natural_language_query("Show me invalid query")
        
        assert result["status"] == "query_error"
        assert result["generated_promql"] == "invalid_query("
        assert "Invalid PromQL syntax" in result["error"]
    
    @pytest.mark.asyncio
    async def test_chat_functionality(self, agent, mock_prometheus_client, mock_openai_client):
        """Test chat functionality."""
        # Mock system summary
        mock_prometheus_client.query.return_value = {
            "result": [{"metric": {}, "value": [1609459200, "1"]}]
        }
        mock_prometheus_client.get_active_alerts.return_value = []
        
        # Mock OpenAI chat response
        mock_openai_client.chat_with_metrics.return_value = "Hello! I can help you with monitoring."
        
        response = await agent.chat("Hello, can you help me?")
        
        assert "Hello!" in response
        assert "monitoring" in response
        
        # Check conversation history
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0]["role"] == "user"
        assert agent.conversation_history[0]["content"] == "Hello, can you help me?"
        assert agent.conversation_history[1]["role"] == "assistant"
        assert agent.conversation_history[1]["content"] == response
        
        mock_openai_client.chat_with_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_conversation_history_limit(self, agent, mock_prometheus_client, mock_openai_client):
        """Test chat conversation history limit."""
        # Fill conversation history beyond limit
        for i in range(25):  # More than the 20 limit
            agent.conversation_history.append({"role": "user", "content": f"Message {i}"})
            agent.conversation_history.append({"role": "assistant", "content": f"Response {i}"})
        
        # Mock dependencies
        mock_prometheus_client.query.return_value = {"result": []}
        mock_prometheus_client.get_active_alerts.return_value = []
        mock_openai_client.chat_with_metrics.return_value = "New response"
        
        await agent.chat("New message")
        
        # Should keep only last 20 messages
        assert len(agent.conversation_history) == 20
        assert agent.conversation_history[-2]["content"] == "New message"
        assert agent.conversation_history[-1]["content"] == "New response"
    
    @pytest.mark.asyncio
    async def test_get_monitoring_recommendations(self, agent, mock_prometheus_client, mock_openai_client):
        """Test getting monitoring recommendations."""
        # Mock metadata
        mock_prometheus_client.get_metrics_metadata.return_value = {
            "cpu_usage": {"type": "gauge"},
            "memory_usage": {"type": "gauge"}
        }
        
        # Mock OpenAI recommendations
        mock_openai_client.suggest_monitoring_improvements.return_value = (
            "Consider adding disk usage and network latency monitoring."
        )
        
        recommendations = await agent.get_monitoring_recommendations("Web application")
        
        assert "disk usage" in recommendations
        assert "network latency" in recommendations
        
        mock_openai_client.suggest_monitoring_improvements.assert_called_once_with(
            current_metrics=["cpu_usage", "memory_usage"],
            system_description="Web application"
        )
    
    @pytest.mark.asyncio
    async def test_get_related_metrics(self, agent, mock_prometheus_client):
        """Test getting related metrics for an alert."""
        alert = {
            "labels": {
                "alertname": "HighCPUUsage",
                "instance": "localhost:9090"
            }
        }
        
        # Mock query responses
        mock_prometheus_client.query.side_effect = [
            {"result": [{"metric": {}, "value": [1609459200, "1"]}]},  # up query
            {"result": [{"metric": {}, "value": [1609459200, "85"]}]},  # cpu_usage query
            {"result": []},  # memory_usage query (no results)
        ]
        
        related_metrics = await agent._get_related_metrics(alert)
        
        assert "up" in related_metrics
        assert "cpu_usage_percent" in related_metrics
        assert len(related_metrics) == 2  # Only successful queries
        
        # Should have made 3 query attempts
        assert mock_prometheus_client.query.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_current_system_summary(self, agent, mock_prometheus_client):
        """Test getting current system summary."""
        # Mock up query
        mock_prometheus_client.query.return_value = {
            "result": [
                {"metric": {}, "value": [1609459200, "1"]},
                {"metric": {}, "value": [1609459200, "1"]},
                {"metric": {}, "value": [1609459200, "0"]},  # One service down
            ]
        }
        
        # Mock alerts
        mock_prometheus_client.get_active_alerts.return_value = [
            {"labels": {"alertname": "ServiceDown"}}
        ]
        
        summary = await agent._get_current_system_summary()
        
        assert "2/3 services up" in summary
        assert "1 active alerts" in summary
        
        mock_prometheus_client.query.assert_called_once_with("up")
        mock_prometheus_client.get_active_alerts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_system_summary_error(self, agent, mock_prometheus_client):
        """Test system summary with error."""
        mock_prometheus_client.query.side_effect = Exception("Connection failed")
        
        summary = await agent._get_current_system_summary()
        
        assert summary == "System status unavailable"

class TestPrometheusAgentEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def agent(self):
        mock_prometheus = Mock(spec=PrometheusClient)
        mock_openai = Mock(spec=OpenAIClient)
        return PrometheusAgent(mock_prometheus, mock_openai)
    
    @pytest.mark.asyncio
    async def test_analyze_system_health_openai_error(self, agent):
        """Test system health analysis with OpenAI error."""
        # Mock Prometheus success
        agent.prometheus.query_range = AsyncMock(return_value={"result": []})
        agent.prometheus.get_active_alerts = AsyncMock(return_value=[])
        
        # Mock OpenAI failure
        agent.openai.analyze_metrics = AsyncMock(side_effect=Exception("OpenAI API error"))
        
        with pytest.raises(Exception) as exc_info:
            await agent.analyze_system_health(time_range_hours=1)
        
        assert "OpenAI API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_natural_language_query_metadata_error(self, agent):
        """Test natural language query with metadata error."""
        # Mock metadata error
        agent.prometheus.get_metrics_metadata = AsyncMock(side_effect=Exception("Metadata error"))
        
        with pytest.raises(Exception):
            await agent.natural_language_query("Show me CPU usage")
    
    @pytest.mark.asyncio
    async def test_chat_with_empty_message(self, agent):
        """Test chat with empty message."""
        agent.prometheus.query = AsyncMock(return_value={"result": []})
        agent.prometheus.get_active_alerts = AsyncMock(return_value=[])
        agent.openai.chat_with_metrics = AsyncMock(return_value="I need a message to respond to.")
        
        response = await agent.chat("")
        
        assert "message" in response
        
        # Should still add to conversation history
        assert len(agent.conversation_history) == 2
    
    @pytest.mark.asyncio
    async def test_investigate_alert_with_special_characters(self, agent):
        """Test alert investigation with special characters in alert name."""
        special_alert_name = "High-CPU_Usage@Server#1"
        
        agent.prometheus.get_active_alerts = AsyncMock(return_value=[
            {
                "labels": {"alertname": special_alert_name},
                "annotations": {"summary": "Special alert"}
            }
        ])
        
        agent.openai.explain_alert = AsyncMock(return_value="Alert explanation.")
        
        result = await agent.investigate_alert(special_alert_name)
        
        assert result["status"] == "success"
        assert result["alert"]["labels"]["alertname"] == special_alert_name

class TestPrometheusAgentIntegration:
    """Integration tests for Prometheus Agent."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_health_analysis(self):
        """Test complete health analysis workflow."""
        # This would be an integration test with real services
        # For now, we'll mock the entire workflow
        
        mock_prometheus = Mock(spec=PrometheusClient)
        mock_openai = Mock(spec=OpenAIClient)
        agent = PrometheusAgent(mock_prometheus, mock_openai)
        
        # Setup comprehensive mocks
        mock_prometheus.query_range.return_value = {
            "result": [{"metric": {"__name__": "up"}, "values": [[1609459200, "1"]]}]
        }
        mock_prometheus.get_active_alerts.return_value = []
        mock_openai.analyze_metrics.return_value = "System is healthy."
        
        result = await agent.analyze_system_health(time_range_hours=24)
        
        assert result["status"] == "success"
        assert result["time_range_hours"] == 24
        assert "System is healthy" in result["ai_analysis"]
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent agent operations."""
        mock_prometheus = Mock(spec=PrometheusClient)
        mock_openai = Mock(spec=OpenAIClient)
        agent = PrometheusAgent(mock_prometheus, mock_openai)
        
        # Setup mocks for different operations
        mock_prometheus.get_active_alerts.return_value = []
        mock_prometheus.query_range.return_value = {"result": []}
        mock_prometheus.get_metrics_metadata.return_value = {"up": {}}
        mock_prometheus.query.return_value = {"result": []}
        mock_prometheus.format_query_result_to_dataframe.return_value = pd.DataFrame()
        
        mock_openai.analyze_metrics.return_value = "Analysis complete."
        mock_openai.generate_promql_query.return_value = "up"
        mock_openai.chat_with_metrics.return_value = "Chat response."
        
        # Run multiple operations concurrently
        tasks = [
            agent.analyze_system_health(1),
            agent.natural_language_query("Show me status"),
            agent.chat("Hello")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete successfully
        assert len(results) == 3
        assert all(not isinstance(result, Exception) for result in results)
        
        # Check that each operation returned expected results
        health_result, nl_result, chat_result = results
        assert health_result["status"] == "success"
        assert nl_result["status"] == "success"
        assert chat_result == "Chat response."

class TestPrometheusAgentPerformance:
    """Performance tests for Prometheus Agent."""
    
    @pytest.mark.asyncio
    async def test_health_analysis_performance(self):
        """Test health analysis performance."""
        import time
        
        mock_prometheus = Mock(spec=PrometheusClient)
        mock_openai = Mock(spec=OpenAIClient)
        agent = PrometheusAgent(mock_prometheus, mock_openai)
        
        # Mock fast responses
        mock_prometheus.query_range.return_value = {"result": []}
        mock_prometheus.get_active_alerts.return_value = []
        mock_openai.analyze_metrics.return_value = "Quick analysis."
        
        start_time = time.time()
        await agent.analyze_system_health(time_range_hours=1)
        end_time = time.time()
        
        # Should complete quickly (mocked, so very fast)
        assert (end_time - start_time) < 1.0
    
    @pytest.mark.asyncio
    async def test_memory_usage_conversation_history(self):
        """Test memory usage with large conversation history."""
        mock_prometheus = Mock(spec=PrometheusClient)
        mock_openai = Mock(spec=OpenAIClient)
        agent = PrometheusAgent(mock_prometheus, mock_openai)
        
        # Mock responses
        mock_prometheus.query.return_value = {"result": []}
        mock_prometheus.get_active_alerts.return_value = []
        mock_openai.chat_with_metrics.return_value = "Response"
        
        # Add many messages to conversation history
        initial_history_length = len(agent.conversation_history)
        
        for i in range(50):
            await agent.chat(f"Message {i}")
        
        # Should maintain reasonable history size
        assert len(agent.conversation_history) <= 20
        assert len(agent.conversation_history) > initial_history_length
