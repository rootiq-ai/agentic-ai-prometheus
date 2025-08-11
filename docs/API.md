# Prometheus Agent AI - API Documentation

## Overview

The Prometheus Agent AI provides a comprehensive REST API for AI-powered monitoring and analysis of Prometheus metrics. The API is built with FastAPI and includes interactive documentation.

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/api/docs`  
**OpenAPI Schema:** `http://localhost:8000/openapi.json`

## Authentication

Currently, the API does not require authentication for basic usage. In production environments, consider implementing API keys or OAuth2.

## API Endpoints

### Health Check

#### `GET /health`

Check the health and status of all services.

**Response:**
```json
{
  "status": "healthy",
  "prometheus_connected": true,
  "openai_connected": true,
  "agent_ready": true,
  "uptime_seconds": 3600.5,
  "version": "1.0.0"
}
```

---

## Metrics Endpoints

### Execute PromQL Query

#### `POST /api/v1/metrics/query`

Execute an instant PromQL query.

**Request Body:**
```json
{
  "query": "up",
  "time": "2024-01-01T12:00:00Z"  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "resultType": "vector",
    "result": [
      {
        "metric": {
          "__name__": "up",
          "instance": "localhost:9090",
          "job": "prometheus"
        },
        "value": [1609459200, "1"]
      }
    ]
  },
  "query": "up",
  "execution_time_ms": 45.2
}
```

### Execute Range Query

#### `POST /api/v1/metrics/query_range`

Execute a PromQL range query over a time period.

**Request Body:**
```json
{
  "query": "rate(http_requests_total[5m])",
  "start": "2024-01-01T10:00:00Z",
  "end": "2024-01-01T12:00:00Z",
  "step": "1m"
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "http_requests_total",
          "method": "GET"
        },
        "values": [
          [1609459200, "10.5"],
          [1609459260, "12.1"]
        ]
      }
    ]
  },
  "dataframe": {...},  // Pandas DataFrame representation
  "metadata": {
    "start": "2024-01-01T10:00:00Z",
    "end": "2024-01-01T12:00:00Z",
    "step": "1m",
    "data_points": 120
  }
}
```

### Get Metrics Metadata

#### `GET /api/v1/metrics/metadata`

Get metadata for all available metrics.

**Response:**
```json
{
  "status": "success",
  "metadata": {
    "up": {
      "type": "gauge",
      "help": "1 if the instance is healthy, 0 otherwise",
      "unit": ""
    },
    "http_requests_total": {
      "type": "counter",
      "help": "Total number of HTTP requests",
      "unit": "requests"
    }
  }
}
```

### Get Label Names

#### `GET /api/v1/metrics/labels`

Get all available label names.

**Response:**
```json
{
  "status": "success",
  "labels": ["__name__", "instance", "job", "method", "status"],
  "count": 5
}
```

### Get Label Values

#### `GET /api/v1/metrics/labels/{label}/values`

Get all values for a specific label.

**Parameters:**
- `label`: Label name (path parameter)

**Response:**
```json
{
  "status": "success",
  "label": "instance",
  "values": ["localhost:9090", "localhost:9100"],
  "count": 2
}
```

### Get Common Metrics

#### `GET /api/v1/metrics/common?hours=1`

Get commonly used metrics with data.

**Query Parameters:**
- `hours`: Hours of data to analyze (default: 1)

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "up": {
      "query": "up",
      "data": {...},
      "has_data": true
    },
    "cpu_usage": {
      "query": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
      "data": {...},
      "has_data": true
    }
  },
  "available_metrics": ["up", "cpu_usage"],
  "time_range": "1 hours"
}
```

---

## Alerts Endpoints

### Get Active Alerts

#### `GET /api/v1/alerts/active`

Get all currently active alerts.

**Response:**
```json
{
  "status": "success",
  "alerts": [
    {
      "labels": {
        "alertname": "HighCPUUsage",
        "severity": "warning",
        "instance": "localhost:9090"
      },
      "annotations": {
        "summary": "High CPU usage detected",
        "description": "CPU usage is above 80% for more than 5 minutes"
      },
      "state": "firing",
      "activeAt": "2024-01-01T12:00:00Z",
      "value": "85.2"
    }
  ],
  "count": 1
}
```

### Get Alerting Rules

#### `GET /api/v1/alerts/rules`

Get all configured alerting rules.

**Response:**
```json
{
  "status": "success",
  "rules": [
    {
      "name": "HighCPUUsage",
      "query": "cpu_usage > 80",
      "duration": "5m",
      "labels": {
        "severity": "warning"
      },
      "annotations": {
        "summary": "High CPU usage on {{ $labels.instance }}",
        "description": "CPU usage is above 80%"
      },
      "state": "inactive",
      "health": "ok"
    }
  ],
  "count": 1
}
```

### Get Alerts Summary

#### `GET /api/v1/alerts/summary`

Get a summary of alert status and statistics.

**Response:**
```json
{
  "status": "success",
  "total_active_alerts": 3,
  "total_alerting_rules": 15,
  "severity_breakdown": {
    "critical": 1,
    "warning": 2,
    "info": 0
  },
  "state_breakdown": {
    "firing": 2,
    "pending": 1
  },
  "most_common_alerts": [
    ["HighCPUUsage", 2],
    ["DiskSpaceLow", 1]
  ]
}
```

---

## AI Analysis Endpoints

### System Health Analysis

#### `POST /api/v1/analysis/health`

Perform AI-powered system health analysis.

**Request Body:**
```json
{
  "time_range_hours": 2
}
```

**Response:**
```json
{
  "status": "success",
  "analysis_timestamp": "2024-01-01T12:00:00Z",
  "time_range_hours": 2,
  "metrics_collected": ["up", "cpu_usage", "memory_usage"],
  "active_alerts_count": 2,
  "ai_analysis": "System is experiencing moderate load with 2 active alerts. CPU usage is elevated but within acceptable ranges. Memory usage is stable. The ServiceDown alert requires immediate attention as it indicates a critical service failure.",
  "health_score": 78.5,
  "anomalies_detected": [
    {
      "metric": "cpu_usage",
      "timestamp": "2024-01-01T11:45:00Z",
      "value": 95.2,
      "severity": "high"
    }
  ],
  "recommendations": [
    "Investigate the ServiceDown alert immediately",
    "Monitor CPU usage trends over the next hour",
    "Consider scaling resources if load continues"
  ],
  "raw_data": {...}
}
```

### Natural Language Query

#### `POST /api/v1/analysis/natural-language`

Convert natural language questions into PromQL queries and execute them.

**Request Body:**
```json
{
  "query": "Show me CPU usage for the last hour"
}
```

**Response:**
```json
{
  "status": "success",
  "original_query": "Show me CPU usage for the last hour",
  "generated_promql": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
  "results": {...},
  "dataframe": {...},
  "ai_analysis": "CPU usage has been averaging around 65% over the last hour with a peak of 82% at 11:30 AM. This indicates moderate system load with brief periods of high utilization.",
  "confidence_score": 0.92,
  "alternative_queries": [
    "node_cpu_seconds_total",
    "rate(node_cpu_seconds_total[1h])"
  ]
}
```

### Chat with Agent

#### `POST /api/v1/analysis/chat`

Have a conversational interaction with the AI agent.

**Request Body:**
```json
{
  "message": "What's causing the high CPU usage?",
  "conversation_id": "uuid-string",  // optional
  "include_metrics_context": true
}
```

**Response:**
```json
{
  "status": "success",
  "response": "Based on the current metrics, the high CPU usage appears to be caused by increased application load. I can see that HTTP request rates have increased by 40% in the last 30 minutes, which correlates with the CPU spike. The load balancer metrics also show uneven distribution across instances.",
  "conversation_id": "uuid-string",
  "context_used": true,
  "suggested_actions": [
    "Check load balancer configuration",
    "Monitor application response times",
    "Consider horizontal scaling"
  ]
}
```

### Alert Investigation

#### `POST /api/v1/analysis/investigate-alert`

Get AI-powered investigation and explanation of a specific alert.

**Request Body:**
```json
{
  "alert_name": "HighMemoryUsage",
  "include_related_metrics": true,
  "time_range_hours": 2
}
```

**Response:**
```json
{
  "status": "success",
  "alert": {
    "labels": {...},
    "annotations": {...},
    "state": "firing"
  },
  "related_metrics": {...},
  "ai_explanation": "The HighMemoryUsage alert indicates that memory consumption has exceeded 85% on instance localhost:9090. This appears to be caused by a memory leak in the application process, as evidenced by the steady increase in memory usage over the past 2 hours without corresponding increases in active connections or request volume.",
  "investigation_timestamp": "2024-01-01T12:00:00Z",
  "severity_assessment": "high",
  "root_cause_analysis": "Memory leak in application process based on linear memory growth pattern",
  "remediation_steps": [
    "Restart the affected service to immediately free memory",
    "Review application logs for memory-related errors",
    "Implement memory profiling to identify the leak source",
    "Set up more granular memory monitoring"
  ]
}
```

### Monitoring Recommendations

#### `POST /api/v1/analysis/recommendations`

Get AI recommendations for improving monitoring setup.

**Request Body:**
```json
{
  "system_description": "Microservices architecture with Node.js APIs, PostgreSQL database, Redis cache"
}
```

**Response:**
```json
{
  "status": "success",
  "recommendations": "Based on your microservices architecture, I recommend implementing the following monitoring improvements:\n\n1. **Service-Level Monitoring**: Add custom metrics for each microservice including request/response times, error rates, and business logic metrics.\n\n2. **Database Monitoring**: Implement PostgreSQL exporter to track query performance, connection pool usage, and transaction rates.\n\n3. **Cache Monitoring**: Add Redis monitoring for hit rates, memory usage, and key expiration patterns.\n\n4. **Distributed Tracing**: Consider implementing OpenTelemetry for request tracing across services.\n\n5. **SLA Monitoring**: Define and monitor Service Level Indicators (SLIs) for each critical user journey.",
  "priority": "high",
  "implementation_complexity": "medium",
  "categories": [
    "Application Metrics",
    "Infrastructure Monitoring", 
    "Database Performance",
    "Service Mesh Observability"
  ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Server Error (500)
```json
{
  "status": "error",
  "message": "Internal server error occurred",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Service Unavailable (503)
```json
{
  "status": "error",
  "message": "Prometheus service is unavailable",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Rate Limiting

- **Default Limit:** 100 requests per hour per IP
- **Headers:** 
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

---

## Pagination

For endpoints that return large datasets:

**Query Parameters:**
- `limit`: Maximum items per page (default: 100, max: 1000)
- `offset`: Number of items to skip (default: 0)

**Response Headers:**
- `X-Total-Count`: Total number of items
- `X-Page-Count`: Total number of pages

---

## WebSocket Endpoints (Future)

### Real-time Metrics Stream
`ws://localhost:8000/ws/metrics`

### Alert Notifications
`ws://localhost:8000/ws/alerts`

---

## SDK Examples

### Python
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Health check
health = client.get("/health").json()

# Execute query
response = client.post("/api/v1/metrics/query", json={
    "query": "up"
})
data = response.json()

# Natural language query
nl_response = client.post("/api/v1/analysis/natural-language", json={
    "query": "Show me CPU usage trends"
})
```

### JavaScript
```javascript
const API_BASE = 'http://localhost:8000';

// Health check
const health = await fetch(`${API_BASE}/health`).then(r => r.json());

// Execute query
const queryResponse = await fetch(`${API_BASE}/api/v1/metrics/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'up' })
});

// Natural language query
const nlResponse = await fetch(`${API_BASE}/api/v1/analysis/natural-language`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'What is my current system health?' })
});
```

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Execute query
curl -X POST http://localhost:8000/api/v1/metrics/query \
  -H "Content-Type: application/json" \
  -d '{"query": "up"}'

# Chat with agent
curl -X POST http://localhost:8000/api/v1/analysis/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain my current alerts"}'
```

---

## Performance Considerations

- **Query Timeout:** 60 seconds for complex queries
- **Concurrent Requests:** Up to 20 concurrent requests per client
- **Memory Usage:** Large result sets are automatically paginated
- **Caching:** Responses are cached for 5 minutes where appropriate

---

## Changelog

### v1.0.0
- Initial API release
- Core metrics, alerts, and analysis endpoints
- Natural language query processing
- AI-powered health analysis and recommendations

---

For more information, visit the interactive API documentation at `/api/docs` when the service is running.
