"""
Dashboard component for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class DashboardComponent:
    """Dashboard component for displaying metrics overview."""
    
    def __init__(self, api_client: httpx.AsyncClient, api_base_url: str):
        """Initialize dashboard component.
        
        Args:
            api_client: HTTP client for API calls
            api_base_url: Base URL for the API
        """
        self.api_client = api_client
        self.api_base_url = api_base_url
    
    def render_metrics_overview(self) -> None:
        """Render the main metrics overview dashboard."""
        st.header("📊 System Metrics Overview")
        
        # Time range selector
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            time_range = st.selectbox(
                "Time Range",
                ["1h", "6h", "12h", "24h", "7d"],
                index=0,
                key="dashboard_time_range"
            )
        
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=False)
        
        with col3:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        
        # Auto refresh logic
        if auto_refresh:
            if "last_refresh" not in st.session_state:
                st.session_state.last_refresh = datetime.now()
            
            # Refresh every 30 seconds
            if (datetime.now() - st.session_state.last_refresh).seconds > 30:
                st.session_state.last_refresh = datetime.now()
                st.rerun()
        
        # Key metrics cards
        self._render_key_metrics_cards()
        
        # System health charts
        self._render_system_health_charts(time_range)
        
        # Active alerts section
        self._render_active_alerts_section()
        
        # Recent activity
        self._render_recent_activity()
    
    def _render_key_metrics_cards(self) -> None:
        """Render key metrics cards at the top of dashboard."""
        st.subheader("Key Metrics")
        
        # Fetch system status
        try:
            system_status = asyncio.run(self._get_system_status())
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="🟢 Services Up",
                    value=f"{system_status.get('services_up', 0)}/{system_status.get('total_services', 0)}",
                    delta=None
                )
            
            with col2:
                alerts_count = system_status.get('active_alerts', 0)
                st.metric(
                    label="⚠️ Active Alerts",
                    value=str(alerts_count),
                    delta=f"+{alerts_count}" if alerts_count > 0 else "0",
                    delta_color="inverse"
                )
            
            with col3:
                cpu_usage = system_status.get('avg_cpu_usage', 0)
                st.metric(
                    label="💻 Avg CPU Usage",
                    value=f"{cpu_usage:.1f}%",
                    delta=f"{cpu_usage - 50:.1f}%" if cpu_usage else None,
                    delta_color="inverse" if cpu_usage > 80 else "normal"
                )
            
            with col4:
                memory_usage = system_status.get('avg_memory_usage', 0)
                st.metric(
                    label="🧠 Avg Memory Usage",
                    value=f"{memory_usage:.1f}%",
                    delta=f"{memory_usage - 50:.1f}%" if memory_usage else None,
                    delta_color="inverse" if memory_usage > 85 else "normal"
                )
                
        except Exception as e:
            st.error(f"Failed to fetch system status: {str(e)}")
    
    def _render_system_health_charts(self, time_range: str) -> None:
        """Render system health charts.
        
        Args:
            time_range: Time range for the charts
        """
        st.subheader("System Health Trends")
        
        try:
            # Fetch metrics data
            metrics_data = asyncio.run(self._get_metrics_data(time_range))
            
            if not metrics_data:
                st.warning("No metrics data available for the selected time range.")
                return
            
            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('CPU Usage', 'Memory Usage', 'Network I/O', 'Disk I/O'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": True}, {"secondary_y": True}]]
            )
            
            # CPU Usage Chart
            if 'cpu_usage' in metrics_data:
                cpu_df = pd.DataFrame(metrics_data['cpu_usage'])
                if not cpu_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=cpu_df['timestamp'],
                            y=cpu_df['value'],
                            name='CPU Usage %',
                            line=dict(color='#FF6B6B'),
                            mode='lines'
                        ),
                        row=1, col=1
                    )
            
            # Memory Usage Chart
            if 'memory_usage' in metrics_data:
                memory_df = pd.DataFrame(metrics_data['memory_usage'])
                if not memory_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=memory_df['timestamp'],
                            y=memory_df['value'],
                            name='Memory Usage %',
                            line=dict(color='#4ECDC4'),
                            mode='lines'
                        ),
                        row=1, col=2
                    )
            
            # Network I/O Chart
            if 'network_in' in metrics_data and 'network_out' in metrics_data:
                net_in_df = pd.DataFrame(metrics_data['network_in'])
                net_out_df = pd.DataFrame(metrics_data['network_out'])
                
                if not net_in_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=net_in_df['timestamp'],
                            y=net_in_df['value'],
                            name='Network In',
                            line=dict(color='#45B7D1'),
                            mode='lines'
                        ),
                        row=2, col=1
                    )
                
                if not net_out_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=net_out_df['timestamp'],
                            y=net_out_df['value'],
                            name='Network Out',
                            line=dict(color='#96CEB4'),
                            mode='lines'
                        ),
                        row=2, col=1
                    )
            
            # Disk I/O Chart
            if 'disk_read' in metrics_data and 'disk_write' in metrics_data:
                disk_read_df = pd.DataFrame(metrics_data['disk_read'])
                disk_write_df = pd.DataFrame(metrics_data['disk_write'])
                
                if not disk_read_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=disk_read_df['timestamp'],
                            y=disk_read_df['value'],
                            name='Disk Read',
                            line=dict(color='#FECA57'),
                            mode='lines'
                        ),
                        row=2, col=2
                    )
                
                if not disk_write_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=disk_write_df['timestamp'],
                            y=disk_write_df['value'],
                            name='Disk Write',
                            line=dict(color='#FF9FF3'),
                            mode='lines'
                        ),
                        row=2, col=2
                    )
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                title_text=f"System Metrics - Last {time_range}",
                title_x=0.5
            )
            
            # Update y-axis labels
            fig.update_yaxes(title_text="Percentage (%)", row=1, col=1)
            fig.update_yaxes(title_text="Percentage (%)", row=1, col=2)
            fig.update_yaxes(title_text="Bytes/sec", row=2, col=1)
            fig.update_yaxes(title_text="Bytes/sec", row=2, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Failed to render system health charts: {str(e)}")
    
    def _render_active_alerts_section(self) -> None:
        """Render active alerts section."""
        st.subheader("🚨 Active Alerts")
        
        try:
            alerts = asyncio.run(self._get_active_alerts())
            
            if not alerts:
                st.success("🎉 No active alerts - All systems are running normally!")
                return
            
            # Create alerts DataFrame
            alerts_df = pd.DataFrame(alerts)
            
            # Alert severity distribution
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if 'severity' in alerts_df.columns:
                    severity_counts = alerts_df['severity'].value_counts()
                    
                    fig_pie = px.pie(
                        values=severity_counts.values,
                        names=severity_counts.index,
                        title="Alerts by Severity",
                        color_discrete_map={
                            'critical': '#FF6B6B',
                            'warning': '#FFD93D',
                            'info': '#6BCF7F'
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Recent alerts table
                st.write("**Recent Alerts**")
                
                # Prepare alerts for display
                display_alerts = []
                for alert in alerts[:10]:  # Show last 10 alerts
                    labels = alert.get('labels', {})
                    annotations = alert.get('annotations', {})
                    
                    display_alerts.append({
                        'Alert': labels.get('alertname', 'Unknown'),
                        'Severity': labels.get('severity', 'unknown'),
                        'Instance': labels.get('instance', 'N/A'),
                        'Summary': annotations.get('summary', 'No summary'),
                        'State': alert.get('state', 'unknown')
                    })
                
                if display_alerts:
                    alerts_display_df = pd.DataFrame(display_alerts)
                    st.dataframe(alerts_display_df, use_container_width=True)
                else:
                    st.info("No alert details available.")
        
        except Exception as e:
            st.error(f"Failed to fetch active alerts: {str(e)}")
    
    def _render_recent_activity(self) -> None:
        """Render recent activity section."""
        st.subheader("📈 Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Queries (Last Hour)**")
            try:
                top_queries = asyncio.run(self._get_top_queries())
                if top_queries:
                    for i, query in enumerate(top_queries[:5], 1):
                        st.write(f"{i}. `{query}`")
                else:
                    st.info("No recent queries available.")
            except Exception:
                st.warning("Could not fetch recent queries.")
        
        with col2:
            st.write("**System Events**")
            try:
                events = asyncio.run(self._get_recent_events())
                if events:
                    for event in events[:5]:
                        timestamp = event.get('timestamp', 'Unknown time')
                        message = event.get('message', 'No message')
                        st.write(f"• {timestamp}: {message}")
                else:
                    st.info("No recent events available.")
            except Exception:
                st.warning("Could not fetch recent events.")
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            # Get health check
            health_response = await self.api_client.get(f"{self.api_base_url}/health")
            health_data = health_response.json()
            
            # Get active alerts count
            alerts_response = await self.api_client.get(f"{self.api_base_url}/api/v1/alerts/active")
            alerts_data = alerts_response.json()
            
            # Get basic metrics
            common_metrics_response = await self.api_client.get(
                f"{self.api_base_url}/api/v1/metrics/common?hours=1"
            )
            metrics_data = common_metrics_response.json()
            
            return {
                'services_up': 3 if health_data.get('prometheus_connected') else 0,
                'total_services': 3,
                'active_alerts': alerts_data.get('count', 0),
                'avg_cpu_usage': 45.2,  # Would be calculated from actual metrics
                'avg_memory_usage': 67.8,  # Would be calculated from actual metrics
            }
            
        except Exception as e:
            st.warning(f"Could not fetch system status: {str(e)}")
            return {}
    
    async def _get_metrics_data(self, time_range: str) -> Dict[str, List[Dict]]:
        """Get metrics data for charts."""
        try:
            # Convert time range to hours
            hours_map = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "7d": 168}
            hours = hours_map.get(time_range, 1)
            
            response = await self.api_client.get(
                f"{self.api_base_url}/api/v1/metrics/common?hours={hours}"
            )
            
            if response.status_code == 200:
                data = response.json()
                metrics = data.get('metrics', {})
                
                # Transform data for plotting
                result = {}
                for metric_name, metric_data in metrics.items():
                    if metric_data.get('has_data') and metric_data.get('data'):
                        # Extract time series data
                        series_data = metric_data['data'].get('result', [])
                        if series_data:
                            points = []
                            for series in series_data:
                                if 'values' in series:
                                    for timestamp, value in series['values']:
                                        points.append({
                                            'timestamp': pd.to_datetime(timestamp, unit='s'),
                                            'value': float(value)
                                        })
                            
                            if points:
                                result[metric_name] = points
                
                return result
            
            return {}
            
        except Exception as e:
            st.warning(f"Could not fetch metrics data: {str(e)}")
            return {}
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        try:
            response = await self.api_client.get(f"{self.api_base_url}/api/v1/alerts/active")
            
            if response.status_code == 200:
                data = response.json()
                return data.get('alerts', [])
            
            return []
            
        except Exception as e:
            st.warning(f"Could not fetch active alerts: {str(e)}")
            return []
    
    async def _get_top_queries(self) -> List[str]:
        """Get top queries from recent activity."""
        # This would typically come from logs or a database
        # For now, return some example queries
        return [
            "up",
            "rate(http_requests_total[5m])",
            "node_memory_MemAvailable_bytes",
            "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "increase(prometheus_notifications_total[1h])"
        ]
    
    async def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent system events."""
        # This would typically come from logs or event store
        # For now, return some example events
        now = datetime.now()
        return [
            {
                'timestamp': (now - timedelta(minutes=5)).strftime('%H:%M:%S'),
                'message': 'System health analysis completed'
            },
            {
                'timestamp': (now - timedelta(minutes=12)).strftime('%H:%M:%S'),
                'message': 'New Prometheus target discovered'
            },
            {
                'timestamp': (now - timedelta(minutes=18)).strftime('%H:%M:%S'),
                'message': 'Alert rule evaluation completed'
            },
            {
                'timestamp': (now - timedelta(minutes=25)).strftime('%H:%M:%S'),
                'message': 'Configuration reload successful'
            }
        ]
