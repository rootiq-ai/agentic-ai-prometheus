"""
OpenAI Client for AI-powered analysis and insights.
"""

import openai
from typing import List, Dict, Optional, Any
import json
import structlog
from datetime import datetime

logger = structlog.get_logger()

class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
    async def analyze_metrics(
        self,
        metrics_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Analyze metrics data and provide insights.
        
        Args:
            metrics_data: Prometheus metrics data
            context: Additional context about the metrics
            
        Returns:
            AI-generated analysis and insights
        """
        try:
            system_prompt = """You are a Prometheus monitoring expert and AI assistant. 
            Analyze the provided metrics data and provide actionable insights, anomaly detection, 
            and recommendations for system optimization. Focus on:
            
            1. Identifying anomalies or concerning trends
            2. Performance bottlenecks
            3. Resource utilization patterns
            4. Potential issues that might need attention
            5. Optimization recommendations
            
            Provide a structured response with clear sections for different types of insights."""
            
            user_prompt = f"""
            Please analyze the following Prometheus metrics data:
            
            {json.dumps(metrics_data, indent=2)}
            
            Additional context: {context if context else 'No additional context provided'}
            
            Provide a comprehensive analysis including:
            - Key findings and anomalies
            - Performance insights
            - Recommendations for improvement
            - Any urgent issues that need immediate attention
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Failed to analyze metrics", error=str(e))
            raise
    
    async def generate_promql_query(
        self,
        natural_language_query: str,
        available_metrics: List[str]
    ) -> str:
        """Generate PromQL query from natural language description.
        
        Args:
            natural_language_query: User's query in natural language
            available_metrics: List of available metric names
            
        Returns:
            Generated PromQL query
        """
        try:
            system_prompt = """You are a PromQL expert. Convert natural language queries 
            into valid PromQL expressions. Use the provided list of available metrics 
            and generate syntactically correct PromQL queries.
            
            Return only the PromQL query without additional explanation unless the query 
            cannot be generated, in which case explain why."""
            
            user_prompt = f"""
            Available metrics: {', '.join(available_metrics[:50])}  # Limit to avoid token overflow
            
            Natural language query: "{natural_language_query}"
            
            Generate a PromQL query for this request. Consider:
            - Common metric patterns (rate, histogram_quantile, etc.)
            - Appropriate time ranges and aggregations
            - Proper label filtering
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to generate PromQL query", error=str(e))
            raise
    
    async def explain_alert(
        self,
        alert_data: Dict[str, Any],
        metrics_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Explain an alert and provide troubleshooting guidance.
        
        Args:
            alert_data: Alert information from Prometheus
            metrics_context: Additional metrics context
            
        Returns:
            AI-generated explanation and troubleshooting steps
        """
        try:
            system_prompt = """You are a DevOps expert specializing in system monitoring 
            and incident response. Analyze the provided alert information and explain:
            
            1. What the alert means in plain language
            2. Potential root causes
            3. Immediate troubleshooting steps
            4. Long-term prevention strategies
            
            Be practical and actionable in your recommendations."""
            
            user_prompt = f"""
            Alert Information:
            {json.dumps(alert_data, indent=2)}
            
            Additional Metrics Context:
            {json.dumps(metrics_context, indent=2) if metrics_context else 'No additional metrics provided'}
            
            Please provide:
            1. Clear explanation of what this alert indicates
            2. Possible causes for this alert
            3. Step-by-step troubleshooting guide
            4. Prevention recommendations
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Failed to explain alert", error=str(e))
            raise
    
    async def suggest_monitoring_improvements(
        self,
        current_metrics: List[str],
        system_description: str
    ) -> str:
        """Suggest monitoring improvements based on current setup.
        
        Args:
            current_metrics: List of currently monitored metrics
            system_description: Description of the system being monitored
            
        Returns:
            AI-generated monitoring improvement suggestions
        """
        try:
            system_prompt = """You are a monitoring and observability expert. 
            Analyze the current monitoring setup and suggest improvements for better 
            observability, performance tracking, and incident detection."""
            
            user_prompt = f"""
            System Description: {system_description}
            
            Current Metrics Being Monitored:
            {chr(10).join(current_metrics[:100])}  # Limit to avoid token overflow
            
            Please suggest:
            1. Missing critical metrics that should be monitored
            2. Additional alerting rules that would be beneficial
            3. Monitoring best practices for this type of system
            4. Recommended dashboards and visualizations
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Failed to suggest monitoring improvements", error=str(e))
            raise
    
    async def chat_with_metrics(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_metrics_summary: Optional[str] = None
    ) -> str:
        """Have a conversational interaction about metrics and monitoring.
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            current_metrics_summary: Summary of current metrics state
            
        Returns:
            AI response to the user's message
        """
        try:
            system_prompt = f"""You are a helpful AI assistant specialized in Prometheus 
            monitoring and system observability. You can help users understand their metrics, 
            troubleshoot issues, and improve their monitoring setup.
            
            Current metrics summary: {current_metrics_summary if current_metrics_summary else 'No current metrics data available'}
            
            Be helpful, accurate, and provide actionable advice when possible."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Keep last 10 messages
                messages.append(msg)
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Failed to process chat message", error=str(e))
            raise
