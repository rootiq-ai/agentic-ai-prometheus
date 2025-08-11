"""
Utility functions for Prometheus Agent AI.
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import structlog
from functools import wraps
import time

logger = structlog.get_logger()

def validate_promql_query(query: str) -> bool:
    """Validate if a string is a potentially valid PromQL query.
    
    Args:
        query: PromQL query string
        
    Returns:
        True if query appears valid, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    # Basic PromQL validation patterns
    metric_pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*'
    function_pattern = r'^(rate|increase|sum|avg|max|min|count|histogram_quantile|irate|delta|changes)\s*\('
    
    # Remove whitespace for easier checking
    query_clean = query.strip()
    
    # Check if it starts with a metric name or function
    if re.match(metric_pattern, query_clean) or re.match(function_pattern, query_clean):
        return True
    
    return False

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"

def format_bytes(bytes_value: Union[int, float]) -> str:
    """Format bytes to human-readable format.
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}EB"

def extract_metric_names(promql_query: str) -> List[str]:
    """Extract metric names from a PromQL query.
    
    Args:
        promql_query: PromQL query string
        
    Returns:
        List of metric names found in the query
    """
    # Pattern to match metric names
    metric_pattern = r'\b([a-zA-Z_:][a-zA-Z0-9_:]*)\b'
    
    # Find all potential metric names
    matches = re.findall(metric_pattern, promql_query)
    
    # Filter out PromQL functions and keywords
    promql_functions = {
        'rate', 'increase', 'sum', 'avg', 'max', 'min', 'count', 'by', 'without',
        'histogram_quantile', 'irate', 'delta', 'changes', 'sort', 'sort_desc',
        'topk', 'bottomk', 'time', 'vector', 'scalar', 'bool', 'on', 'ignoring',
        'group_left', 'group_right', 'offset', 'and', 'or', 'unless'
    }
    
    metrics = [match for match in matches if match.lower() not in promql_functions]
    return list(set(metrics))  # Remove duplicates

def parse_time_range(time_string: str) -> timedelta:
    """Parse time range string (e.g., '1h', '30m', '7d') to timedelta.
    
    Args:
        time_string: Time range string
        
    Returns:
        timedelta object
    """
    pattern = r'^(\d+)([smhd])$'
    match = re.match(pattern, time_string.lower())
    
    if not match:
        raise ValueError(f"Invalid time range format: {time_string}")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        raise ValueError(f"Unknown time unit: {unit}")

def sanitize_metric_name(name: str) -> str:
    """Sanitize metric name for safe usage.
    
    Args:
        name: Original metric name
        
    Returns:
        Sanitized metric name
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not re.match(r'^[a-zA-Z_]', sanitized):
        sanitized = f"_{sanitized}"
    
    return sanitized

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunked lists
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def retry_async(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            "Function failed after all retries",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e)
                        )
                        raise
                    
                    logger.warning(
                        "Function failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=current_delay,
                        error=str(e)
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

def calculate_rate_of_change(data: pd.DataFrame, value_column: str = 'value', time_column: str = 'timestamp') -> pd.DataFrame:
    """Calculate rate of change for time series data.
    
    Args:
        data: DataFrame with time series data
        value_column: Name of the value column
        time_column: Name of the timestamp column
        
    Returns:
        DataFrame with rate of change calculated
    """
    if data.empty or len(data) < 2:
        return data
    
    # Ensure data is sorted by timestamp
    data_sorted = data.sort_values(time_column)
    
    # Calculate time differences in seconds
    time_diff = data_sorted[time_column].diff().dt.total_seconds()
    
    # Calculate value differences
    value_diff = data_sorted[value_column].diff()
    
    # Calculate rate (value change per second)
    rate = value_diff / time_diff
    
    # Add rate column
    data_sorted['rate'] = rate
    
    return data_sorted

def detect_anomalies(data: pd.DataFrame, value_column: str = 'value', threshold: float = 2.0) -> pd.DataFrame:
    """Detect anomalies in time series data using standard deviation.
    
    Args:
        data: DataFrame with time series data
        value_column: Name of the value column
        threshold: Number of standard deviations for anomaly detection
        
    Returns:
        DataFrame with anomaly detection results
    """
    if data.empty or len(data) < 3:
        data['is_anomaly'] = False
        return data
    
    values = data[value_column]
    mean_val = values.mean()
    std_val = values.std()
    
    # Mark values outside threshold * std as anomalies
    data['is_anomaly'] = abs(values - mean_val) > (threshold * std_val)
    data['anomaly_score'] = abs(values - mean_val) / std_val if std_val > 0 else 0
    
    return data

def format_prometheus_time(dt: datetime) -> str:
    """Format datetime for Prometheus API.
    
    Args:
        dt: datetime object
        
    Returns:
        Formatted timestamp string
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def parse_prometheus_labels(labels_str: str) -> Dict[str, str]:
    """Parse Prometheus labels string into dictionary.
    
    Args:
        labels_str: Labels string like '{job="prometheus",instance="localhost:9090"}'
        
    Returns:
        Dictionary of label key-value pairs
    """
    if not labels_str or labels_str == '{}':
        return {}
    
    # Remove outer braces
    labels_str = labels_str.strip('{}')
    
    labels = {}
    
    # Split by comma, but handle quoted values
    parts = []
    current_part = ""
    in_quotes = False
    
    for char in labels_str:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            parts.append(current_part.strip())
            current_part = ""
            continue
        
        current_part += char
    
    if current_part.strip():
        parts.append(current_part.strip())
    
    # Parse each key=value pair
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')
            labels[key] = value
    
    return labels

class TimedCache:
    """Simple time-based cache for function results."""
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL.
        
        Args:
            ttl_seconds: Time to live in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                return entry['value']
            else:
                del self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()

# Global cache instance
cache = TimedCache(ttl_seconds=300)  # 5 minutes TTL
