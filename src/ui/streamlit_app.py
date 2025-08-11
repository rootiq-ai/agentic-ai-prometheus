"""
Prometheus Agent AI - Streamlit UI Application
"""

import streamlit as st
import httpx
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="Prometheus Agent AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class PrometheusAgentUI:
    """UI class for Prometheus Agent AI."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def make_api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """Make API request to the FastAPI backend."""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            st.error(f"API request failed: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return {"error": str(e)}

# Initialize UI
ui = PrometheusAgentUI()

def main():
    """Main Streamlit application."""
    
    # Title and header
    st.title("🤖 Prometheus Agent AI")
    st.markdown("### AI-Powered Monitoring and Analysis")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Chat with Agent", "Natural Language Queries", "System Health", "Alert Investigation", "Monitoring Recommendations"]
    )
    
    # Health check
    with st.sidebar:
        st.markdown("---")
        if st.button("🔍 Check System Health"):
            health_status = asyncio.run(ui.make_api_request("/health"))
            if "error" not in health_status:
                st.success("✅ System Healthy")
                with st.expander("Health Details"):
                    st.json(health_status)
            else:
                st.error("❌ System Unhealthy")
                st.error(health_status.get("error", "Unknown error"))
    
    # Route to different pages
    if page == "Dashboard":
        show_dashboard()
    elif page == "Chat with Agent":
        show_chat_interface()
    elif page == "Natural Language Queries":
        show_natural_language_queries()
    elif page == "System Health":
        show_system_health()
    elif page == "Alert Investigation":
        show_alert_investigation()
    elif page == "Monitoring Recommendations":
        show_monitoring_recommendations()

def show_dashboard():
    """Show the main dashboard."""
    st.header("📊 Monitoring Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("System Status", "Monitoring", "📈")
    
    with col2:
        st.metric("Active Alerts", "Loading...", "⚠️")
    
    with col3:
        st.metric("Services Up", "Loading...", "🟢")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Analyze System Health"):
            with st.spinner("Analyzing system health..."):
                result = asyncio.run(ui.make_api_request("/api/v1/analysis/health", "POST", {"time_range_hours": 1}))
                if "error" not in result:
                    st.success("Analysis complete!")
                    st.json(result)
                else:
                    st.error(f"Analysis failed: {result['error']}")
    
    with col2:
        if st.button("📋 Get Active Alerts"):
            with st.spinner("Fetching alerts..."):
                result = asyncio.run(ui.make_api_request("/api/v1/alerts/active"))
                if "error" not in result:
                    st.write(f"Found {len(result.get('alerts', []))} active alerts")
                    if result.get('alerts'):
                        df = pd.DataFrame(result['alerts'])
                        st.dataframe(df)
                else:
                    st.error(f"Failed to fetch alerts: {result['error']}")
    
    with col3:
        if st.button("📊 View Metrics"):
            st.info("Use the Natural Language Queries page to explore metrics")
    
    with col4:
        if st.button("🤖 Chat with AI"):
            st.info("Use the Chat with Agent page to interact with the AI")

def show_chat_interface():
    """Show the chat interface."""
    st.header("💬 Chat with Prometheus Agent AI")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**Agent:** {message['content']}")
    
    # Chat input
    user_input = st.text_input("Ask the agent about your metrics:", key="chat_input")
    
    if st.button("Send") and user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Get AI response
        with st.spinner("Agent is thinking..."):
            response_data = asyncio.run(
                ui.make_api_request("/api/v1/analysis/chat", "POST", {"message": user_input})
            )
            
            if "error" not in response_data:
                agent_response = response_data.get("response", "Sorry, I couldn't process your request.")
                st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
                st.rerun()
            else:
                st.error(f"Chat failed: {response_data['error']}")
    
    # Clear chat history
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def show_natural_language_queries():
    """Show natural language query interface."""
    st.header("🔍 Natural Language Queries")
    st.markdown("Ask questions about your metrics in plain English!")
    
    # Example queries
    st.subheader("Example Queries")
    examples = [
        "Show me CPU usage for the last hour",
        "What's the average response time of my web service?",
        "How much memory is my application using?",
        "Show me the error rate for HTTP requests",
        "What's the disk usage on my servers?"
    ]
    
    example_cols = st.columns(len(examples))
    for i, example in enumerate(examples):
        with example_cols[i]:
            if st.button(f"📝 {example[:20]}...", key=f"example_{i}"):
                st.session_state.query_input = example
    
    # Query input
    query = st.text_area(
        "Enter your query:",
        value=st.session_state.get("query_input", ""),
        height=100,
        key="nl_query"
    )
    
    if st.button("🚀 Execute Query") and query:
        with st.spinner("Processing your query..."):
            result = asyncio.run(
                ui.make_api_request("/api/v1/analysis/natural-language", "POST", {"query": query})
            )
            
            if "error" not in result and result.get("status") == "success":
                st.success("Query executed successfully!")
                
                # Show generated PromQL
                st.subheader("Generated PromQL Query")
                st.code(result.get("generated_promql", ""), language="promql")
                
                # Show AI analysis
                if result.get("ai_analysis"):
                    st.subheader("AI Analysis")
                    st.markdown(result["ai_analysis"])
                
                # Show results if available
                if result.get("results") and result["results"].get("result"):
                    st.subheader("Query Results")
                    
                    # Convert to DataFrame for display
                    try:
                        df_data = result.get("dataframe", {})
                        if df_data:
                            df = pd.DataFrame(df_data)
                            st.dataframe(df)
                            
                            # Create visualization if numeric data
                            numeric_columns = df.select_dtypes(include=['number']).columns
                            if len(numeric_columns) > 0 and 'timestamp' in df.columns:
                                fig = px.line(df, x='timestamp', y=numeric_columns[0], 
                                            title=f"Time Series: {numeric_columns[0]}")
                                st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not create visualization: {str(e)}")
                        st.json(result["results"])
                
            else:
                st.error(f"Query failed: {result.get('error', 'Unknown error')}")
                if result.get("generated_promql"):
                    st.subheader("Generated PromQL (for debugging)")
                    st.code(result["generated_promql"], language="promql")

def show_system_health():
    """Show system health analysis."""
    st.header("🏥 System Health Analysis")
    
    # Time range selector
    time_range = st.selectbox(
        "Select time range for analysis:",
        [1, 2, 6, 12, 24],
        format_func=lambda x: f"{x} hour{'s' if x > 1 else ''}"
    )
    
    if st.button("🔍 Analyze System Health"):
        with st.spinner(f"Analyzing system health for the last {time_range} hour(s)..."):
            result = asyncio.run(
                ui.make_api_request(
                    "/api/v1/analysis/health", 
                    "POST", 
                    {"time_range_hours": time_range}
                )
            )
            
            if "error" not in result and result.get("status") == "success":
                st.success("✅ Health analysis complete!")
                
                # Show summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Metrics Collected", 
                        len(result.get("metrics_collected", []))
                    )
                
                with col2:
                    st.metric(
                        "Active Alerts", 
                        result.get("active_alerts_count", 0)
                    )
                
                with col3:
                    st.metric(
                        "Analysis Time", 
                        f"{time_range}h"
                    )
                
                # Show AI analysis
                st.subheader("🤖 AI Analysis")
                st.markdown(result.get("ai_analysis", "No analysis available"))
                
                # Show raw data in expandable section
                with st.expander("📊 Raw Data"):
                    st.json(result.get("raw_data", {}))
                
            else:
                st.error(f"Health analysis failed: {result.get('error', 'Unknown error')}")

def show_alert_investigation():
    """Show alert investigation interface."""
    st.header("🚨 Alert Investigation")
    
    # Get active alerts first
    if st.button("🔄 Refresh Active Alerts"):
        with st.spinner("Fetching active alerts..."):
            alerts_result = asyncio.run(ui.make_api_request("/api/v1/alerts/active"))
            if "error" not in alerts_result:
                st.session_state.active_alerts = alerts_result.get("alerts", [])
            else:
                st.error(f"Failed to fetch alerts: {alerts_result['error']}")
    
    # Show active alerts
    if hasattr(st.session_state, 'active_alerts') and st.session_state.active_alerts:
        st.subheader("Active Alerts")
        
        alert_names = [alert.get("labels", {}).get("alertname", "Unknown") 
                      for alert in st.session_state.active_alerts]
        
        selected_alert = st.selectbox("Select an alert to investigate:", alert_names)
        
        if st.button("🔍 Investigate Alert") and selected_alert:
            with st.spinner(f"Investigating alert: {selected_alert}..."):
                investigation_result = asyncio.run(
                    ui.make_api_request(
                        "/api/v1/analysis/investigate-alert", 
                        "POST", 
                        {"alert_name": selected_alert}
                    )
                )
                
                if "error" not in investigation_result and investigation_result.get("status") == "success":
                    st.success("🕵️ Investigation complete!")
                    
                    # Show alert details
                    st.subheader("Alert Details")
                    alert_info = investigation_result.get("alert", {})
                    st.json(alert_info)
                    
                    # Show AI explanation
                    st.subheader("🤖 AI Explanation")
                    st.markdown(investigation_result.get("ai_explanation", "No explanation available"))
                    
                    # Show related metrics
                    if investigation_result.get("related_metrics"):
                        with st.expander("📊 Related Metrics"):
                            st.json(investigation_result["related_metrics"])
                
                else:
                    st.error(f"Investigation failed: {investigation_result.get('error', 'Unknown error')}")
    
    else:
        st.info("No active alerts found. Click 'Refresh Active Alerts' to check for alerts.")

def show_monitoring_recommendations():
    """Show monitoring recommendations."""
    st.header("💡 Monitoring Recommendations")
    
    # System description input
    system_description = st.text_area(
        "Describe your system (optional):",
        placeholder="e.g., Microservices architecture with Node.js APIs, PostgreSQL database, Redis cache...",
        height=100
    )
    
    if st.button("🎯 Get Recommendations"):
        with st.spinner("Generating monitoring recommendations..."):
            result = asyncio.run(
                ui.make_api_request(
                    "/api/v1/analysis/recommendations", 
                    "POST", 
                    {"system_description": system_description}
                )
            )
            
            if "error" not in result:
                st.success("✅ Recommendations generated!")
                st.markdown(result.get("recommendations", "No recommendations available"))
            else:
                st.error(f"Failed to generate recommendations: {result['error']}")
    
    # Show general best practices
    with st.expander("📚 General Monitoring Best Practices"):
        st.markdown("""
        ### Key Metrics to Monitor:
        - **Application Performance**: Response time, throughput, error rates
        - **Infrastructure**: CPU, memory, disk, network usage
        - **Business Metrics**: User activity, revenue-impacting events
        - **Security**: Failed login attempts, unauthorized access
        
        ### Alert Best Practices:
        - Set meaningful thresholds based on historical data
        - Avoid alert fatigue with proper escalation
        - Include runbooks for common alerts
        - Monitor alert effectiveness and adjust as needed
        
        ### Dashboard Design:
        - Focus on actionable metrics
        - Use consistent time ranges
        - Group related metrics together
        - Include both technical and business metrics
        """)

if __name__ == "__main__":
    main()
