# Agentic AI Prometheus 🤖

An AI-powered monitoring and analysis agent for Prometheus that combines advanced metrics analysis with natural language interactions using OpenAI.

## Features 🚀

- **AI-Powered Analysis**: Get intelligent insights from your Prometheus metrics using OpenAI
- **Natural Language Queries**: Ask questions about your metrics in plain English
- **Interactive Chat**: Conversational interface for troubleshooting and monitoring
- **Alert Investigation**: AI-driven alert analysis and remediation suggestions
- **System Health Analysis**: Comprehensive health assessments with actionable recommendations
- **Monitoring Recommendations**: AI suggestions for improving your monitoring setup
- **Modern Web UI**: Built with Streamlit for an intuitive user experience
- **RESTful API**: FastAPI backend for integration with other tools
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Architecture 🏗️

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   Prometheus    │
│   (Port 8501)   │◄──►│   (Port 8000)   │◄──►│   (Port 9090)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4)       │
                       └─────────────────┘
```

## Quick Start 🚀

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Python 3.11+ (for local development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prometheus-agent-ai
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
nano .env
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Prometheus Agent AI API (http://localhost:8000)
- Prometheus Agent AI UI (http://localhost:8501)
- Prometheus Server (http://localhost:9090)
- Node Exporter (http://localhost:9100)
- cAdvisor (http://localhost:8080)

### 4. Access the Application

- **Web UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/api/docs
- **Prometheus**: http://localhost:9090

## Installation 📦

### Local Development Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**:
```bash
export PROMETHEUS_URL=http://localhost:9090
export OPENAI_API_KEY=your_openai_api_key_here
```

3. **Start the API Server**:
```bash
uvicorn src.api.main:app --reload --port 8000
```

4. **Start the UI** (in another terminal):
```bash
streamlit run src/ui/streamlit_app.py --server.port 8501
```

### Production Deployment

For production, use the provided Docker setup with appropriate environment variables and security configurations.

## Usage 💡

### 1. Natural Language Queries

Ask questions about your metrics in plain English:

- "Show me CPU usage for the last hour"
- "What's the average response time of my web service?"
- "How much memory is my application using?"
- "Show me the error rate for HTTP requests"

### 2. System Health Analysis

Get comprehensive AI-powered analysis of your system's health:

```python
# Via API
POST /api/v1/analysis/health
{
    "time_range_hours": 2
}
```

### 3. Alert Investigation

Investigate specific alerts with AI assistance:

```python
# Via API
POST /api/v1/analysis/investigate-alert
{
    "alert_name": "HighCPUUsage"
}
```

### 4. Chat Interface

Have conversational interactions with the AI agent about your monitoring setup.

## API Reference 📚

### Core Endpoints

#### Health Check
```http
GET /health
```

#### System Health Analysis
```http
POST /api/v1/analysis/health
Content-Type: application/json

{
    "time_range_hours": 1
}
```

#### Natural Language Query
```http
POST /api/v1/analysis/natural-language
Content-Type: application/json

{
    "query": "Show me CPU usage for the last hour"
}
```

#### Chat with Agent
```http
POST /api/v1/analysis/chat
Content-Type: application/json

{
    "message": "How can I improve my monitoring setup?"
}
```

#### Alert Investigation
```http
POST /api/v1/analysis/investigate-alert
Content-Type: application/json

{
    "alert_name": "HighMemoryUsage"
}
```

### Metrics Endpoints

#### Execute PromQL Query
```http
POST /api/v1/metrics/query
Content-Type: application/json

{
    "query": "up",
    "time": "2024-01-01T00:00:00Z"
}
```

#### Get Active Alerts
```http
GET /api/v1/alerts/active
```

For complete API documentation, visit http://localhost:8000/api/docs when running.

## Configuration ⚙️

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_URL` | Prometheus server URL | `http://localhost:9090` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `API_HOST` | FastAPI host | `0.0.0.0` |
| `API_PORT` | FastAPI port | `8000` |
| `STREAMLIT_PORT` | Streamlit port | `8501` |

### Prometheus Configuration

Create `config/prometheus.yml` for custom Prometheus configuration:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

## Development 🛠️

### Project Structure

```
prometheus-agent-ai/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── routes/            # API route handlers
│   │   └── models/            # Pydantic models
│   ├── core/                  # Core business logic
│   │   ├── prometheus_client.py
│   │   ├── openai_client.py
│   │   └── agent.py
│   └── ui/                    # Streamlit UI
│       └── streamlit_app.py
├── config/                    # Configuration files
├── tests/                     # Test files
└── scripts/                   # Utility scripts
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black src/
flake8 src/
mypy src/
```

## Monitoring Best Practices 📊

The AI agent can help you implement monitoring best practices:

1. **Four Golden Signals**: Latency, Traffic, Errors, Saturation
2. **USE Method**: Utilization, Saturation, Errors
3. **RED Method**: Rate, Errors, Duration
4. **Custom Business Metrics**: Monitor what matters to your business

## Troubleshooting 🔧

### Common Issues

1. **OpenAI API Key Issues**:
   - Ensure your API key is valid and has sufficient credits
   - Check the `OPENAI_API_KEY` environment variable

2. **Prometheus Connection Issues**:
   - Verify Prometheus is running and accessible
   - Check the `PROMETHEUS_URL` environment variable

3. **No Metrics Available**:
   - Ensure exporters (node-exporter, cAdvisor) are running
   - Check Prometheus targets page

### Logs

View application logs:
```bash
docker-compose logs prometheus-agent-api
docker-compose logs prometheus-agent-ui
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and linting: `pytest && black src/ && flake8 src/`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Create a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

- Create an issue for bug reports or feature requests
- Check the API documentation at `/api/docs`
- Review the troubleshooting section above

## Roadmap 🗺️

- [ ] Historical alert tracking
- [ ] Custom dashboard builder
- [ ] Slack/Teams integration
- [ ] Multi-tenancy support
- [ ] Custom AI model fine-tuning
- [ ] Grafana integration
- [ ] Performance optimization
- [ ] Advanced security features

---

**Built with ❤️ using FastAPI, Streamlit, OpenAI, and Prometheus**
