"""
Home page for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_home_page(api_client: httpx.AsyncClient, api_base_url: str) -> None:
    """Render the home page.
    
    Args:
        api_client: HTTP client for API calls
        api_base_url: Base URL for the API
    """
    # Hero section
    render_hero_section()
    
    # Quick status overview
    render_status_overview(api_client, api_base_url)
    
    # Quick actions
    render_quick_actions()
    
    # Recent activity summary
    render_recent_activity(api_client, api_base_url)
    
    # Getting started guide
    render_getting_started()

def render_hero_section() -> None:
    """Render the hero section with welcome message."""
    st.markdown("""
    # 🤖 Welcome to Prometheus Agent AI
    
    Your intelligent monitoring companion that combines the power of Prometheus metrics 
    with AI-driven insights and natural language interactions.
    """)
    
    # Key features
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 💬 AI Chat
        Ask questions about your metrics in plain English
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Smart Analysis
        Get intelligent insights and anomaly detection
        """)
    
    with col3:
        st.markdown("""
        ### 🚨 Alert Intelligence
        AI-powered alert investigation and remediation
        """)
    
    with col4:
        st.markdown("""
        ### 📈 Visual Explorer
        Interactive metrics exploration and visualization
        """)

def render_status_overview(api_client: httpx.AsyncClient, api_base_url: str) -> None:
    """Render system status overview.
    
    Args:
        api_client: HTTP client for API calls
        api_base_url: Base URL for the API
    """
    st.markdown("---")
    st.subheader("📊 System Status Overview")
    
    try:
        # Get system health
        health_data = asyncio.run(get_system_health(api_client, api_base_url))
        
        if health_data:
            render_health_metrics(health_data)
        else:
            st.warning("Unable to fetch system status. Please check if the API is running.")
            
    except Exception as e:
        st.error(f"Failed to load system status: {str(e)}")

def render_health_metrics(health_data: Dict[str, Any]) -> None:
    """Render health metrics cards.
    
    Args:
        health_data: Health data from API
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # API Status
        if health_data.get("prometheus_connected", False):
            st.success("🟢 **Prometheus**\nConnected")
        else:
            st.error("🔴 **Prometheus**\nDisconnected")
    
    with col2:
        # OpenAI Status
        if health_data.get("openai_connected", False):
            st.success("🟢 **OpenAI**\nConnected")
        else:
            st.error("🔴 **OpenAI**\nDisconnected")
    
    with col3:
        # Agent Status
        if health_data.get("agent_ready", False):
            st.success("🟢 **AI Agent**\nReady")
        else:
            st.error("🔴 **AI Agent**\nNot Ready")
    
    with col4:
        # Overall Health
        all_healthy = all([
            health_data.get("prometheus_connected", False),
            health_data.get("openai_connected", False),
            health_data.get("agent_ready", False)
        ])
        
        if all_healthy:
            st.success("🟢 **Overall**\nHealthy")
        else:
            st.warning("🟡 **Overall**\nPartial")

def render_quick_actions() -> None:
    """Render quick action buttons."""
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💬 Start Chat", use_container_width=True, type="primary"):
            st.switch_page("Chat with Agent")
    
    with col2:
        if st.button("📊 Explore Metrics", use_container_width=True):
            st.switch_page("Metrics")
    
    with col3:
        if st.button("🚨 View Alerts", use_container_width=True):
            st.switch_page("Alerts")
    
    with col4:
        if st.button("🔍 System Health", use_container_width=True):
            # Trigger health analysis
            st.info("Redirecting to System Health analysis...")

def render_recent_activity(api_client: httpx.AsyncClient, api_base_url: str) -> None:
    """Render recent activity section.
    
    Args:
        api_client: HTTP client for API calls
        api_base_url: Base URL for the API
    """
    st.markdown("---")
    st.subheader("📈 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚨 Recent Alerts")
        try:
            alerts = asyncio.run(get_recent_alerts(api_client, api_base_url))
            
            if alerts:
                for alert in alerts[:3]:  # Show last 3 alerts
                    labels = alert.get('labels', {})
                    severity = labels.get('severity', 'unknown')
                    alertname = labels.get('alertname', 'Unknown Alert')
                    
                    # Color code by severity
                    if severity == 'critical':
                        st.error(f"🔴 **{alertname}** ({severity})")
                    elif severity == 'warning':
                        st.warning(f"🟡 **{alertname}** ({severity})")
                    else:
                        st.info(f"🔵 **{alertname}** ({severity})")
                
                if len(alerts) > 3:
                    st.caption(f"... and {len(alerts) - 3} more alerts")
            else:
                st.success("🎉 No recent alerts - all systems running smoothly!")
                
        except Exception as e:
            st.warning("Could not fetch recent alerts")
    
    with col2:
        st.markdown("#### 📊 Popular Metrics")
        
        # Show popular/common metrics
        popular_metrics = [
            "up - Service availability",
            "cpu_usage_percent - CPU utilization", 
            "memory_usage_percent - Memory usage",
            "http_requests_total - HTTP request count",
            "response_time - Request duration"
        ]
        
        for metric in popular_metrics:
            st.text(f"• {metric}")

def render_getting_started() -> None:
    """Render getting started guide."""
    st.markdown("---")
    st.subheader("🎯 Getting Started")
    
    with st.expander("👋 New to Prometheus Agent AI?", expanded=False):
        st.markdown("""
        ### 🚀 Quick Start Guide
        
        **1. Chat with the AI Agent**
        - Ask questions in plain English: *"Show me CPU usage for the last hour"*
        - Get explanations: *"What does this alert mean?"*
        - Request analysis: *"Analyze my system health"*
        
        **2. Explore Your Metrics**
        - Browse available metrics in the Metrics page
        - Execute custom PromQL queries
        - Visualize time series data
        
        **3. Monitor Alerts**
        - View active alerts and their status
        - Get AI-powered alert explanations
        - Learn about potential root causes
        
        **4. System Health Analysis**
        - Get comprehensive health reports
        - Identify performance bottlenecks
        - Receive optimization recommendations
        
        ### 💡 Tips for Better Results
        
        - **Be specific**: Instead of "show metrics", try "show CPU usage for web servers"
        - **Include time ranges**: "...over the last 2 hours" or "...since yesterday"
        - **Ask follow-ups**: The AI remembers context within your conversation
        - **Use natural language**: No need to learn PromQL - just ask naturally!
        
        ### 🔧 Common Commands to Try
        
        ```
        "What's my system health status?"
        "Show me memory usage trends"
        "Are there any critical alerts?"
        "Explain the HighCPUUsage alert"
        "What metrics should I monitor for my API?"
        ```
        """)
    
    # System requirements and links
    with st.expander("📚 Documentation & Resources", expanded=False):
        st.markdown("""
        ### 📖 Documentation
        - **API Documentation**: `/api/docs` - Interactive API documentation
        - **Prometheus Docs**: [Official Prometheus Documentation](https://prometheus.io/docs/)
        - **PromQL Guide**: [Prometheus Query Language Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
        
        ### 🔗 Quick Links
        - **Prometheus UI**: [http://localhost:9090](http://localhost:9090) (if running locally)
        - **Alertmanager**: [http://localhost:9093](http://localhost:9093) (if running locally)
        - **API Health**: [/health](/health) - Check service health
        
        ### ⚙️ Configuration
        - Prometheus URL: Check your `.env` file for `PROMETHEUS_URL`
        - OpenAI API: Ensure `OPENAI_API_KEY` is set correctly
        - Time zones: All times are displayed in your local timezone
        """)

async def get_system_health(api_client: httpx.AsyncClient, api_base_url: str) -> Dict[str, Any]:
    """Get system health status.
    
    Args:
        api_client: HTTP client
        api_base_url: API base URL
        
    Returns:
        Health status data
    """
    try:
        response = await api_client.get(f"{api_base_url}/health", timeout=10.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
            
    except Exception:
        return {}

async def get_recent_alerts(api_client: httpx.AsyncClient, api_base_url: str) -> list:
    """Get recent alerts.
    
    Args:
        api_client: HTTP client
        api_base_url: API base URL
        
    Returns:
        List of recent alerts
    """
    try:
        response = await api_client.get(f"{api_base_url}/api/v1/alerts/active", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('alerts', [])
        else:
            return []
            
    except Exception:
        return []

def render_footer() -> None:
    """Render page footer."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🤖 Prometheus Agent AI**")
        st.caption("AI-powered monitoring and analysis")
    
    with col2:
        st.markdown("**📊 System Info**")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col3:
        st.markdown("**🔗 Links**")
        st.caption("[Documentation](/) | [API Docs](/api/docs) | [Health Check](/health)")

# Render the home page
def show_home_page():
    """Main function to show the home page."""
    # Get API client from session state or create new one
    if "api_client" not in st.session_state:
        st.session_state.api_client = httpx.AsyncClient(timeout=30.0)
    
    api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
    
    render_home_page(st.session_state.api_client, api_base_url)
    render_footer()
