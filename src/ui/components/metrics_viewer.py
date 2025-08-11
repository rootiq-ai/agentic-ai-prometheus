"""
Metrics viewer component for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import re

class MetricsViewerComponent:
    """Component for viewing and analyzing Prometheus metrics."""
    
    def __init__(self, api_client: httpx.AsyncClient, api_base_url: str):
        """Initialize metrics viewer component.
        
        Args:
            api_client: HTTP client for API calls
            api_base_url: Base URL for the API
        """
        self.api_client = api_client
        self.api_base_url = api_base_url
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state variables."""
        if "selected_metrics" not in st.session_state:
            st.session_state.selected_metrics = []
        
        if "custom_query" not in st.session_state:
            st.session_state.custom_query = ""
        
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
    
    def render_metrics_explorer(self) -> None:
        """Render the main metrics explorer interface."""
        st.header("📊 Metrics Explorer")
        
        # Metrics browser and query interface
        col1, col2 = st.columns([1, 2])
        
        with col1:
            self._render_metrics_browser()
        
        with col2:
            self._render_query_interface()
        
        # Query results and visualization
        self._render_query_results()
    
    def _render_metrics_browser(self) -> None:
        """Render the metrics browser sidebar."""
        st.subheader("📋 Available Metrics")
        
        # Search metrics
        search_term = st.text_input(
            "🔍 Search metrics:",
            placeholder="e.g., cpu, memory, http",
            key="metrics_search"
        )
        
        # Get available metrics
        try:
            metrics = asyncio.run(self._get_available_metrics())
            
            if search_term:
                metrics = [m for m in metrics if search_term.lower() in m.lower()]
            
            # Display metrics in categories
            self._display_metrics_by_category(metrics)
            
        except Exception as e:
            st.error(f"Failed to load metrics: {str(e)}")
    
    def _display_metrics_by_category(self, metrics: List[str]) -> None:
        """Display metrics organized by category.
        
        Args:
            metrics: List of metric names
        """
        # Categorize metrics
        categories = self._categorize_metrics(metrics)
        
        # Display each category
        for category, metric_list in categories.items():
            if metric_list:
                with st.expander(f"📁 {category} ({len(metric_list)})", expanded=(category == "System")):
                    for metric in metric_list[:20]:  # Limit to 20 per category
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.text(metric)
                        
                        with col2:
                            if st.button("➕", key=f"add_{metric}", help=f"Add {metric} to query"):
                                self._add_metric_to_query(metric)
    
    def _categorize_metrics(self, metrics: List[str]) -> Dict[str, List[str]]:
        """Categorize metrics by common patterns.
        
        Args:
            metrics: List of metric names
            
        Returns:
            Dictionary of categorized metrics
        """
        categories = {
            "System": [],
            "HTTP": [],
            "Database": [],
            "Application": [],
            "Network": [],
            "Prometheus": [],
            "Other": []
        }
        
        # Categorization patterns
        patterns = {
            "System": [r"node_", r"cpu_", r"memory_", r"disk_", r"filesystem_"],
            "HTTP": [r"http_", r"nginx_", r"apache_"],
            "Database": [r"mysql_", r"postgres_", r"redis_", r"mongodb_"],
            "Application": [r"app_", r"service_", r"custom_"],
            "Network": [r"network_", r"interface_", r"tcp_", r"udp_"],
            "Prometheus": [r"prometheus_", r"up$", r"scrape_"]
        }
        
        for metric in metrics:
            categorized = False
            
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, metric, re.IGNORECASE):
                        categories[category].append(metric)
                        categorized = True
                        break
                
                if categorized:
                    break
            
            if not categorized:
                categories["Other"].append(metric)
        
        # Sort metrics within each category
        for category in categories:
            categories[category].sort()
        
        return categories
    
    def _render_query_interface(self) -> None:
        """Render the query interface."""
        st.subheader("🔧 Query Interface")
        
        # Query tabs
        tab1, tab2, tab3 = st.tabs(["PromQL Query", "Query Builder", "History"])
        
        with tab1:
            self._render_promql_tab()
        
        with tab2:
            self._render_query_builder_tab()
        
        with tab3:
            self._render_query_history_tab()
    
    def _render_promql_tab(self) -> None:
        """Render the PromQL query tab."""
        # Custom PromQL query
        query = st.text_area(
            "Enter PromQL query:",
            value=st.session_state.custom_query,
            height=100,
            placeholder="e.g., rate(http_requests_total[5m])",
            help="Enter a valid PromQL expression"
        )
        
        # Query options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query_type = st.radio(
                "Query Type:",
                ["Instant", "Range"],
                key="query_type"
            )
        
        with col2:
            if query_type == "Range":
                time_range = st.selectbox(
                    "Time Range:",
                    ["1h", "6h", "12h", "24h", "7d"],
                    key="time_range"
                )
                
                step = st.selectbox(
                    "Step:",
                    ["15s", "30s", "1m", "5m", "15m", "1h"],
                    index=2,
                    key="step"
                )
            else:
                time_range = None
                step = None
        
        with col3:
            st.write("")  # Spacing
            execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)
        
        # Execute query
        if execute_button and query.strip():
            st.session_state.custom_query = query
            self._execute_query(query, query_type, time_range, step)
    
    def _render_query_builder_tab(self) -> None:
        """Render the visual query builder tab."""
        st.info("🚧 Visual Query Builder - Coming Soon!")
        
        # Placeholder for query builder
        st.markdown("""
        **Future features:**
        - Drag & drop metric selection
        - Visual function composition
        - Template-based query generation
        - Query validation and suggestions
        """)
    
    def _render_query_history_tab(self) -> None:
        """Render the query history tab."""
        if not st.session_state.query_history:
            st.info("No query history available. Execute some queries to see them here.")
            return
        
        st.write(f"**Recent Queries ({len(st.session_state.query_history)}):**")
        
        for i, query_info in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"Query {len(st.session_state.query_history) - i}: {query_info['query'][:50]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.code(query_info['query'], language='promql')
                    st.text(f"Executed: {query_info['timestamp']}")
                    if query_info.get('error'):
                        st.error(f"Error: {query_info['error']}")
                    else:
                        st.success(f"Success - {query_info.get('result_count', 0)} results")
                
                with col2:
                    if st.button("🔄 Re-run", key=f"rerun_{i}"):
                        self._execute_query(
                            query_info['query'],
                            query_info.get('type', 'Instant'),
                            query_info.get('time_range'),
                            query_info.get('step')
                        )
    
    def _render_query_results(self) -> None:
        """Render query results and visualizations."""
        if "last_query_result" not in st.session_state:
            st.info("👆 Execute a query above to see results and visualizations here.")
            return
        
        result = st.session_state.last_query_result
        
        if result.get("error"):
            st.error(f"Query failed: {result['error']}")
            return
        
        st.subheader("📈 Query Results")
        
        # Results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Visualization", "Raw Data", "Table View", "Export"])
        
        with tab1:
            self._render_visualization_tab(result)
        
        with tab2:
            self._render_raw_data_tab(result)
        
        with tab3:
            self._render_table_tab(result)
        
        with tab4:
            self._render_export_tab(result)
    
    def _render_visualization_tab(self, result: Dict[str, Any]) -> None:
        """Render visualization of query results.
        
        Args:
            result: Query result data
        """
        if not result.get("dataframe"):
            st.warning("No data available for visualization.")
            return
        
        df = pd.DataFrame(result["dataframe"])
        
        if df.empty:
            st.warning("No data points to visualize.")
            return
        
        # Chart type selection
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            chart_type = st.selectbox(
                "Chart Type:",
                ["Line Chart", "Area Chart", "Bar Chart", "Scatter Plot"],
                key="chart_type"
            )
        
        with col2:
            if "timestamp" in df.columns:
                time_grouping = st.selectbox(
                    "Time Grouping:",
                    ["None", "1min", "5min", "15min", "1hour"],
                    key="time_grouping"
                )
            else:
                time_grouping = "None"
        
        with col3:
            if len(df.select_dtypes(include=['number']).columns) > 1:
                show_legend = st.checkbox("Show Legend", value=True)
            else:
                show_legend = False
        
        # Create visualization
        try:
            self._create_chart(df, chart_type, time_grouping, show_legend)
        except Exception as e:
            st.error(f"Failed to create chart: {str(e)}")
    
    def _create_chart(self, df: pd.DataFrame, chart_type: str, time_grouping: str, show_legend: bool) -> None:
        """Create and display chart based on parameters.
        
        Args:
            df: Data to chart
            chart_type: Type of chart to create
            time_grouping: Time aggregation grouping
            show_legend: Whether to show legend
        """
        # Prepare data
        if time_grouping != "None" and "timestamp" in df.columns:
            # Group by time
            df_grouped = self._group_by_time(df, time_grouping)
        else:
            df_grouped = df
        
        # Get numeric columns for plotting
        numeric_columns = df_grouped.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_columns:
            st.warning("No numeric data available for plotting.")
            return
        
        # Create chart based on type
        if chart_type == "Line Chart":
            if "timestamp" in df_grouped.columns:
                fig = px.line(df_grouped, x="timestamp", y=numeric_columns[0], 
                             title=f"Time Series: {numeric_columns[0]}")
            else:
                fig = px.line(df_grouped, y=numeric_columns[0], 
                             title=f"Line Chart: {numeric_columns[0]}")
        
        elif chart_type == "Area Chart":
            if "timestamp" in df_grouped.columns:
                fig = px.area(df_grouped, x="timestamp", y=numeric_columns[0],
                             title=f"Area Chart: {numeric_columns[0]}")
            else:
                fig = px.area(df_grouped, y=numeric_columns[0],
                             title=f"Area Chart: {numeric_columns[0]}")
        
        elif chart_type == "Bar Chart":
            if len(df_grouped) > 50:
                st.warning("Too many data points for bar chart. Showing first 50.")
                df_grouped = df_grouped.head(50)
            
            fig = px.bar(df_grouped, y=numeric_columns[0],
                        title=f"Bar Chart: {numeric_columns[0]}")
        
        elif chart_type == "Scatter Plot":
            if len(numeric_columns) >= 2:
                fig = px.scatter(df_grouped, x=numeric_columns[0], y=numeric_columns[1],
                               title=f"Scatter: {numeric_columns[0]} vs {numeric_columns[1]}")
            else:
                if "timestamp" in df_grouped.columns:
                    fig = px.scatter(df_grouped, x="timestamp", y=numeric_columns[0],
                                   title=f"Scatter: {numeric_columns[0]}")
                else:
                    fig = px.scatter(df_grouped, y=numeric_columns[0],
                                   title=f"Scatter: {numeric_columns[0]}")
        
        # Update layout
        fig.update_layout(
            showlegend=show_legend,
            height=500,
            xaxis_title=None,
            yaxis_title=None
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show basic statistics
        if numeric_columns:
            st.subheader("📊 Statistics")
            stats_df = df_grouped[numeric_columns].describe()
            st.dataframe(stats_df, use_container_width=True)
    
    def _render_raw_data_tab(self, result: Dict[str, Any]) -> None:
        """Render raw data tab.
        
        Args:
            result: Query result data
        """
        st.subheader("🔍 Raw Query Response")
        st.json(result.get("results", {}))
    
    def _render_table_tab(self, result: Dict[str, Any]) -> None:
        """Render table view tab.
        
        Args:
            result: Query result data
        """
        if not result.get("dataframe"):
            st.warning("No tabular data available.")
            return
        
        df = pd.DataFrame(result["dataframe"])
        
        if df.empty:
            st.warning("No data to display in table.")
            return
        
        # Table options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_index = st.checkbox("Show Index", value=False)
        
        with col2:
            max_rows = st.number_input("Max Rows", min_value=10, max_value=1000, value=100)
        
        with col3:
            if st.button("📋 Copy to Clipboard"):
                st.info("Copy functionality would be implemented here")
        
        # Display table
        st.dataframe(
            df.head(max_rows),
            use_container_width=True,
            hide_index=not show_index
        )
        
        # Show data info
        st.caption(f"Showing {min(len(df), max_rows)} of {len(df)} rows")
    
    def _render_export_tab(self, result: Dict[str, Any]) -> None:
        """Render export tab.
        
        Args:
            result: Query result data
        """
        st.subheader("📤 Export Data")
        
        if not result.get("dataframe"):
            st.warning("No data available for export.")
            return
        
        df = pd.DataFrame(result["dataframe"])
        
        if df.empty:
            st.warning("No data to export.")
            return
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format:",
                ["CSV", "JSON", "Excel"],
                key="export_format"
            )
        
        with col2:
            include_metadata = st.checkbox("Include Metadata", value=True)
        
        # Generate export
        if st.button("📥 Download", type="primary"):
            try:
                if export_format == "CSV":
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download CSV",
                        data=csv_data,
                        file_name=f"prometheus_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    export_data = {
                        "query": result.get("original_query", ""),
                        "timestamp": datetime.now().isoformat(),
                        "data": df.to_dict(orient="records")
                    }
                    
                    if include_metadata and "results" in result:
                        export_data["metadata"] = result["results"]
                    
                    json_data = json.dumps(export_data, indent=2)
                    st.download_button(
                        label="📄 Download JSON",
                        data=json_data,
                        file_name=f"prometheus_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "Excel":
                    # Note: This would require openpyxl package
                    st.info("Excel export would be implemented with openpyxl")
                    
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    def _add_metric_to_query(self, metric: str) -> None:
        """Add a metric to the current query.
        
        Args:
            metric: Metric name to add
        """
        current_query = st.session_state.custom_query
        
        if current_query.strip():
            # Add to existing query (simple concatenation for now)
            st.session_state.custom_query = f"{current_query.strip()}, {metric}"
        else:
            st.session_state.custom_query = metric
        
        st.success(f"Added {metric} to query")
        st.rerun()
    
    def _execute_query(self, query: str, query_type: str, time_range: Optional[str] = None, step: Optional[str] = None) -> None:
        """Execute a PromQL query.
        
        Args:
            query: PromQL query string
            query_type: Type of query (Instant or Range)
            time_range: Time range for range queries
            step: Step for range queries
        """
        with st.spinner("Executing query..."):
            try:
                if query_type == "Range" and time_range:
                    result = asyncio.run(self._execute_range_query(query, time_range, step))
                else:
                    result = asyncio.run(self._execute_instant_query(query))
                
                # Store result
                st.session_state.last_query_result = result
                
                # Add to history
                query_info = {
                    "query": query,
                    "type": query_type,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "time_range": time_range,
                    "step": step
                }
                
                if result.get("error"):
                    query_info["error"] = result["error"]
                else:
                    query_info["result_count"] = len(result.get("results", {}).get("result", []))
                
                st.session_state.query_history.append(query_info)
                
                # Show success/error message
                if result.get("error"):
                    st.error(f"Query failed: {result['error']}")
                else:
                    st.success("Query executed successfully!")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Query execution failed: {str(e)}")
    
    async def _execute_instant_query(self, query: str) -> Dict[str, Any]:
        """Execute an instant query.
        
        Args:
            query: PromQL query
            
        Returns:
            Query result
        """
        try:
            response = await self.api_client.post(
                f"{self.api_base_url}/api/v1/metrics/query",
                json={"query": query}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_range_query(self, query: str, time_range: str, step: str) -> Dict[str, Any]:
        """Execute a range query.
        
        Args:
            query: PromQL query
            time_range: Time range (e.g., "1h")
            step: Query step (e.g., "1m")
            
        Returns:
            Query result
        """
        try:
            # Calculate start and end times
            end_time = datetime.now()
            
            # Parse time range
            time_map = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "7d": 168}
            hours = time_map.get(time_range, 1)
            start_time = end_time - timedelta(hours=hours)
            
            response = await self.api_client.post(
                f"{self.api_base_url}/api/v1/metrics/query_range",
                json={
                    "query": query,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "step": step or "1m"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_available_metrics(self) -> List[str]:
        """Get list of available metrics.
        
        Returns:
            List of metric names
        """
        try:
            response = await self.api_client.get(f"{self.api_base_url}/api/v1/metrics/metadata")
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata", {})
                return list(metadata.keys())
            else:
                return []
                
        except Exception:
            # Return some common metrics as fallback
            return [
                "up", "node_cpu_seconds_total", "node_memory_MemTotal_bytes",
                "prometheus_notifications_total", "http_requests_total"
            ]
    
    def _group_by_time(self, df: pd.DataFrame, grouping: str) -> pd.DataFrame:
        """Group dataframe by time intervals.
        
        Args:
            df: DataFrame with timestamp column
            grouping: Time grouping (e.g., "5min")
            
        Returns:
            Grouped DataFrame
        """
        if "timestamp" not in df.columns:
            return df
        
        # Convert timestamp to datetime if needed
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Group by time intervals
        freq_map = {
            "1min": "1min",
            "5min": "5min", 
            "15min": "15min",
            "1hour": "1h"
        }
        
        freq = freq_map.get(grouping, "1min")
        df_grouped = df.set_index("timestamp").resample(freq).mean().reset_index()
        
        return df_grouped
