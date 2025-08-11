"""
Metrics page for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import httpx
from src.ui.components.metrics_viewer import MetricsViewerComponent

def show_metrics_page():
    """Show the metrics exploration page."""
    st.set_page_config(
        page_title="Metrics Explorer - Prometheus Agent AI",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize API client
    if "api_client" not in st.session_state:
        st.session_state.api_client = httpx.AsyncClient(timeout=60.0)
    
    api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
    
    # Initialize metrics viewer component
    metrics_viewer = MetricsViewerComponent(
        st.session_state.api_client, 
        api_base_url
    )
    
    # Render the metrics explorer
    metrics_viewer.render_metrics_explorer()
    
    # Add sidebar information
    render_metrics_sidebar()

def render_metrics_sidebar():
    """Render metrics page sidebar with helpful information."""
    with st.sidebar:
        st.markdown("### 📊 Metrics Explorer")
        
        st.markdown("""
        **How to use:**
        1. Browse available metrics on the left
        2. Click ➕ to add metrics to your query
        3. Or write custom PromQL queries
        4. Execute and visualize results
        """)
        
        st.markdown("---")
        
        # PromQL help
        with st.expander("📚 PromQL Quick Reference"):
            st.markdown("""
            **Basic Queries:**
            ```
            up                    # Service status
            cpu_usage             # CPU usage
            memory_usage          # Memory usage
            ```
            
            **Functions:**
            ```
            rate(metric[5m])      # Per-second rate
            avg(metric)           # Average value
            sum(metric)           # Sum values
            max(metric)           # Maximum value
            ```
            
            **Time Ranges:**
            ```
            [5m]   # Last 5 minutes
            [1h]   # Last 1 hour
            [1d]   # Last 1 day
            ```
            
            **Operators:**
            ```
            +, -, *, /           # Arithmetic
            >, <, >=, <=, ==     # Comparison
            and, or, unless      # Logical
            ```
            """)
        
        # Common patterns
        with st.expander("🔍 Common Patterns"):
            st.markdown("""
            **CPU Usage:**
            ```
            100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
            ```
            
            **Memory Usage:**
            ```
            (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
            ```
            
            **HTTP Request Rate:**
            ```
            rate(http_requests_total[5m])
            ```
            
            **95th Percentile Response Time:**
            ```
            histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
            ```
            
            **Error Rate:**
            ```
            rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
            ```
            """)
        
        # Tips
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Use the search box to find specific metrics
        - Range queries work better for time series visualization
        - Large time ranges may take longer to load
        - Export data for further analysis
        """)

if __name__ == "__main__":
    show_metrics_page()
