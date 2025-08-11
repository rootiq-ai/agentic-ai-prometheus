"""
Alerts page for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import httpx
import asyncio
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Any

def show_alerts_page():
    """Show the alerts management page."""
    st.set_page_config(
        page_title="Alerts - Prometheus Agent AI",
        page_icon="🚨",
        layout="wide"
    )
    
    # Initialize API client
    if "api_client" not in st.session_state:
        st.session_state.api_client = httpx.AsyncClient(timeout=60.0)
    
    api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
    
    st.title("🚨 Alert Management")
    
    # Alert overview
    render_alert_overview(st.session_state.api_client, api_base_url)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Active Alerts", "📋 Alert Rules", "📊 Alert History", "🔍 Investigation"])
    
    with tab1:
        render_active_alerts_tab(st.session_state.api_client, api_base_url)
    
    with tab2:
        render_alert_rules_tab(st.session_state.api_client, api_base_url)
    
    with tab3:
        render_alert_history_tab(st.session_state.api_client, api_base_url)
    
    with tab4:
        render_investigation_tab(st.session_state.api_client, api_base_url)
    
    # Sidebar
    render_alerts_sidebar()

def render_alert_overview(api_client: httpx.AsyncClient, api_base_url: str):
    """Render alert overview metrics."""
    try:
        # Get alert summary
        summary = asyncio.run(get_alert_summary(api_client, api_base_url))
        
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_alerts = summary.get('total_active_alerts', 0)
                st.metric(
                    "🚨 Active Alerts", 
                    total_alerts,
                    delta=f"+{total_alerts}" if total_alerts > 0 else "0",
                    delta_color="inverse" if total_alerts > 0 else "normal"
                )
            
            with col2:
                critical_count = summary.get('severity_breakdown', {}).get('critical', 0)
                st.metric(
                    "🔴 Critical", 
                    critical_count,
                    delta=f"+{critical_count}" if critical_count > 0 else "0",
                    delta_color="inverse" if critical_count > 0 else "normal"
                )
            
            with col3:
                warning_count = summary.get('severity_breakdown', {}).get('warning', 0)
                st.metric(
                    "🟡 Warning", 
                    warning_count,
                    delta=f"+{warning_count}" if warning_count > 0 else "0",
                    delta_color="inverse" if warning_count > 0 else "normal"
                )
            
            with col4:
                total_rules = summary.get('total_alerting_rules', 0)
                st.metric("📋 Alert Rules", total_rules)
            
            # Alert trend visualization
            if summary.get('severity_breakdown'):
                severity_data = summary['severity_breakdown']
                if any(severity_data.values()):
                    fig = px.pie(
                        values=list(severity_data.values()),
                        names=list(severity_data.keys()),
                        title="Alert Distribution by Severity",
                        color_discrete_map={
                            'critical': '#FF6B6B',
                            'warning': '#FFD93D',
                            'info': '#6BCF7F'
                        }
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Unable to fetch alert summary")
            
    except Exception as e:
        st.error(f"Failed to load alert overview: {str(e)}")

def render_active_alerts_tab(api_client: httpx.AsyncClient, api_base_url: str):
    """Render active alerts tab."""
    st.subheader("🔥 Currently Active Alerts")
    
    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Alerts", key="refresh_active"):
            st.rerun()
    
    try:
        alerts = asyncio.run(get_active_alerts(api_client, api_base_url))
        
        if not alerts:
            st.success("🎉 No active alerts! All systems are running normally.")
            return
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severities = list(set(alert.get('labels', {}).get('severity', 'unknown') for alert in alerts))
            selected_severity = st.selectbox("Filter by Severity:", ["All"] + severities)
        
        with col2:
            instances = list(set(alert.get('labels', {}).get('instance', 'unknown') for alert in alerts))
            selected_instance = st.selectbox("Filter by Instance:", ["All"] + instances)
        
        with col3:
            sort_by = st.selectbox("Sort by:", ["Severity", "Alert Name", "Time"])
        
        # Filter alerts
        filtered_alerts = filter_alerts(alerts, selected_severity, selected_instance)
        filtered_alerts = sort_alerts(filtered_alerts, sort_by)
        
        # Display alerts
        for i, alert in enumerate(filtered_alerts):
            render_alert_card(alert, i, api_client, api_base_url)
            
    except Exception as e:
        st.error(f"Failed to load active alerts: {str(e)}")

def render_alert_card(alert: Dict[str, Any], index: int, api_client: httpx.AsyncClient, api_base_url: str):
    """Render a single alert card."""
    labels = alert.get('labels', {})
    annotations = alert.get('annotations', {})
    
    # Determine alert styling based on severity
    severity = labels.get('severity', 'unknown')
    if severity == 'critical':
        alert_color = "🔴"
        border_color = "#FF6B6B"
    elif severity == 'warning':
        alert_color = "🟡" 
        border_color = "#FFD93D"
    else:
        alert_color = "🔵"
        border_color = "#6BCF7F"
    
    # Create expandable alert card
    alertname = labels.get('alertname', 'Unknown Alert')
    summary = annotations.get('summary', 'No summary available')
    
    with st.expander(f"{alert_color} **{alertname}** - {summary[:100]}{'...' if len(summary) > 100 else ''}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Alert details
            st.markdown(f"**Alert Name:** {alertname}")
            st.markdown(f"**Severity:** {severity.title()}")
            st.markdown(f"**Instance:** {labels.get('instance', 'N/A')}")
            st.markdown(f"**Job:** {labels.get('job', 'N/A')}")
            st.markdown(f"**State:** {alert.get('state', 'unknown')}")
            
            if 'active_at' in alert and alert['active_at']:
                active_time = alert['active_at']
                st.markdown(f"**Active Since:** {active_time}")
            
            # Description
            description = annotations.get('description', 'No description available')
            st.markdown(f"**Description:** {description}")
            
            # Labels
            if labels:
                st.markdown("**Labels:**")
                for key, value in labels.items():
                    st.code(f"{key}: {value}")
        
        with col2:
            # Action buttons
            st.markdown("**Actions:**")
            
            if st.button(f"🔍 Investigate", key=f"investigate_{index}"):
                investigate_alert(alertname, api_client, api_base_url)
            
            if st.button(f"📊 View Metrics", key=f"metrics_{index}"):
                st.info(f"Would show related metrics for {alertname}")
            
            if st.button(f"📝 Add Note", key=f"note_{index}"):
                st.info("Note functionality would be implemented here")
            
            # Runbook link if available
            runbook = annotations.get('runbook_url')
            if runbook:
                st.markdown(f"[📖 Runbook]({runbook})")

def render_alert_rules_tab(api_client: httpx.AsyncClient, api_base_url: str):
    """Render alert rules tab."""
    st.subheader("📋 Alert Rules Configuration")
    
    try:
        rules = asyncio.run(get_alert_rules(api_client, api_base_url))
        
        if not rules:
            st.info("No alert rules found.")
            return
        
        # Search and filter
        search_term = st.text_input("🔍 Search rules:", placeholder="Enter rule name or expression")
        
        # Display rules
        for i, rule in enumerate(rules):
            if search_term and search_term.lower() not in rule.get('name', '').lower():
                continue
                
            with st.expander(f"📏 **{rule.get('name', 'Unnamed Rule')}**"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Rule Name:** {rule.get('name', 'N/A')}")
                    st.markdown(f"**Expression:**")
                    st.code(rule.get('query', 'No expression'), language='promql')
                    
                    duration = rule.get('duration', 'N/A')
                    st.markdown(f"**Duration:** {duration}")
                    
                    labels = rule.get('labels', {})
                    if labels:
                        st.markdown("**Labels:**")
                        for key, value in labels.items():
                            st.code(f"{key}: {value}")
                    
                    annotations = rule.get('annotations', {})
                    if annotations:
                        st.markdown("**Annotations:**")
                        for key, value in annotations.items():
                            st.text(f"{key}: {value}")
                
                with col2:
                    st.markdown("**Rule Info:**")
                    st.markdown(f"State: {rule.get('state', 'N/A')}")
                    st.markdown(f"Health: {rule.get('health', 'N/A')}")
                    
                    last_evaluation = rule.get('lastEvaluation')
                    if last_evaluation:
                        st.markdown(f"Last Eval: {last_evaluation}")
                    
                    evaluation_time = rule.get('evaluationTime')
                    if evaluation_time:
                        st.markdown(f"Eval Time: {evaluation_time}s")
                        
    except Exception as e:
        st.error(f"Failed to load alert rules: {str(e)}")

def render_alert_history_tab(api_client: httpx.AsyncClient, api_base_url: str):
    """Render alert history tab."""
    st.subheader("📊 Alert History & Trends")
    
    # Time range selection
    col1, col2 = st.columns(2)
    
    with col1:
        hours = st.selectbox("Time Range:", [1, 6, 12, 24, 48, 168], index=3, format_func=lambda x: f"{x} hours")
    
    with col2:
        if st.button("📈 Analyze Trends"):
            analyze_alert_trends(hours, api_client, api_base_url)
    
    try:
        # Get alert history (for now, we'll show current alerts with timestamp info)
        alerts = asyncio.run(get_alert_history(api_client, api_base_url, hours))
        
        if alerts:
            # Create timeline visualization
            render_alert_timeline(alerts)
            
            # Show alert frequency
            render_alert_frequency(alerts)
        else:
            st.info(f"No alert history found for the last {hours} hours.")
            
    except Exception as e:
        st.error(f"Failed to load alert history: {str(e)}")

def render_investigation_tab(api_client: httpx.AsyncClient, api_base_url: str):
    """Render alert investigation tab."""
    st.subheader("🔍 Alert Investigation")
    
    # Get active alerts for investigation
    try:
        alerts = asyncio.run(get_active_alerts(api_client, api_base_url))
        
        if not alerts:
            st.info("No active alerts to investigate.")
            return
        
        # Alert selection
        alert_names = [alert.get('labels', {}).get('alertname', 'Unknown') for alert in alerts]
        selected_alert = st.selectbox("Select alert to investigate:", alert_names)
        
        if st.button("🔍 Start Investigation", type="primary"):
            investigate_alert(selected_alert, api_client, api_base_url)
            
    except Exception as e:
        st.error(f"Failed to load alerts for investigation: {str(e)}")

def investigate_alert(alert_name: str, api_client: httpx.AsyncClient, api_base_url: str):
    """Investigate a specific alert."""
    with st.spinner(f"🔍 Investigating alert: {alert_name}..."):
        try:
            result = asyncio.run(run_alert_investigation(api_client, api_base_url, alert_name))
            
            if result and result.get('status') == 'success':
                st.success("✅ Investigation completed!")
                
                # Show AI explanation
                st.subheader("🤖 AI Analysis")
                st.markdown(result.get('ai_explanation', 'No explanation available'))
                
                # Show alert details
                with st.expander("📋 Alert Details"):
                    st.json(result.get('alert', {}))
                
                # Show related metrics
                related_metrics = result.get('related_metrics', {})
                if related_metrics:
                    with st.expander("📊 Related Metrics"):
                        st.json(related_metrics)
                        
            else:
                st.error(f"Investigation failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"Investigation failed: {str(e)}")

def render_alerts_sidebar():
    """Render alerts page sidebar."""
    with st.sidebar:
        st.markdown("### 🚨 Alert Management")
        
        st.markdown("""
        **Quick Actions:**
        - View all active alerts
        - Investigate critical issues  
        - Check alert rules
        - Analyze alert trends
        """)
        
        st.markdown("---")
        
        # Alert severity guide
        with st.expander("📊 Severity Levels"):
            st.markdown("""
            **🔴 Critical**
            - Service down
            - Data loss risk
            - Immediate action required
            
            **🟡 Warning** 
            - Performance degraded
            - Capacity approaching limits
            - Monitor closely
            
            **🔵 Info**
            - Informational events
            - Maintenance notifications
            - Non-urgent updates
            """)
        
        # Best practices
        with st.expander("💡 Alert Best Practices"):
            st.markdown("""
            **Alert Management:**
            - Acknowledge alerts promptly
            - Document resolution steps
            - Review alert thresholds regularly
            - Keep runbooks updated
            
            **Investigation Tips:**
            - Start with critical alerts
            - Check related metrics
            - Look for patterns
            - Use AI explanations
            """)

# Helper functions
async def get_alert_summary(api_client: httpx.AsyncClient, api_base_url: str) -> Dict[str, Any]:
    """Get alert summary."""
    try:
        response = await api_client.get(f"{api_base_url}/api/v1/alerts/summary")
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

async def get_active_alerts(api_client: httpx.AsyncClient, api_base_url: str) -> List[Dict[str, Any]]:
    """Get active alerts."""
    try:
        response = await api_client.get(f"{api_base_url}/api/v1/alerts/active")
        if response.status_code == 200:
            data = response.json()
            return data.get('alerts', [])
        return []
    except:
        return []

async def get_alert_rules(api_client: httpx.AsyncClient, api_base_url: str) -> List[Dict[str, Any]]:
    """Get alert rules."""
    try:
        response = await api_client.get(f"{api_base_url}/api/v1/alerts/rules")
        if response.status_code == 200:
            data = response.json()
            return data.get('rules', [])
        return []
    except:
        return []

async def get_alert_history(api_client: httpx.AsyncClient, api_base_url: str, hours: int) -> List[Dict[str, Any]]:
    """Get alert history."""
    try:
        response = await api_client.get(f"{api_base_url}/api/v1/alerts/history?hours={hours}")
        if response.status_code == 200:
            data = response.json()
            return data.get('alerts', [])
        return []
    except:
        return []

async def run_alert_investigation(api_client: httpx.AsyncClient, api_base_url: str, alert_name: str) -> Dict[str, Any]:
    """Run alert investigation."""
    try:
        response = await api_client.post(
            f"{api_base_url}/api/v1/analysis/investigate-alert",
            json={"alert_name": alert_name}
        )
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def filter_alerts(alerts: List[Dict[str, Any]], severity: str, instance: str) -> List[Dict[str, Any]]:
    """Filter alerts by criteria."""
    filtered = alerts
    
    if severity != "All":
        filtered = [a for a in filtered if a.get('labels', {}).get('severity') == severity]
    
    if instance != "All":
        filtered = [a for a in filtered if a.get('labels', {}).get('instance') == instance]
    
    return filtered

def sort_alerts(alerts: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort alerts by criteria."""
    if sort_by == "Severity":
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        return sorted(alerts, key=lambda x: severity_order.get(x.get('labels', {}).get('severity', 'info'), 3))
    elif sort_by == "Alert Name":
        return sorted(alerts, key=lambda x: x.get('labels', {}).get('alertname', ''))
    elif sort_by == "Time":
        return sorted(alerts, key=lambda x: x.get('active_at', ''), reverse=True)
    
    return alerts

def render_alert_timeline(alerts: List[Dict[str, Any]]):
    """Render alert timeline visualization."""
    st.markdown("#### ⏰ Alert Timeline")
    
    # This would create a timeline chart
    # For now, show a simple summary
    st.info("Alert timeline visualization would be implemented here with Plotly timeline charts")

def render_alert_frequency(alerts: List[Dict[str, Any]]):
    """Render alert frequency analysis."""
    st.markdown("#### 📊 Alert Frequency")
    
    # Count alerts by name
    alert_counts = {}
    for alert in alerts:
        name = alert.get('labels', {}).get('alertname', 'Unknown')
        alert_counts[name] = alert_counts.get(name, 0) + 1
    
    if alert_counts:
        # Create bar chart
        fig = px.bar(
            x=list(alert_counts.keys()),
            y=list(alert_counts.values()),
            title="Alert Frequency",
            labels={'x': 'Alert Name', 'y': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alert frequency data available")

def analyze_alert_trends(hours: int, api_client: httpx.AsyncClient, api_base_url: str):
    """Analyze alert trends."""
    st.info(f"Analyzing alert trends for the last {hours} hours...")
    # This would implement trend analysis
    st.success("Trend analysis would be implemented here with historical data")

if __name__ == "__main__":
    show_alerts_page()
