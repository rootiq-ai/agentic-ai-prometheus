# Prometheus Agent AI - Usage Guide

This comprehensive guide covers how to use Prometheus Agent AI effectively for monitoring and analysis.

## Table of Contents

- [Getting Started](#getting-started)
- [Web Interface Guide](#web-interface-guide)
- [API Usage Examples](#api-usage-examples)
- [Natural Language Queries](#natural-language-queries)
- [AI-Powered Features](#ai-powered-features)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Steps After Installation

1. **Verify Services**: Ensure all components are running
2. **Check Connectivity**: Confirm Prometheus and OpenAI connections
3. **Explore Interface**: Familiarize yourself with the web UI
4. **Try Basic Queries**: Start with simple metric queries

### Quick Health Check

Visit http://localhost:8501 and verify you see:
- ✅ Green status indicators
- ✅ System metrics cards
- ✅ Chat interface available

---

## Web Interface Guide

### Dashboard Overview

The main dashboard provides:

#### **System Status Cards**
- **Services Up**: Monitor service availability
- **Active Alerts**: Current alert count
- **CPU Usage**: Average system CPU utilization
- **Memory Usage**: System memory consumption

#### **Quick Actions**
- 💬 **Start Chat**: Begin conversation with AI agent
- 📊 **Explore Metrics**: Browse and query metrics
- 🚨 **View Alerts**: Check active alerts
- 🔍 **System Health**: Run comprehensive analysis

### Chat Interface

The AI chat is your primary interface for natural language monitoring.

#### **Starting a Conversation**

1. Navigate to "Chat with Agent"
2. Type your question in plain English
3. Press Enter or click "Send"
4. Review the AI's response and suggested actions

#### **Example Conversations**

**Basic Health Check:**
```
You: "What's my system health status?"
Agent: "Your system is currently healthy with 3/3 services up and no critical alerts. CPU usage is at 45% and memory usage is at 67%, both within normal ranges."
```

**Investigating Issues:**
```
You: "I'm seeing high CPU usage, what's causing it?"
Agent: "Based on the metrics, CPU usage spiked to 85% starting 20 minutes ago. This correlates with a 40% increase in HTTP request rates. The load appears to be concentrated on the web server instances."
```

**Getting Recommendations:**
```
You: "How can I improve my monitoring?"
Agent: "I recommend adding these monitoring improvements: 1) Disk usage alerts (currently missing), 2) Database connection pool monitoring, 3) Response time percentiles for your APIs."
```

### Metrics Explorer

#### **Browsing Available Metrics**

1. Go to "Metrics" page
2. Use the search box to filter metrics
3. Browse by categories:
   - **System**: CPU, memory, disk metrics
   - **HTTP**: Web server and API metrics
   - **Database**: Database performance metrics
   - **Application**: Custom application metrics

#### **Executing Queries**

**PromQL Tab:**
```promql
# Basic queries
up
cpu_usage_percent
memory_usage_percent

# Rate calculations
rate(http_requests_total[5m])

# Aggregations
avg(cpu_usage_percent) by (instance)

# Complex queries
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Query Builder** (Visual Interface):
- Select metrics from dropdown
- Choose time ranges
- Apply functions and aggregations
- Preview results before execution

### Alert Management

#### **Active Alerts View**

- **Filter by Severity**: Critical, Warning, Info
- **Filter by Instance**: Specific servers or services
- **Sort Options**: By severity, time, or name

#### **Alert Investigation**

1. Click on any alert card
2. Review alert details and labels
3. Click "🔍 Investigate" for AI analysis
4. Follow recommended remediation steps

#### **Alert Rules Configuration**

View and understand your alerting rules:
- **Expression**: The PromQL condition
- **Duration**: How long condition must be true
- **Labels**: Alert categorization
- **Annotations**: Human-readable descriptions

---

## API Usage Examples

### Python Examples

#### **Basic Health Check**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Check system health
health = client.get("/health").json()
print(f"System status: {health['status']}")
print(f"Prometheus connected: {health['prometheus_connected']}")
```

#### **Execute PromQL Queries**
```python
# Instant query
response = client.post("/api/v1/metrics/query", json={
    "query": "up"
})
data = response.json()

for result in data['result']['result']:
    metric = result['metric']
    value = result['value'][1]
    print(f"{metric['instance']}: {value}")
```

#### **Range Query with Visualization**
```python
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# Get last hour of CPU data
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

response = client.post("/api/v1/metrics/query_range", json={
    "query": "cpu_usage_percent",
    "start": start_time.isoformat(),
    "end": end_time.isoformat(),
    "step": "1m"
})

# Convert to DataFrame and plot
df = pd.DataFrame(response.json()['dataframe'])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.plot(x='timestamp', y='value', title='CPU Usage Over Time')
plt.show()
```

#### **Natural Language Queries**
```python
# Ask questions in natural language
response = client.post("/api/v1/analysis/natural-language", json={
    "query": "Show me HTTP error rates for the last 30 minutes"
})

result = response.json()
print(f"Generated PromQL: {result['generated_promql']}")
print(f"AI Analysis: {result['ai_analysis']}")
```

#### **AI Chat Integration**
```python
# Start a conversation
conversation_id = "my-session-123"

def chat_with_agent(message):
    response = client.post("/api/v1/analysis/chat", json={
        "message": message,
        "conversation_id": conversation_id
    })
    return response.json()["response"]

# Multi-turn conversation
print(chat_with_agent("What's my current system status?"))
print(chat_with_agent("Are there any performance issues?"))
print(chat_with_agent("What should I monitor more closely?"))
```

### JavaScript/Node.js Examples

#### **Real-time Dashboard**
```javascript
const API_BASE = 'http://localhost:8000';

class PrometheusMonitor {
    async getSystemHealth() {
        const response = await fetch(`${API_BASE}/health`);
        return response.json();
    }

    async getActiveAlerts() {
        const response = await fetch(`${API_BASE}/api/v1/alerts/active`);
        return response.json();
    }

    async executeQuery(query) {
        const response = await fetch(`${API_BASE}/api/v1/metrics/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        return response.json();
    }

    async askAgent(question) {
        const response = await fetch(`${API_BASE}/api/v1/analysis/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: question })
        });
        return response.json();
    }
}

// Usage
const monitor = new PrometheusMonitor();

// Update dashboard every 30 seconds
setInterval(async () => {
    const health = await monitor.getSystemHealth();
    const alerts = await monitor.getActiveAlerts();
    
    updateDashboard(health, alerts);
}, 30000);
```

### cURL Examples

#### **Basic Queries**
```bash
# Health check
curl http://localhost:8000/health

# Get active alerts
curl http://localhost:8000/api/v1/alerts/active

# Execute PromQL query
curl -X POST http://localhost:8000/api/v1/metrics/query \
  -H "Content-Type: application/json" \
  -d '{"query": "up"}'
```

#### **Natural Language Processing**
```bash
# Ask AI about system health
curl -X POST http://localhost:8000/api/v1/analysis/natural-language \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my database performance like?"}'

# Get system health analysis
curl -X POST http://localhost:8000/api/v1/analysis/health \
  -H "Content-Type: application/json" \
  -d '{"time_range_hours": 2}'
```

---

## Natural Language Queries

### Query Types and Examples

#### **System Health Queries**
```
"What's my overall system health?"
"Are there any performance issues right now?"
"Show me a health report for the last 2 hours"
"What services are down?"
```

#### **Metrics Exploration**
```
"Show me CPU usage for the last hour"
"What's the memory usage trend?"
"How many HTTP requests am I getting?"
"What's my database response time?"
"Show me disk usage across all servers"
```

#### **Performance Analysis**
```
"Why is my application slow?"
"What's causing high CPU usage?"
"Are there any memory leaks?"
"Show me error rates by endpoint"
"Which services are using the most resources?"
```

#### **Alert Investigation**
```
"Explain the HighMemoryUsage alert"
"What alerts are currently firing?"
"Why am I getting database connection alerts?"
"How can I fix the disk space alert?"
```

#### **Trend Analysis**
```
"How has performance changed over the last week?"
"Show me traffic patterns for yesterday"
"What are the peak usage hours?"
"Compare this week's metrics to last week"
```

### Tips for Better Results

#### **Be Specific**
❌ "Show metrics"  
✅ "Show CPU usage for web servers over the last 2 hours"

#### **Include Time Ranges**
❌ "What's the error rate?"  
✅ "What's the error rate for the last 30 minutes?"

#### **Ask Follow-up Questions**
✅ "Why is CPU high?" → "What processes are causing it?" → "How can I optimize it?"

#### **Use Context**
✅ "My API is slow" → "Which endpoints are affected?" → "What's the root cause?"

---

## AI-Powered Features

### System Health Analysis

#### **Automated Health Reports**

The AI provides comprehensive health analysis including:

- **Performance Metrics**: CPU, memory, disk, network analysis
- **Service Availability**: Uptime and service status checking
- **Anomaly Detection**: Identification of unusual patterns
- **Trend Analysis**: Performance trends over time
- **Recommendations**: Actionable improvement suggestions

#### **Example Health Report**
```
System Health Analysis - Last 2 Hours

OVERALL STATUS: HEALTHY (Score: 78/100)

Key Findings:
• 3/3 services are operational
• CPU usage elevated but stable (avg 72%)
• Memory usage within normal range (avg 58%)
• 2 warning-level alerts require attention

Anomalies Detected:
• CPU spike at 14:32 (reached 95% for 3 minutes)
• HTTP response time increased 40% during peak hours

Recommendations:
1. Investigate CPU spike - correlates with database query surge
2. Consider horizontal scaling for web tier
3. Monitor disk space - trending upward at 2%/day
```

### Alert Intelligence

#### **Smart Alert Explanations**

The AI analyzes alerts and provides:
- **Root Cause Analysis**: Potential reasons for the alert
- **Impact Assessment**: How this affects your system
- **Remediation Steps**: Specific actions to resolve issues
- **Prevention**: How to avoid similar issues

#### **Example Alert Investigation**
```
Alert: HighMemoryUsage on web-server-01

AI Analysis:
This alert indicates memory consumption has exceeded 85% on web-server-01. 
Based on metric correlation, this appears to be caused by:

1. Memory leak in the user session handler
2. 300% increase in concurrent users since 13:00
3. Insufficient garbage collection frequency

Immediate Actions:
1. Restart the affected service to free memory
2. Increase JVM heap size from 4GB to 6GB
3. Review session cleanup intervals

Long-term Solutions:
1. Implement memory profiling in staging
2. Add memory usage dashboards
3. Set up predictive memory alerts
```

### Monitoring Recommendations

#### **Personalized Suggestions**

Based on your system and current monitoring setup, the AI suggests:
- **Missing Metrics**: Important metrics you're not tracking
- **Alert Improvements**: Better thresholds and conditions  
- **Dashboard Enhancements**: More useful visualizations
- **Best Practices**: Industry-standard monitoring approaches

#### **Example Recommendations**
```
Monitoring Improvements for Your Microservices Architecture:

Current Gaps:
1. No distributed tracing between services
2. Missing business metrics (user signups, purchases)
3. Database query performance not monitored
4. No synthetic monitoring for critical user journeys

Recommended Additions:
1. Implement OpenTelemetry for request tracing
2. Add custom metrics for key business events
3. Deploy PostgreSQL exporter for query insights
4. Set up blackbox monitoring for user flows

Priority Implementation:
High: Database monitoring (affects performance)
Medium: Business metrics (affects insights)
Low: Distributed tracing (affects debugging)
```

---

## Advanced Usage

### Custom Metrics Integration

#### **Adding Application Metrics**

```python
# In your application code
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_duration_seconds', 'Request latency')
ACTIVE_USERS = Gauge('app_active_users', 'Currently active users')

# Use in your application
@REQUEST_LATENCY.time()
def handle_request():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/users').inc()
    # Your application logic
    return response

# Start metrics server
start_http_server(8000)
```

#### **Querying Custom Metrics**

```python
# Query your custom metrics through the agent
response = client.post("/api/v1/analysis/natural-language", json={
    "query": "How many users are currently active in my application?"
})

print(response.json()['ai_analysis'])
```

### Advanced PromQL Patterns

#### **Performance Monitoring**

```promql
# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate calculation
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Apdex score (application performance index)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.1"}[5m])) +
  sum(rate(http_request_duration_seconds_bucket{le="0.4"}[5m]))
) / 2 / sum(rate(http_request_duration_seconds_count[5m]))
```

#### **Resource Utilization**

```promql
# CPU utilization by instance
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100)

# Memory utilization
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage prediction (linear regression)
predict_linear(node_filesystem_avail_bytes[1h], 24*3600)
```

### Automation and Integrations

#### **Automated Alert Response**

```python
import asyncio
from src.api.main import app

async def auto_investigate_critical_alerts():
    """Automatically investigate critical alerts"""
    
    alerts = await get_active_alerts()
    critical_alerts = [a for a in alerts if a['labels']['severity'] == 'critical']
    
    for alert in critical_alerts:
        # Get AI investigation
        investigation = await investigate_alert(alert['labels']['alertname'])
        
        # Send to incident management system
        await send_to_incident_system(investigation)
        
        # Post to Slack/Teams
        await post_to_chat(f"Critical Alert Analysis: {investigation['ai_explanation']}")

# Run every 5 minutes
asyncio.create_task(auto_investigate_critical_alerts())
```

#### **Slack Integration**

```python
from slack_sdk import WebClient

def send_health_report_to_slack():
    """Send daily health report to Slack"""
    
    # Get health analysis
    health = client.post("/api/v1/analysis/health", json={"time_range_hours": 24})
    
    # Format for Slack
    message = f"""
    📊 *Daily Health Report*
    
    *Overall Status:* {health['status']}
    *Active Alerts:* {health['active_alerts_count']}
    
    *AI Analysis:*
    {health['ai_analysis'][:500]}...
    
    View full report: http://localhost:8501
    """
    
    slack_client = WebClient(token=os.environ["SLACK_TOKEN"])
    slack_client.chat_postMessage(channel="#monitoring", text=message)
```

---

## Best Practices

### Effective Monitoring Strategy

#### **The Four Golden Signals**
1. **Latency**: How long requests take
2. **Traffic**: How many requests you're receiving
3. **Errors**: Rate of requests that fail
4. **Saturation**: How full your services are

#### **Implementing with Prometheus Agent AI**
```
# Ask the AI to help implement golden signals
"Help me set up monitoring for the four golden signals"
"What metrics should I track for latency?"
"How do I calculate error rates for my API?"
"Show me saturation metrics for my database"
```

### Alert Design Principles

#### **Actionable Alerts Only**
- Every alert should require human action
- If you can't act on it, don't alert on it
- Use the AI to validate alert usefulness

#### **Meaningful Thresholds**
```
# Ask AI to help set thresholds
"What's a good threshold for CPU usage alerts?"
"When should I alert on memory usage?"
"Help me set database response time alerts"
```

#### **Context-Rich Descriptions**
Use the AI to improve alert descriptions:
```
"Rewrite this alert description to be more helpful: 'High CPU usage detected'"
```

### Dashboard Design

#### **User-Focused Dashboards**
- **SRE Dashboard**: Focus on SLIs and error budgets
- **Developer Dashboard**: Application-specific metrics
- **Business Dashboard**: User and revenue metrics

#### **Effective Visualizations**
```
# Ask AI for visualization advice
"What's the best way to visualize response time data?"
"How should I display error rates on a dashboard?"
"What charts work best for capacity planning?"
```

---

## Troubleshooting

### Common Issues

#### **1. "No Data Available" Messages**

**Symptoms:**
- Metrics explorer shows no data
- Natural language queries return empty results
- Charts are blank

**Solutions:**
```bash
# Check Prometheus connectivity
curl http://localhost:9090/api/v1/targets

# Verify metric names
curl http://localhost:9090/api/v1/label/__name__/values

# Test direct query
curl "http://localhost:9090/api/v1/query?query=up"
```

**Ask the AI:**
```
"Why am I not seeing any metrics data?"
"Help me troubleshoot missing metrics"
```

#### **2. AI Responses Are Generic**

**Symptoms:**
- AI provides vague or unhelpful responses
- Recommendations don't match your setup
- Analysis lacks specific insights

**Solutions:**
- Provide more context in your questions
- Describe your system architecture to the AI
- Ask follow-up questions for specifics

**Better Questions:**
```
❌ "What's wrong with my system?"
✅ "My Node.js API on Kubernetes is showing high response times during peak hours (2-4 PM). What could be causing this?"

❌ "How to improve monitoring?"
✅ "I have a microservices e-commerce platform with 10 services. Currently monitoring basic metrics. What additional monitoring should I add for better observability?"
```

#### **3. PromQL Query Errors**

**Symptoms:**
- "Invalid query" errors
- Syntax errors in generated queries
- Unexpected query results

**Solutions:**
```bash
# Validate query syntax
promtool query instant 'your_query_here'

# Test in Prometheus UI first
http://localhost:9090/graph
```

**Ask the AI:**
```
"Fix this PromQL query: [paste your query]"
"Explain why this query isn't working: [query]"
"Convert this to valid PromQL: [description]"
```

#### **4. Performance Issues**

**Symptoms:**
- Slow API responses
- UI timeouts
- High memory usage

**Solutions:**
```bash
# Check resource usage
docker stats

# Reduce query time ranges
export DEFAULT_TIME_RANGE_HOURS=1

# Limit concurrent requests
export API_WORKERS=2
```

### Getting Help

#### **Using the AI for Troubleshooting**
```
"I'm getting timeout errors when querying metrics. What should I check?"
"My dashboards are loading slowly. How can I optimize performance?"
"The AI responses seem incorrect. How can I improve them?"
```

#### **Log Analysis**
```bash
# Check API logs
docker-compose logs prometheus-agent-api

# Check UI logs  
docker-compose logs prometheus-agent-ui

# Check Prometheus logs
docker-compose logs prometheus
```

#### **Community Support**

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share experiences
- **Documentation**: Check API docs and guides

---

## Advanced Configuration

### Custom AI Prompts

You can customize how the AI analyzes your metrics by providing system context:

```python
# When chatting, provide system context
context = """
System: E-commerce platform
Architecture: Microservices on Kubernetes  
Key Services: API Gateway, User Service, Product Service, Order Service, Payment Service
Database: PostgreSQL with Redis cache
Peak Traffic: 2-4 PM EST, 10k+ requests/minute
Critical SLA: 99.9% uptime, <200ms response time
"""

response = client.post("/api/v1/analysis/chat", json={
    "message": f"System Context: {context}\n\nQuestion: Analyze my current performance",
    "include_metrics_context": True
})
```

### Metric Collection Optimization

```yaml
# Custom Prometheus config for better performance
global:
  scrape_interval: 15s     # Balance between freshness and load
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'high-frequency'
    scrape_interval: 5s    # Critical metrics
    static_configs:
      - targets: ['api-gateway:8080']
  
  - job_name: 'standard'
    scrape_interval: 30s   # Standard metrics
    static_configs:
      - targets: ['user-service:8080', 'product-service:8080']
```

---

This guide covers the essential usage patterns for Prometheus Agent AI. For more advanced features and integrations, check the [API documentation](./API.md) and [deployment guide](./DEPLOYMENT.md).
