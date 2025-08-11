#!/bin/bash

# Prometheus Setup Script for Prometheus Agent AI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📊 Prometheus Setup for Agent AI${NC}"
echo "======================================="

# Create config directory if it doesn't exist
mkdir -p config

# Create Prometheus configuration
echo -e "${BLUE}📝 Creating Prometheus configuration...${NC}"
cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter for system metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 5s

  # cAdvisor for container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 5s

  # Prometheus Agent AI API
  - job_name: 'prometheus-agent-api'
    static_configs:
      - targets: ['prometheus-agent-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # Example application (if you have one)
  - job_name: 'my-app'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 15s
EOF

# Create alert rules
echo -e "${BLUE}📝 Creating alert rules...${NC}"
cat > config/alert_rules.yml << 'EOF'
groups:
  - name: system_alerts
    rules:
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."

      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100) > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for more than 2 minutes on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 85% for more than 2 minutes on {{ $labels.instance }}"

      - alert: HighDiskUsage
        expr: 100 - ((node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100) > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High disk usage on {{ $labels.instance }}"
          description: "Disk usage is above 90% on {{ $labels.instance }}"

      - alert: PrometheusAgentAPIDown
        expr: up{job="prometheus-agent-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Prometheus Agent AI API is down"
          description: "The Prometheus Agent AI API has been down for more than 1 minute."

  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is above 10% for more than 2 minutes on {{ $labels.instance }}"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.instance }}"
          description: "95th percentile response time is above 500ms for more than 2 minutes on {{ $labels.instance }}"
EOF

# Create Alertmanager configuration
echo -e "${BLUE}📝 Creating Alertmanager configuration...${NC}"
cat > config/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourcompany.com'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://prometheus-agent-api:8000/api/v1/alerts/webhook'
        title: 'Prometheus Alert'
        text: 'Alert: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://prometheus-agent-api:8000/api/v1/alerts/webhook'
        title: 'CRITICAL: Prometheus Alert'
        text: 'CRITICAL Alert: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    # Add email, Slack, PagerDuty configurations here

  - name: 'warning-alerts'
    webhook_configs:
      - url: 'http://prometheus-agent-api:8000/api/v1/alerts/webhook'
        title: 'WARNING: Prometheus Alert'
        text: 'Warning Alert: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
EOF

# Create a simple docker-compose override for local development
echo -e "${BLUE}📝 Creating development docker-compose override...${NC}"
cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  prometheus-agent-api:
    volumes:
      - ./src:/app/src
      - ./config:/app/config
    environment:
      - API_RELOAD=true

  prometheus-agent-ui:
    volumes:
      - ./src:/app/src

  prometheus:
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./config/alert_rules.yml:/etc/prometheus/alert_rules.yml
    ports:
      - "9090:9090"

  alertmanager:
    volumes:
      - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
EOF

echo -e "${GREEN}✅ Prometheus configuration created successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Created files:${NC}"
echo "   • config/prometheus.yml      - Prometheus server configuration"
echo "   • config/alert_rules.yml     - Alert rules for monitoring"
echo "   • config/alertmanager.yml    - Alertmanager configuration"
echo "   • docker-compose.override.yml - Development overrides"
echo ""
echo -e "${GREEN}🚀 Next steps:${NC}"
echo "   1. Review and customize the configuration files"
echo "   2. Run: docker-compose up -d"
echo "   3. Access Prometheus at: http://localhost:9090"
echo "   4. Access Alertmanager at: http://localhost:9093"
echo "   5. Access Agent AI at: http://localhost:8501"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "   • Modify alert thresholds in config/alert_rules.yml"
echo "   • Add more scrape targets in config/prometheus.yml"
echo "   • Configure notification channels in config/alertmanager.yml"
