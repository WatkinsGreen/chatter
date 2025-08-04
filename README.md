# Incident Response Chatbot

A professional chatbot interface for incident response that correlates data from multiple monitoring systems to help identify what changed recently and focus troubleshooting efforts.

## Features

- **Real-time Analysis**: Queries multiple monitoring systems simultaneously
- **Change Correlation**: Identifies relationships between deployments, errors, and alerts
- **Professional UI**: Clean, responsive chat interface with suggestions
- **Multi-source Integration**: Supports Grafana, Prometheus, Elasticsearch, Nagios, and more
- **Mock Data**: Includes sample data for testing without live systems

## Architecture

- **Backend**: FastAPI with async connectors for monitoring systems
- **Frontend**: React with TypeScript, Tailwind CSS, and professional styling
- **Real-time**: WebSocket-ready architecture for live updates

## Installation & Setup

### Prerequisites

- Python 3.11+ 
- Node.js 18+
- npm or yarn

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chatter
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Docker (nginx)**: http://localhost (when using docker-compose)

## Configuration

Set environment variables to connect to your monitoring systems:

```bash
# Grafana
export GRAFANA_URL="http://your-grafana:3000"
export GRAFANA_TOKEN="your-token"

# Prometheus
export PROMETHEUS_URL="http://your-prometheus:9090"

# Elasticsearch
export ELASTICSEARCH_URL="http://your-elasticsearch:9200"
export ELASTICSEARCH_USERNAME="elastic"
export ELASTICSEARCH_PASSWORD="your-password"

# Nagios
export NAGIOS_URL="http://your-nagios/nagios"
export NAGIOS_USERNAME="nagiosadmin"
export NAGIOS_PASSWORD="your-password"
```

## Sample Queries

Try these questions with the chatbot:

- "What changed in the last 2 hours?"
- "Show me error details"
- "Check active alerts"
- "What changed since 15:30?"
- "Analyze recent deployments"

## Extending

The system is designed to be easily extended:

1. **Add new connectors**: Implement the `MonitoringConnector` base class
2. **Custom correlation**: Modify the `analyze_correlation` method
3. **New data sources**: Add connectors in the `connectors/` directory
4. **UI customization**: Modify React components in `frontend/src/`

## Production Deployment

For production use:

1. Replace mock data with real API calls to your monitoring systems
2. Add authentication and authorization
3. Implement rate limiting and caching
4. Add monitoring and logging
5. Use HTTPS and secure headers